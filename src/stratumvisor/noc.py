"""STRATUM NOC APIs."""
from __future__ import annotations

from typing import Any


class NOCManager:
    def __init__(self, client: Any) -> None:
        self.client = client

    def status(self) -> Any:
        return self.client.request('GET', '/api/stratum/noc')

