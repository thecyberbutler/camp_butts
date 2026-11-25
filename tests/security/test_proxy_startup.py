"""Run against the locally built proxy image; Docker is required, no ports published."""

import json
import subprocess

import pytest


@pytest.mark.parametrize(
    ("domain", "mode"),
    [
        ("localhost`, PathPrefix(`/`)", "development"),
        ("localhost", "unsupported"),
        ("localhost", "acme"),
        ("localhost", "development"),  # Missing TLS files must prevent startup.
    ],
)
def test_proxy_refuses_unsafe_startup(domain, mode):
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "-e",
            f"APP_DOMAIN={domain}",
            "-e",
            f"TLS_MODE={mode}",
            "campground-proxy:local",
        ],
        capture_output=True,
        timeout=10,
        check=False,
    )
    refused = result.returncode == 1 and b"Proxy startup refused" in result.stderr
    assert refused


def test_proxy_image_has_no_root_user_or_caddy_binary():
    result = subprocess.run(
        ["docker", "image", "inspect", "campground-proxy:local"],
        capture_output=True,
        timeout=10,
        check=True,
    )
    image = json.loads(result.stdout)[0]
    assert image["Config"]["User"].split(":")[0] not in ("", "0", "root")
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--entrypoint",
            "/bin/sh",
            "campground-proxy:local",
            "-c",
            "test ! -e /usr/bin/caddy && test ! -e /usr/local/bin/caddy",
        ],
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0
