"""Authentication helpers for STRATUM's public reverse-proxy edge."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from requests.auth import AuthBase, HTTPBasicAuth


@dataclass(frozen=True)
class BasicAuth:
    username: str
    password: str

    def requests_auth(self) -> AuthBase:
        return HTTPBasicAuth(self.username, self.password)


@dataclass(frozen=True)
class BearerAuth:
    token: str

    def header(self) -> str:
        return f"Bearer {self.token}"


@dataclass(frozen=True)
class CookieAuth:
    cookies: Mapping[str, str]


AuthConfig = Optional[AuthBase]
