"""Lightweight resource objects returned by high-level STRATUM APIs."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .client import Stratum


@dataclass
class Datacenter:
    client: "Stratum" = field(repr=False, compare=False)
    path: str = ""
    name: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def vms(self):
        from .vms import VMManager
        return VMManager(self.client, self.path)

    @property
    def networks(self):
        from .networks import NetworkManager
        return NetworkManager(self.client, self.path)

    def activate(self) -> "Datacenter":
        self.client.datacenters.activate(self.path)
        return self

    def topology(self) -> Dict[str, Any]:
        return self.client.datacenters.topology(self.path)

    def info(self) -> Any:
        return self.client.request("GET", "/api/labs/session/info", params={"path": self.path})

    def lock(self) -> Any:
        return self.client.request("POST", "/api/labs/session/lab/lock", json={"path": self.path})

    def unlock(self) -> Any:
        return self.client.request("POST", "/api/labs/session/lab/unlock", json={"path": self.path})

    def connect(self, source: Union["VM", str], source_if: str, destination: Union["VM", str], destination_if: str) -> Any:
        return self.networks.connect(source, source_if, destination, destination_if)

    def delete(self) -> Any:
        return self.client.datacenters.delete(self.path)

    def export(self, destination: Union[str, Path], **kwargs: Any) -> Path:
        return self.client.datacenters.export(self.path, destination, **kwargs)

    def update_metadata(self, **metadata: Any) -> Any:
        return self.client.datacenters.update_metadata(self.path, **metadata)


@dataclass
class VM:
    client: "Stratum" = field(repr=False, compare=False)
    datacenter_path: str = ""
    id: str = ""
    name: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.datacenter_path, self.id))

    def _manager(self):
        from .vms import VMManager
        return VMManager(self.client, self.datacenter_path)

    @property
    def snapshots(self):
        from .vms import SnapshotManager
        return SnapshotManager(self.client, self.datacenter_path, self.id)

    @property
    def disks(self):
        from .vms import DiskManager
        return DiskManager(self.client, self.datacenter_path, self.id)

    def refresh(self) -> "VM":
        current = self._manager().get(self.id)
        self.name = current.name
        self.raw = current.raw
        return self

    def edit(self, **changes: Any) -> Any:
        return self._manager().edit(self.id, **changes)

    def move(self, x: int, y: int) -> Any:
        return self.edit(left=int(x), top=int(y))

    def power_on(self) -> Any:
        return self._manager().power_on(self.id)

    start = power_on

    def power_off(self) -> Any:
        return self._manager().power_off(self.id)

    stop = power_off

    def pause(self) -> Any:
        return self._manager().pause(self.id)

    suspend = pause

    def resume(self) -> Any:
        return self._manager().resume(self.id)

    def hibernate(self) -> Any:
        return self._manager().hibernate(self.id)

    def consolidate(self) -> Any:
        return self._manager().consolidate(self.id)

    def wipe(self) -> Any:
        return self._manager().wipe(self.id)

    def migrate(self, target_host: str) -> Any:
        return self._manager().migrate(self.id, target_host)

    def delete(self) -> Any:
        return self._manager().delete(self.id)

    def status(self) -> Any:
        return self._manager().status([self.id])

    def console_link(self) -> Any:
        return self._manager().console_link(self.id)

    def media(self) -> Any:
        return self.client.request(
            "GET", "/api/labs/session/nodes/media",
            params={"path": self.datacenter_path, "id": self.id},
        )

    def mount_iso(
        self,
        media: Union["MediaItem", str],
        *,
        slot: str = "cdrom0",
        connect_at_power_on: bool = True,
        boot_once: bool = False,
    ) -> Any:
        media_id = media.id if isinstance(media, MediaItem) else str(media)
        return self.client.request(
            "POST", "/api/labs/session/nodes/media/change",
            json={
                "path": self.datacenter_path,
                "id": self.id,
                "slot": slot,
                "media_type": "arsenal-iso",
                "media_id": media_id,
                "connect_at_power_on": bool(connect_at_power_on),
                "boot_once": bool(boot_once),
            },
        )

    def mount_guest_tools(
        self,
        media_id: str,
        *,
        connect_at_power_on: bool = True,
    ) -> Any:
        return self.client.request(
            "POST", "/api/labs/session/nodes/media/change",
            json={
                "path": self.datacenter_path,
                "id": self.id,
                "slot": "guesttools0",
                "media_type": "guest-tools",
                "media_id": media_id,
                "connect_at_power_on": bool(connect_at_power_on),
                "boot_once": False,
            },
        )

    def eject_media(self, *, slot: str = "cdrom0", clear_power_on: bool = True) -> Any:
        return self.client.request(
            "POST", "/api/labs/session/nodes/media/eject",
            json={
                "path": self.datacenter_path,
                "id": self.id,
                "slot": slot,
                "clear_power_on": bool(clear_power_on),
            },
        )


@dataclass
class Template:
    client: "Stratum" = field(repr=False, compare=False)
    name: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)

    def refresh(self) -> "Template":
        current = self.client.templates.get(self.name)
        self.raw = current.raw
        return self


@dataclass
class MediaItem:
    client: "Stratum" = field(repr=False, compare=False)
    id: str = ""
    name: str = ""
    kind: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)
