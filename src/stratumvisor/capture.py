"""Controller-mediated STRATUMswitch packet capture APIs."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Optional, Union
import os
from .transport import ProgressCallback

class CaptureManager:
    def __init__(self, client: Any) -> None:
        self.client = client

    @staticmethod
    def _params(path: str, node_id: str, interface: str = "") -> dict[str, Any]:
        p: dict[str, Any] = {"path": path, "id": node_id}
        if interface:
            p["interface"] = interface
        return p

    def interfaces(self, path: str, node_id: str) -> Any:
        return self.client.request("GET", "/api/stratum/capture/interfaces", params=self._params(path, node_id))

    def start(self, path: str, node_id: str, interface: str, *, direction: str = "both",
              max_bytes: int = 0, duration: int = 0, filter_mac: str = "") -> Any:
        body = {"path": path, "id": node_id, "interface": interface, "direction": direction}
        if max_bytes:
            body["max_bytes"] = int(max_bytes)
        if duration:
            body["duration"] = int(duration)
        if filter_mac:
            body["filter_mac"] = filter_mac
        return self.client.request("POST", "/api/stratum/capture/start", json=body)

    def stop(self, path: str, node_id: str, interface: str) -> Any:
        return self.client.request("POST", "/api/stratum/capture/stop", json={"path": path, "id": node_id, "interface": interface})

    def packets(self, path: str, node_id: str, interface: str, *, offset: int = 0, packet_start: int = 1) -> Any:
        params = self._params(path, node_id, interface)
        params.update({"offset": int(offset), "packet_start": int(packet_start)})
        return self.client.request("GET", "/api/stratum/capture/packets", params=params)

    def export(self, path: str, node_id: str, interface: str, destination: Union[str, os.PathLike], *, progress: Optional[ProgressCallback] = None) -> Path:
        return self.client.transport.download("GET", "/api/stratum/capture/export", destination, params=self._params(path, node_id, interface), progress=progress)
