"""Disposable Docker tests of the approved proxy boundary; never mount app secrets."""

import argparse
import time

from scripts.release_images import ReleaseError, run

CLIENT_IMAGE = (
    "python:3.13-alpine@sha256:9ef1a599f863231c3d91e941389bfdc4a2d6070557243d54df1a4e57015b960e"
)
PROBE = r"""
import http.client
import socket
import ssl

def tunnel(host, port=443):
    conn = http.client.HTTPConnection("172.30.20.2", 3128, timeout=10)
    try:
        conn.request("CONNECT", f"{host}:{port}")
        response = conn.getresponse()
        assert response.status == 403
    finally:
        conn.close()

for host in ("example.com", "169.254.169.254", "127.0.0.1", "10.0.0.1",
             "www.googleapis.com.evil.invalid", "[::1]"):
    tunnel(host)
tunnel("www.googleapis.com", 80)
conn = http.client.HTTPConnection("172.30.20.2", 3128, timeout=10)
conn.request("GET", "http://www.googleapis.com/oauth2/v1/certs")
assert conn.getresponse().status == 403
conn.close()
conn = http.client.HTTPSConnection(
    "172.30.20.2", 3128, context=ssl.create_default_context(), timeout=15)
conn.set_tunnel("www.googleapis.com", 443)
conn.request("GET", "/oauth2/v1/certs")
assert conn.getresponse().status == 200
conn.close()
try:
    with socket.create_connection(("1.1.1.1", 443), timeout=2):
        raise AssertionError("Direct Internet route exists")
except OSError:
    pass
print("Google TLS tunnel and denied destinations/methods/ports/direct egress verified.")
"""
DENY_GOOGLE = r"""
import http.client
conn = http.client.HTTPConnection("172.30.20.2", 3128, timeout=10)
conn.request("CONNECT", "www.googleapis.com:443")
assert conn.getresponse().status == 403
conn.close()
print("Google tunnel denied under the negative boundary condition.")
"""


def check(image):
    private = "campground-google-validation-private"
    edge = "campground-google-validation-edge"
    container = "campground-google-validation-proxy"
    created = []
    running = False

    def start(*extra):
        nonlocal running
        run(
            [
                "docker",
                "create",
                "--name",
                container,
                "--network",
                private,
                "--ip",
                "172.30.20.2",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
                "--memory",
                "128m",
                "--pids-limit",
                "64",
                "--tmpfs",
                "/run/squid:rw,noexec,nosuid,size=4m,mode=0700,uid=10001,gid=10001",
                *extra,
                image,
            ]
        )
        running = True
        run(["docker", "network", "connect", edge, container])
        run(["docker", "start", container])
        for _ in range(20):
            try:
                run(["docker", "exec", container, "/usr/sbin/squid", "-k", "check"])
                return
            except ReleaseError:
                time.sleep(0.25)
        raise ReleaseError("Google egress did not start with restricted permissions.")

    def client(script, ip="172.30.20.3"):
        run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                private,
                "--ip",
                ip,
                "--user",
                "10001:10001",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges:true",
                "--entrypoint",
                "python",
                CLIENT_IMAGE,
                "-c",
                script,
            ]
        )

    try:
        run(["docker", "network", "create", "--internal", "--subnet", "172.30.20.0/28", private])
        created.append(private)
        run(["docker", "network", "create", edge])
        created.append(edge)
        start()
        client(PROBE)
        client(DENY_GOOGLE, "172.30.20.4")
        for address in ("169.254.169.254", "::ffff:169.254.169.254"):
            run(["docker", "rm", "-f", container])
            running = False
            start("--add-host", "www.googleapis.com:" + address)
            client(DENY_GOOGLE)
        print(
            "Google proxy: verified TLS; unapproved/private/metadata targets, wrong peer, "
            "wrong ports/methods and direct Internet access denied.",
            flush=True,
        )
    finally:
        if running:
            run(["docker", "rm", "-f", container])
        for network in reversed(created):
            run(["docker", "network", "rm", network])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    try:
        check(parser.parse_args().image)
    except (ReleaseError, OSError, ValueError):
        raise SystemExit("Google egress validation failed; raw diagnostics withheld.") from None
