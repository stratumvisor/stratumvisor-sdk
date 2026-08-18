"""Datacenter topology wiring and network/interface operations."""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Union

from .models import VM


def _id(value: Union[VM, str]) -> str:
    return value.id if isinstance(value, VM) else str(value)


class NetworkManager:
    def __init__(self, client: Any, path: str) -> None:
        self.client, self.path = client, path

    def list(self) -> Any:
        topology = self.client.datacenters.topology(self.path)
        return topology.get("networks", {}) if isinstance(topology, dict) else {}

    def add(
        self,
        name: str,
        *,
        network_type: str = "bridge",
        x: int = 0,
        y: int = 0,
        visibility: Union[str, int, bool] = "1",
        **extra: Any,
    ) -> Any:
        body = {
            "path": self.path, "name": name, "type": network_type,
            "left": int(x), "top": int(y), "visibility": visibility,
        }
        body.update(extra)
        return self.client.request("POST", "/api/labs/session/networks/add", json=body)

    def edit(self, network_id: str, **changes: Any) -> Any:
        body = {"path": self.path, "id": str(network_id)}
        body.update(changes)
        return self.client.request("POST", "/api/labs/session/networks/edit", json=body)

    def delete(self, network_ids: Union[str, Iterable[str]]) -> Any:
        ids = [network_ids] if isinstance(network_ids, str) else [str(x) for x in network_ids]
        return self.client.request(
            "POST", "/api/labs/session/networks/delete",
            json={"path": self.path, "ids": ids},
        )

    def connect(
        self,
        source: Union[VM, str],
        source_if: str,
        destination: Union[VM, str],
        destination_if: str,
    ) -> Any:
        return self.client.request(
            "POST", "/api/labs/session/networks/p2p",
            json={
                "path": self.path,
                "src_id": _id(source), "src_if": str(source_if),
                "dest_id": _id(destination), "dest_if": str(destination_if),
            },
        )

    wire = connect

    def edit_interface(self, node: Union[VM, str], interface_id: str, **changes: Any) -> Any:
        body = {"path": self.path, "node_id": _id(node), "interface_id": str(interface_id)}
        body.update(changes)
        return self.client.request("POST", "/api/labs/session/interfaces/edit", json=body)

    def set_quality(
        self,
        node: Union[VM, str],
        interface_id: str,
        *,
        quality: str = "",
        delay: str = "",
        loss: str = "",
        jitter: str = "",
        rate: str = "",
    ) -> Any:
        return self.client.request(
            "POST", "/api/labs/session/interfaces/setquality",
            json={
                "path": self.path, "node_id": _id(node), "interface_id": str(interface_id),
                "quality": quality, "delay": delay, "loss": loss,
                "jitter": jitter, "rate": rate,
            },
        )

    def set_suspended(self, node: Union[VM, str], interface_id: str, suspended: bool = True) -> Any:
        return self.client.request(
            "POST", "/api/labs/session/interfaces/setSuspend",
            json={
                "path": self.path, "node_id": _id(node),
                "interface_id": str(interface_id), "suspend": bool(suspended),
            },
        )

    def set_suspended_two_way(self, node: Union[VM, str], interface_id: str, suspended: bool = True) -> Any:
        return self.client.request(
            "POST", "/api/labs/session/interfaces/setSuspendtwo_way",
            json={
                "path": self.path, "node_id": _id(node),
                "interface_id": str(interface_id), "suspend": bool(suspended),
            },
        )
