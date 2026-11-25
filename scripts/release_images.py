"""Build/scan prerelease images locally, then explicitly publish the exact digests to Docker Hub."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess  # nosec B404
import tempfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = {"web": "Dockerfile", "db": "Dockerfile.db", "proxy": "Dockerfile.proxy"}
PLATFORMS = ("linux/amd64", "linux/arm64")
TRIVY = "aquasec/trivy@sha256:8f6bb947dbc528902e11f2f5be52f7b519f6a39d5d148f41166f2040499768fb"
GITLEAKS = (
    "ghcr.io/gitleaks/gitleaks@sha256:"
    "c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f"
)
SOURCES = (
    "apps",
    "config",
    "templates",
    "static",
    "data",
    "infra",
    "scripts",
    "tests",
    "pyproject.toml",
    "poetry.lock",
    "manage.py",
    "gunicorn.conf.py",
    ".dockerignore",
    "Dockerfile",
    "Dockerfile.db",
    "Dockerfile.proxy",
    "compose.yaml",
    "compose.registry.yaml",
)
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


class ReleaseError(Exception):
    """Messages must never contain raw subprocess, HTTP or credential diagnostics."""


def run(argv, *, cwd=None, env=None, input_data=None):
    # SD-025: argument arrays, no shell, no raw child output; caller supplies fixed tools.
    result = subprocess.run(  # nosec B603
        argv, cwd=cwd, env=env, input=input_data, capture_output=True, check=False
    )
    if result.returncode:
        raise ReleaseError(f"{Path(argv[0]).name} failed; raw diagnostics withheld.")
    return result.stdout


def source_digest(directory):
    digest = hashlib.sha256()
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ReleaseError("Source symlinks are not accepted.")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            name = path.relative_to(directory).as_posix().encode()
            data = path.read_bytes()
            digest.update(len(name).to_bytes(8, "big") + name)
            digest.update(len(data).to_bytes(8, "big") + data)
    return digest.hexdigest()


def snapshot(destination):
    destination.mkdir(mode=0o700)
    for name in SOURCES:
        source = ROOT / name
        if source.is_symlink():
            raise ReleaseError("Source symlinks are not accepted.")
        for path in source.rglob("*") if source.is_dir() else [source]:
            if "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            if path.is_symlink():
                raise ReleaseError("Source symlinks are not accepted.")
            if path.is_file():
                target = destination / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
                # Match ordinary source modes in the image; parent workspace stays 0700.
                target.chmod(0o644 | (path.stat().st_mode & 0o111))
    for directory in [destination, *(p for p in destination.rglob("*") if p.is_dir())]:
        directory.chmod(0o755)
    return source_digest(destination)


def image_digest(reference):
    value = json.loads(
        run(["docker", "image", "inspect", reference, "--format", "{{json .Descriptor}} "])
    )
    digest = value.get("digest", "")
    if not DIGEST.fullmatch(digest):
        raise ReleaseError("Docker's containerd image store with manifest descriptors is required.")
    return digest


def scanner(image, mounts, arguments, *, network=True):
    # Container-private tmpfs; not a shared host temporary file (SD-025).
    scratch = "/tmp:rw,noexec,nosuid,size=1g"  # nosec B108
    command = [
        "docker",
        "run",
        "--rm",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--tmpfs",
        scratch,
    ]
    if not network:
        command += ["--network", "none"]
    for mount in mounts:
        command += ["-v", mount]
    run(command + [image, *arguments])


def scan_source(source):
    scanner(
        GITLEAKS, [f"{source}:/scan:ro"], ["dir", "/scan", "--redact", "--no-banner"], network=False
    )
    scanner(
        TRIVY,
        [f"{source}:/scan:ro", "campground-trivy-cache:/root/.cache/"],
        [
            "fs",
            "--scanners",
            "vuln,misconfig",
            "--include-dev-deps",
            "--severity",
            "HIGH,CRITICAL",
            "--exit-code",
            "1",
            "--no-progress",
            "/scan",
        ],
    )


def scan_image(reference, workspace, component):
    for platform in PLATFORMS:
        print(f"Scanning {component} for {platform}", flush=True)
        archive = workspace / f"{component}-{platform.split('/')[1]}.tar"
        run(["docker", "image", "save", "--platform", platform, "-o", str(archive), reference])
        try:
            scanner(
                TRIVY,
                [f"{archive}:/scan/image.tar:ro", "campground-trivy-cache:/root/.cache/"],
                [
                    "image",
                    "--input",
                    "/scan/image.tar",
                    "--scanners",
                    "vuln",
                    "--severity",
                    "HIGH,CRITICAL",
                    "--exit-code",
                    "1",
                    "--no-progress",
                ],
            )
            scanner(
                TRIVY,
                [f"{archive}:/scan/image.tar:ro", "campground-trivy-cache:/root/.cache/"],
                [
                    "image",
                    "--input",
                    "/scan/image.tar",
                    "--scanners",
                    "secret",
                    "--exit-code",
                    "1",
                    "--no-progress",
                ],
            )
        finally:
            archive.unlink(missing_ok=True)


def smoke_images(manifest):
    print("Checking non-root image execution on both architectures", flush=True)
    for platform in PLATFORMS:
        for component, image in manifest["images"].items():
            base = [
                "docker",
                "run",
                "--rm",
                "--platform",
                platform,
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
            ]
            check = 'test "$(id -u)" = 10001 && test "$(id -g)" = 10001'
            if component == "web":
                check += " && test -r /app/manage.py && test -r /app/config/settings/production.py"
                check += ' && test "$(stat -c %u /app/staticfiles)" = 10001'
            elif component == "db":
                check += ' && test "$(stat -c %u /var/lib/postgresql/data)" = 10001'
                check += " && test ! -e /usr/local/bin/gosu && postgres --version >/dev/null"
            else:
                check += " && test -r /etc/traefik/entrypoint.sh"
                check += ' && test "$(stat -c %u /data)" = 10001'
            # Fixed shell expression only; no source/CLI values are interpolated into it.
            run([*base, "--entrypoint", "/bin/sh", image["tag"], "-c", check])
            if component == "web":
                run(
                    [
                        *base,
                        "--entrypoint",
                        "python",
                        image["tag"],
                        "-c",
                        "import django, allauth, axes, psycopg, cryptography",
                    ]
                )
            if component in {"web", "proxy"}:
                command = [*base]
                if component == "proxy":
                    command += ["-e", "APP_DOMAIN=localhost", "-e", "TLS_MODE=development"]
                try:
                    run([*command, image["tag"]])
                except ReleaseError:
                    pass
                else:
                    raise ReleaseError("Missing-secret startup unexpectedly succeeded.")


def validate_names(namespace, version):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,38}", namespace):
        raise ReleaseError("Invalid Docker Hub namespace.")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+-(alpha|beta|rc)\.[0-9]{8}", version):
        raise ReleaseError(
            "Use a prerelease version such as 0.1.0-alpha.20261124; stable release is gated."
        )


def verify_source(workspace):
    source = workspace / "source"
    print("Running source checks and PostgreSQL security/concurrency tests", flush=True)
    files = ["apps", "config", "scripts", "tests", "manage.py", "gunicorn.conf.py"]
    run([str(ROOT / ".venv/bin/ruff"), "check", "--no-cache", *files], cwd=source)
    run([str(ROOT / ".venv/bin/ruff"), "format", "--check", "--no-cache", *files], cwd=source)
    run(
        [
            str(ROOT / ".venv/bin/bandit"),
            "-r",
            "apps",
            "config",
            "scripts",
            "manage.py",
            "gunicorn.conf.py",
            "-q",
        ],
        cwd=source,
    )
    credential = ROOT / ".secrets/database_password"
    info = credential.lstat()
    if (
        credential.is_symlink()
        or not credential.is_file()
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise ReleaseError("Protected synthetic test database credential required.")
    port = os.environ.get("TEST_DATABASE_PORT", "55433")
    if not port.isdecimal() or not 1024 <= int(port) <= 65535:
        raise ReleaseError("Invalid synthetic PostgreSQL port.")
    with tempfile.TemporaryDirectory(prefix="test-private-", dir=workspace) as temporary:
        env = {
            "PATH": os.environ["PATH"],
            "HOME": str(Path.home()),
            "PYTHONUTF8": "1",
            "DJANGO_SETTINGS_MODULE": "config.settings.testing",
            "TMPDIR": temporary,
            "DATABASE_NAME": "campground_test",
            "DATABASE_USER": "campground_test_runner",
            "DATABASE_HOST": "127.0.0.1",
            "DATABASE_PORT": port,
            "DATABASE_PASSWORD_FILE": str(credential),
            "COVERAGE_FILE": str(workspace / ".coverage"),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTEST_PLUGINS": "pytest_django.plugin,pytest_cov.plugin",
        }
        output = run(
            [
                str(ROOT / ".venv/bin/pytest"),
                "-q",
                "-p",
                "no:cacheprovider",
                "--assert=plain",
                "--tb=no",
                "--show-capture=no",
                "--cov",
                "--cov-fail-under=85",
            ],
            cwd=source,
            env=env,
        )
    match = re.search(rb"(\d+) passed", output)
    if match is None:
        raise ReleaseError("Test completion evidence is missing.")
    result = {"passed": int(match.group(1)), "minimum_coverage": 85}
    (workspace / "tests.json").write_text(json.dumps(result) + "\n")
    print(f"PostgreSQL suite passed: {result['passed']} tests; coverage gate passed.", flush=True)


def build(namespace, version):
    validate_names(namespace, version)
    base = ROOT / ".runtime" / "releases"
    if (ROOT / ".runtime").is_symlink() or base.is_symlink():
        raise ReleaseError("Release workspace must not be a symlink.")
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    if base.stat().st_mode & 0o077:
        raise ReleaseError("Release workspace must be private (0700).")
    workspace = Path(tempfile.mkdtemp(prefix="candidate-", dir=base))
    source = workspace / "source"
    digest = snapshot(source)
    tag = f"{version}-{digest[:12]}"
    manifest = {
        "namespace": namespace,
        "version": version,
        "tag": tag,
        "source_sha256": digest,
        "platforms": list(PLATFORMS),
        "images": {},
    }
    print(f"Preparing {namespace}, tag {tag}; local workspace {workspace}", flush=True)
    scan_source(source)
    verify_source(workspace)
    for component, dockerfile in COMPONENTS.items():
        reference = f"docker.io/{namespace}/campground-{component}:{tag}"
        print(f"Building {reference} for AMD64 and ARM64", flush=True)
        run(
            [
                "docker",
                "buildx",
                "build",
                "--platform",
                ",".join(PLATFORMS),
                "--load",
                "--provenance=mode=min",
                "--build-arg",
                "APP_UID=10001",
                "--build-arg",
                "APP_GID=10001",
                "--label",
                f"org.opencontainers.image.version={tag}",
                "--label",
                f"io.campground.source-sha256={digest}",
                "--tag",
                reference,
                "--file",
                str(source / dockerfile),
                str(source),
            ]
        )
        immutable = image_digest(reference)
        scan_image(reference, workspace, component)
        if image_digest(reference) != immutable:
            raise ReleaseError("Local image changed during scanning.")
        manifest["images"][component] = {"tag": reference, "digest": immutable}
    smoke_images(manifest)
    if source_digest(source) != digest:
        raise ReleaseError("Source changed during build.")
    (workspace / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Build and image scans completed. Manifest: {workspace / 'manifest.json'}", flush=True)
    return workspace


def hub_request(method, path, *, token=None, body=None, missing=False):
    # Fixed HTTPS origin; redirects disabled so credentials cannot follow a Location header.
    with requests.Session() as session:
        session.trust_env = False
        response = session.request(
            method,
            "https://hub.docker.com" + path,
            headers={"Authorization": f"Bearer {token}"} if token else {},
            json=body,
            timeout=30,
            allow_redirects=False,
            verify=os.environ.get("SSL_CERT_FILE") or True,
        )
    if missing and response.status_code == 404:
        return None
    if response.status_code not in (200, 201):
        raise ReleaseError(
            f"Docker Hub request refused (HTTP {response.status_code}); details withheld."
        )
    return response.json()


def hub_login():
    config_path = (
        Path(os.environ.get("DOCKER_CONFIG", str(Path.home() / ".docker"))) / "config.json"
    )
    config = json.loads(config_path.read_text())
    server = "https://index.docker.io/v1/"
    helper = config.get("credHelpers", {}).get(server) or config.get("credsStore")
    if helper not in {"desktop", "osxkeychain", "pass", "secretservice"}:
        raise ReleaseError(
            "Configure a supported Docker credential store and log in locally first."
        )
    credential = json.loads(
        run([f"docker-credential-{helper}", "get"], input_data=(server + "\n").encode())
    )
    username, secret = credential["Username"], credential["Secret"]
    if username == "<token>":
        raise ReleaseError("Log in with docker login --username and a scoped access token.")
    result = hub_request("POST", "/v2/auth/token", body={"identifier": username, "secret": secret})
    token = result.get("access_token")
    if not isinstance(token, str) or not token:
        raise ReleaseError("Docker Hub authentication did not return an access token.")
    return token


def validate_manifest(manifest):
    validate_names(manifest["namespace"], manifest["version"])
    digest = manifest["source_sha256"]
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ReleaseError("Invalid source digest.")
    tag = f"{manifest['version']}-{digest[:12]}"
    if manifest["tag"] != tag or manifest["platforms"] != list(PLATFORMS):
        raise ReleaseError("Unexpected tag or platforms.")
    if set(manifest["images"]) != set(COMPONENTS):
        raise ReleaseError("A complete three-image release is required.")
    for component, image in manifest["images"].items():
        expected = f"docker.io/{manifest['namespace']}/campground-{component}:{tag}"
        if image["tag"] != expected or not DIGEST.fullmatch(image["digest"]):
            raise ReleaseError("Invalid image identity.")


def publish(path, *, public_approved=False):
    path = path.resolve()
    workspace = path.parent
    manifest = json.loads(path.read_text())
    validate_manifest(manifest)
    if source_digest(workspace / "source") != manifest["source_sha256"]:
        raise ReleaseError("Release source no longer matches its manifest.")
    # Re-scan before publication; a prior artifact alone cannot bypass current scans.
    scan_source(workspace / "source")
    verify_source(workspace)
    for component, image in manifest["images"].items():
        if image_digest(image["tag"]) != image["digest"]:
            raise ReleaseError("Local image no longer matches its reviewed manifest.")
        scan_image(image["tag"], workspace, component)
    smoke_images(manifest)
    token = hub_login()
    namespace = manifest["namespace"]
    for component in COMPONENTS:
        name = f"campground-{component}"
        endpoint = f"/v2/namespaces/{namespace}/repositories/{name}"
        repository = hub_request("GET", endpoint, token=token, missing=True)
        if repository is None:
            hub_request(
                "POST",
                f"/v2/namespaces/{namespace}/repositories",
                token=token,
                body={
                    "name": name,
                    "namespace": namespace,
                    "is_private": not public_approved,
                    "description": "Campground reservation platform; prerelease evaluation only.",
                },
            )
            repository = hub_request("GET", endpoint, token=token)
        if repository.get("is_private") is not (not public_approved):
            raise ReleaseError(
                "Repository visibility does not match the approved publication mode."
            )
        existing = hub_request(
            "GET", endpoint + f"/tags/{manifest['tag']}", token=token, missing=True
        )
        if (
            existing is not None
            and existing.get("digest") != manifest["images"][component]["digest"]
        ):
            raise ReleaseError("Refusing to overwrite an existing tag with a different image.")
    for image in manifest["images"].values():
        if image_digest(image["tag"]) != image["digest"]:
            raise ReleaseError("Local image changed before push.")
        print(f"Publishing {image['tag']}", flush=True)
        run(["docker", "push", image["tag"]])
        remote = run(["docker", "buildx", "imagetools", "inspect", image["tag"], "--raw"])
        if "sha256:" + hashlib.sha256(remote).hexdigest() != image["digest"]:
            raise ReleaseError("Published manifest digest differs; deployment lock not emitted.")
    lines = [
        f"CAMPGROUND_{component.upper()}_IMAGE={image['tag'].split(':')[0]}@{image['digest']}"
        for component, image in manifest["images"].items()
    ]
    (workspace / "images.env").write_text("\n".join(lines) + "\n")
    print(f"All remote digests verified. Deployment lock: {workspace / 'images.env'}")


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prepare = sub.add_parser("build")
    prepare.add_argument("--namespace", required=True)
    prepare.add_argument("--version", required=True)
    push = sub.add_parser("publish")
    push.add_argument("manifest", type=Path)
    push.add_argument(
        "--public-approved",
        action="store_true",
        help="Use only after explicit owner approval of public source visibility.",
    )
    options = parser.parse_args()
    if options.action == "build":
        build(options.namespace, options.version)
    else:
        publish(options.manifest, public_approved=options.public_approved)


if __name__ == "__main__":
    try:
        main()
    except ReleaseError as error:
        raise SystemExit(str(error)) from None
    except (OSError, ValueError, KeyError, TypeError, requests.RequestException):
        raise SystemExit("Image operation failed; sensitive diagnostics withheld.") from None
