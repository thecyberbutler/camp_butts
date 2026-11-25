"""Registry preparation preserves boundaries and refuses ambiguous publication."""

import copy
import json
import os
from pathlib import Path

import pytest

from scripts import release_images as release


def manifest():
    digest = "a" * 64
    tag = "0.1.0-alpha.20261124-" + digest[:12]
    return {
        "namespace": "exampleowner",
        "version": "0.1.0-alpha.20261124",
        "tag": tag,
        "source_sha256": digest,
        "platforms": list(release.PLATFORMS),
        "images": {
            name: {
                "tag": release.image_reference("exampleowner", name, tag),
                "digest": "sha256:" + "b" * 64,
            }
            for name in release.COMPONENTS
        },
    }


@pytest.mark.parametrize("version", ["latest", "1.0.0", "../alpha", "0.1.0-alpha.20261124;id"])
def test_release_requires_explicit_prerelease(version):
    with pytest.raises(release.ReleaseError):
        release.validate_names("exampleowner", version)


def test_release_manifest_cannot_redirect_push_or_omit_components():
    original = manifest()
    release.validate_manifest(original)
    for mutation in ["registry", "digest", "component", "platform", "tag"]:
        value = copy.deepcopy(original)
        if mutation == "registry":
            value["images"]["web"]["tag"] = "unapproved.example/image:tag"
        elif mutation == "digest":
            value["images"]["db"]["digest"] = "latest"
        elif mutation == "component":
            del value["images"]["proxy"]
        elif mutation == "platform":
            value["platforms"] = ["linux/arm64"]
        else:
            value["tag"] = "latest"
        with pytest.raises(release.ReleaseError):
            release.validate_manifest(value)


def test_source_snapshot_omits_secrets_and_rejects_symlinks(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "app.py").write_text("public application code")
    (root / ".secrets").mkdir()
    (root / ".secrets" / "credential").write_text("excluded synthetic marker")
    monkeypatch.setattr(release, "ROOT", root)
    monkeypatch.setattr(release, "SOURCES", ("app.py",))
    copy_root = tmp_path / "snapshot"
    before = release.snapshot(copy_root)
    assert not (copy_root / ".secrets").exists()
    (copy_root / "app.py").write_text("modified application code")
    assert release.source_digest(copy_root) != before
    (root / "app.py").unlink()
    (root / "app.py").symlink_to(root / ".secrets" / "credential")
    with pytest.raises(release.ReleaseError):
        release.snapshot(tmp_path / "second")


def test_registry_overlay_preserves_runtime_hardening():
    env = dict(os.environ, APP_DOMAIN="localhost", DJANGO_ALLOWED_HOSTS="localhost")
    for component in release.COMPONENTS:
        env[f"CAMPGROUND_{component.upper()}_IMAGE"] = (
            f"docker.io/exampleowner/campground-{component}@sha256:" + "a" * 64
        )
    root = Path(__file__).resolve().parents[2]

    def config(extra):
        return json.loads(
            release.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    "compose.yaml",
                    *extra,
                    "--profile",
                    "tools",
                    "config",
                    "--format",
                    "json",
                ],
                cwd=root,
                env=env,
            )
        )

    base = config([])
    overlay = config(["-f", "compose.registry.yaml"])
    assert base["networks"] == overlay["networks"]
    assert base["secrets"] == overlay["secrets"]
    assert base["volumes"] == overlay["volumes"]
    for name, original in base["services"].items():
        changed = dict(overlay["services"][name])
        assert "build" not in changed
        assert "@sha256:" in changed.pop("image")
        assert changed.pop("pull_policy") == "missing"
        original = {k: v for k, v in original.items() if k not in {"build", "image"}}
        assert changed == original


def test_registry_http_disables_redirects_and_redacts_failures(monkeypatch):
    calls = []

    class Response:
        status_code = 403
        text = "sensitive-synthetic-response-must-not-leak"

    class Session:
        trust_env = True

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def request(self, method, url, **kwargs):
            calls.append((method, url, kwargs, self.trust_env))
            return Response()

    monkeypatch.setattr(release.requests, "Session", Session)
    with pytest.raises(release.ReleaseError) as error:
        release.hub_request("GET", "/v2/namespaces/exampleowner/repositories/campground-web")
    assert Response.text not in str(error.value)
    assert calls[0][1].startswith("https://hub.docker.com/")
    assert calls[0][2]["allow_redirects"] is False
    assert calls[0][2]["verify"] is not False
    assert calls[0][3] is False


def test_snapshot_readable_image_modes_stay_under_private_workspace(tmp_path, monkeypatch):
    workspace = tmp_path / "private"
    workspace.mkdir(mode=0o700)
    root = tmp_path / "repo"
    (root / "app").mkdir(parents=True)
    (root / "app/module.py").write_text("public source")
    monkeypatch.setattr(release, "ROOT", root)
    monkeypatch.setattr(release, "SOURCES", ("app",))
    release.snapshot(workspace / "source")
    assert workspace.stat().st_mode & 0o777 == 0o700
    assert (workspace / "source/app").stat().st_mode & 0o777 == 0o755
    assert (workspace / "source/app/module.py").stat().st_mode & 0o777 == 0o644


@pytest.mark.parametrize("public_approved,private", [(False, False), (True, True)])
def test_publisher_refuses_unapproved_visibility_before_push(
    tmp_path, monkeypatch, public_approved, private
):
    candidate = manifest()
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(candidate))
    monkeypatch.setattr(release, "source_digest", lambda _: candidate["source_sha256"])
    monkeypatch.setattr(release, "image_digest", lambda _: "sha256:" + "b" * 64)
    for name in ["scan_source", "verify_source", "smoke_images"]:
        monkeypatch.setattr(release, name, lambda _: None)
    monkeypatch.setattr(release, "scan_image", lambda *args: None)
    monkeypatch.setattr(release, "hub_login", lambda: "synthetic-not-a-token")
    monkeypatch.setattr(release, "hub_request", lambda *args, **kwargs: {"is_private": private})

    def no_push(*args, **kwargs):
        pytest.fail("A visibility mismatch must never invoke Docker push")

    monkeypatch.setattr(release, "run", no_push)
    with pytest.raises(release.ReleaseError, match="visibility"):
        release.publish(path, public_approved=public_approved)
    assert not (tmp_path / "images.env").exists()


def test_publisher_refuses_overwriting_different_registry_digest(tmp_path, monkeypatch):
    candidate = manifest()
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(candidate))
    monkeypatch.setattr(release, "source_digest", lambda _: candidate["source_sha256"])
    monkeypatch.setattr(release, "image_digest", lambda _: "sha256:" + "b" * 64)
    for name in ["scan_source", "verify_source", "smoke_images"]:
        monkeypatch.setattr(release, name, lambda _: None)
    monkeypatch.setattr(release, "scan_image", lambda *args: None)
    monkeypatch.setattr(release, "hub_login", lambda: "synthetic-not-a-token")

    def response(method, endpoint, **kwargs):
        return {"digest": "sha256:" + "c" * 64} if "/tags/" in endpoint else {"is_private": True}

    monkeypatch.setattr(release, "hub_request", response)

    def no_push(*args, **kwargs):
        pytest.fail("An existing different tag digest must never be overwritten")

    monkeypatch.setattr(release, "run", no_push)
    with pytest.raises(release.ReleaseError, match="overwrite"):
        release.publish(path)
    assert not (tmp_path / "images.env").exists()
