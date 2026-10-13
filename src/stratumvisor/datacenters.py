"""Datacenter management."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable, Optional, Union

from .exceptions import StratumNotFoundError
from .models import Datacenter
from .transport import ProgressCallback


class DatacenterManager:
    def __init__(self, client: Any) -> None:
        self.client = client

    @staticmethod
    def _object(client: Any, raw: dict[str, Any]) -> Datacenter:
        path = str(raw.get("path") or "")
        name = str(raw.get("display_name") or raw.get("name") or Path(path).stem)
        return Datacenter(client=client, path=path, name=name, raw=dict(raw))

    def list(self, path: str = "") -> list[Datacenter]:
        data = self.client.request("GET", "/api/labs", params={"path": path} if path else None)
        return [self._object(self.client, item) for item in (data or []) if isinstance(item, dict)]

    def get(self, path: str) -> Datacenter:
        normalized = path.replace("\\", "/").strip("/")
        parent = str(Path(normalized).parent).replace("\\", "/")
        if parent == ".":
            parent = ""
        for dc in self.list(parent):
            if dc.path == normalized:
                return dc
        raise StratumNotFoundError(f"datacenter not found: {path}", status_code=404)

    def create(
        self,
        name: str,
        *,
        folder: str = "",
        description: str = "",
        version: str = "",
        author: str = "",
        source: str = "",
        region: str = "",
        classification: str = "",
        tags: Optional[Iterable[str]] = None,
        placement_site: str = "",
        placement_host: str = "",
        lat: str = "",
        lng: str = "",
        activate: bool = True,
    ) -> Datacenter:
        body = {
            "path": folder,
            "name": name,
            "description": description,
            "version": version,
            "author": author,
            "source": source,
            "region": region,
            "classification": classification,
            "tags": list(tags or []),
            "placement_site": placement_site,
            "placement_host": placement_host,
            "lat": lat,
            "lng": lng,
        }
        raw = self.client.request("POST", "/api/labs", json=body) or {}
        dc = self._object(self.client, raw)
        if activate:
            self.activate(dc.path)
        return dc

    def activate(self, path: str) -> Datacenter:
        raw = self.client.request("POST", "/api/labs/session/factory/create", json={"path": path}) or {}
        return Datacenter(
            client=self.client,
            path=str(raw.get("labPath") or path),
            name=Path(str(raw.get("labPath") or path)).stem,
            raw=dict(raw),
        )

    open = activate

    def delete(self, path: str) -> Any:
        return self.client.request("DELETE", "/api/labs", json={"path": path})

    def archive(self, path: str) -> Any:
        return self.client.request("POST", "/api/labs/archive", json={"path": path})

    def restore(self, path: str) -> Any:
        return self.client.request("POST", "/api/labs/restore", json={"path": path})

    def update_metadata(self, path: str, **metadata: Any) -> Any:
        body = {"path": path}
        body.update(metadata)
        return self.client.request("POST", "/api/labs/metadata", json=body)

    def topology(self, path: str) -> dict[str, Any]:
        return self.client.request("GET", "/api/labs/session/topology", params={"path": path}) or {}

    def import_(
        self,
        source: Union[str, os.PathLike],
        *,
        name: Optional[str] = None,
        reset_macs: bool = False,
        progress: Optional[ProgressCallback] = None,
        activate: bool = False,
    ) -> Any:
        fields = {"reset_macs": "true" if reset_macs else "false"}
        if name:
            fields["name"] = name
        result = self.client.transport.multipart(
            "POST", "/api/labs/import",
            fields=fields,
            file_fields={"file": source},
            progress=progress,
        )
        if activate and isinstance(result, dict):
            path = result.get("path") or result.get("labPath")
            if path:
                self.activate(str(path))
        return result

    import_bundle = import_

    def export(
        self,
        path: str,
        destination: Union[str, os.PathLike],
        *,
        progress: Optional[ProgressCallback] = None,
    ) -> Path:
        return self.client.transport.download(
            "GET", "/api/labs/export", destination,
            params={"path": path}, progress=progress,
        )
