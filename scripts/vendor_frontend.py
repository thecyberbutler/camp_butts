"""Fetch exact official npm releases, verify registry SRI, copy allowlisted assets only."""

import base64
import hashlib
import io
import json
import ssl
import tarfile
from http.client import HTTPSConnection
from pathlib import Path
from urllib.parse import urlsplit

PACKAGES = [
    (
        "bootstrap",
        "5.3.8",
        {
            "package/dist/css/bootstrap.min.css": "bootstrap.min.css",
            "package/LICENSE": "bootstrap.LICENSE",
        },
    ),
    (
        "htmx.org",
        "2.0.11",
        {"package/dist/htmx.min.js": "htmx.min.js", "package/LICENSE": "htmx.LICENSE"},
    ),
]


def fetch(url, context):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "registry.npmjs.org":
        raise RuntimeError("Unapproved dependency origin")
    connection = HTTPSConnection("registry.npmjs.org", context=context, timeout=30)
    try:
        connection.request("GET", parsed.path)
        response = connection.getresponse()
        if response.status != 200:
            raise RuntimeError("Dependency download failed; redirects are not accepted")
        data = response.read(10_000_001)
        if len(data) > 10_000_000:
            raise RuntimeError("Oversized dependency response")
        return data
    finally:
        connection.close()


def main():
    target = Path(__file__).resolve().parents[1] / "static/vendor"
    target.mkdir(parents=True, exist_ok=True)
    context = ssl.create_default_context()
    inventory = []
    for name, version, files in PACKAGES:
        url = f"https://registry.npmjs.org/{name}/{version}"
        metadata = json.loads(fetch(url, context))
        archive_url = metadata["dist"]["tarball"]
        if not archive_url.startswith("https://registry.npmjs.org/"):
            raise RuntimeError("Unapproved dependency distribution origin")
        archive = fetch(archive_url, context)
        if len(archive) > 10_000_000:
            raise RuntimeError("Oversized dependency archive")
        digest = "sha512-" + base64.b64encode(hashlib.sha512(archive).digest()).decode()
        if digest != metadata["dist"]["integrity"]:
            raise RuntimeError("Dependency archive integrity mismatch")
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
            for source, destination in files.items():
                member = bundle.getmember(source)
                if not member.isfile() or member.size > 2_000_000:
                    raise RuntimeError("Invalid dependency member")
                content = bundle.extractfile(member).read()
                (target / destination).write_bytes(content)
                inventory.append(
                    {
                        "package": name,
                        "version": version,
                        "license": metadata["license"],
                        "source": archive_url,
                        "archive_sri": digest,
                        "file": destination,
                        "sha256": hashlib.sha256(content).hexdigest(),
                    }
                )
    (target / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    print("Vendored exact frontend releases with verified archive integrity.")


if __name__ == "__main__":
    main()
