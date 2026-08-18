"""STRATUM Infrastructure Reasoning Engine APIs."""
from __future__ import annotations
from typing import Any, Iterable, Mapping, Optional

class AIManager:
    def __init__(self, client: Any) -> None:
        self.client = client

    def status(self) -> Any:
        return self.client.request("GET", "/api/stratum/ai/status")

    @staticmethod
    def _request(*, path: str = "", messages: Optional[Iterable[Mapping[str, Any]]] = None,
                 focus: Optional[Iterable[Mapping[str, Any]]] = None, console_grant: Optional[Mapping[str, Any]] = None,
                 **extra: Any) -> dict[str, Any]:
        body: dict[str, Any] = dict(extra)
        if path:
            body["path"] = path
        if messages is not None:
            body["messages"] = [dict(x) for x in messages]
        if focus is not None:
            body["focus"] = [dict(x) for x in focus]
        if console_grant is not None:
            body["console_grant"] = dict(console_grant)
        return body

    def chat(self, *, path: str = "", messages=None, focus=None, console_grant=None, **extra: Any) -> Any:
        return self.client.request("POST", "/api/stratum/ai/chat", json=self._request(path=path, messages=messages, focus=focus, console_grant=console_grant, **extra))

    def start(self, *, path: str = "", messages=None, focus=None, console_grant=None, **extra: Any) -> Any:
        return self.client.request("POST", "/api/stratum/ai/chat/start", json=self._request(path=path, messages=messages, focus=focus, console_grant=console_grant, **extra))

    def job(self, job_id: str) -> Any:
        return self.client.request("GET", f"/api/stratum/ai/chat/jobs/{job_id}")

    def cancel(self, job_id: str) -> Any:
        return self.client.request("DELETE", f"/api/stratum/ai/chat/jobs/{job_id}")
