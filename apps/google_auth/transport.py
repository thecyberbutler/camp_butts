"""Google-only HTTPS through the approved private CONNECT proxy; no TLS interception."""

import requests

from .constants import PEOPLE_SELF_URL


class GoogleSession(requests.Session):
    def __init__(self):
        super().__init__()
        self.trust_env = False

    def request(self, method, url, **kwargs):
        permitted = {
            ("POST", "https://oauth2.googleapis.com/token"),
            ("GET", "https://www.googleapis.com/oauth2/v1/certs"),
            ("GET", PEOPLE_SELF_URL),
        }
        if (method.upper(), url) not in permitted or kwargs.get("params"):
            raise requests.RequestException("Unapproved identity-provider endpoint")
        kwargs.update(
            allow_redirects=False,
            verify=True,
            timeout=(3.05, 10),
            proxies={"https": "http://google-egress:3128"},
            stream=True,
        )
        response = super().request(method, url, **kwargs)
        try:
            if response.status_code != 200:
                raise requests.RequestException("Identity-provider request failed")
            content = bytearray()
            for chunk in response.iter_content(8192):
                content.extend(chunk)
                if len(content) > 65536:
                    raise requests.RequestException("Identity-provider response exceeds limit")
            response._content = bytes(content)
            response._content_consumed = True
            return response
        finally:
            response.close()
            self.cookies.clear()
