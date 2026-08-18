"""Deployed VM/node lifecycle, disk, and snapshot APIs."""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional, Sequence, Union

from .exceptions import StratumNotFoundError
from .models import VM

NodeRef = Union[str, VM]


def _node_id(node: NodeRef) -> str:
    return node.id if isinstance(node, VM) else str(node)


class VMManager:
    def __init__(self, client: Any, datacenter_path: str) -> None:
        self.client = client
        self.path = datacenter_path

    def list(self) -> list[VM]:
        topology = self.client.datacenters.topology(self.path)
        raw_nodes = topology.get("nodes", {}) if isinstance(topology, dict) else {}
        items: list[dict[str, Any]] = []
        if isinstance(raw_nodes, dict):
            for key, value in raw_nodes.items():
                if isinstance(value, dict):
                    item = dict(value)
                    item.setdefault("id", str(key))
                    items.append(item)
        elif isinstance(raw_nodes, list):
            items = [dict(x) for x in raw_nodes if isinstance(x, dict)]
        return [self._vm(item) for item in items]

    def _vm(self, raw: Mapping[str, Any]) -> VM:
        return VM(
            client=self.client,
            datacenter_path=self.path,
            id=str(raw.get("id") or raw.get("node_id") or ""),
            name=str(raw.get("name") or ""),
            raw=dict(raw),
        )

    def get(self, node: NodeRef) -> VM:
        node_id = _node_id(node)
        data = self.client.request(
            "GET", "/api/labs/session/nodes",
            params={"path": self.path, "id": node_id},
        )
        if isinstance(data, dict):
            # nodeDetails returns the node directly when an id is supplied.
            candidate = data.get("node") if isinstance(data.get("node"), dict) else data
            if isinstance(candidate, dict) and (candidate.get("id") or node_id):
                candidate = dict(candidate)
                candidate.setdefault("id", node_id)
                return self._vm(candidate)
        raise StratumNotFoundError(f"VM/node not found: {node_id}", status_code=404)

    def deploy(
        self,
        *,
        template: str,
        name: str,
        x: int = 0,
        y: int = 0,
        ethernet: Optional[int] = None,
        count: int = 1,
        postfix: int = 1,
        **settings: Any,
    ) -> Union[VM, list[VM]]:
        body: dict[str, Any] = {
            "path": self.path,
            "template": template,
            "name": name,
            "left": int(x),
            "top": int(y),
            "count": int(count),
            "postfix": int(postfix),
        }
        if ethernet is not None:
            body["ethernet"] = int(ethernet)
        body.update(settings)
        data = self.client.request("POST", "/api/labs/session/nodes/add", json=body) or {}
        created = data.get("nodes") if isinstance(data, dict) else None
        if isinstance(created, list) and created:
            vms = [self._vm(x) for x in created if isinstance(x, dict)]
            return vms[0] if count == 1 and len(vms) == 1 else vms
        node = data.get("node") if isinstance(data, dict) else None
        if isinstance(node, dict):
            return self._vm(node)
        node_id = str(data.get("node_id") or "") if isinstance(data, dict) else ""
        return VM(self.client, self.path, node_id, name, dict(data) if isinstance(data, dict) else {})

    add = deploy

    def edit(self, node: NodeRef, **changes: Any) -> Any:
        body = {"path": self.path, "id": _node_id(node)}
        body.update(changes)
        return self.client.request("POST", "/api/labs/session/nodes/edit", json=body)

    def batch_edit(self, updates: Sequence[Mapping[str, Any]]) -> Any:
        if len(updates) > 2000:
            raise ValueError("STRATUM accepts at most 2000 node updates per batch")
        nodes = [dict(item) for item in updates]
        for item in nodes:
            item.pop("path", None)
        return self.client.request(
            "POST", "/api/labs/session/nodes/edit/batch",
            json={"path": self.path, "nodes": nodes},
        )

    def move_many(self, positions: Mapping[NodeRef, tuple[int, int]]) -> Any:
        return self.batch_edit([
            {"id": _node_id(node), "left": int(pos[0]), "top": int(pos[1])}
            for node, pos in positions.items()
        ])

    def _action(self, endpoint: str, nodes: Union[NodeRef, Iterable[NodeRef]]) -> Any:
        if isinstance(nodes, (str, VM)):
            ids = [_node_id(nodes)]
        else:
            ids = [_node_id(x) for x in nodes]
        return self.client.request(
            "POST", f"/api/labs/session/nodes/{endpoint}",
            json={"path": self.path, "nodes": ids},
        )

    def power_on(self, nodes: Union[NodeRef, Iterable[NodeRef]]) -> Any:
        return self._action("start", nodes)

    start = power_on

    def power_off(self, nodes: Union[NodeRef, Iterable[NodeRef]]) -> Any:
        return self._action("stop", nodes)

    stop = power_off

    def pause(self, nodes: Union[NodeRef, Iterable[NodeRef]]) -> Any:
        return self._action("pause", nodes)

    suspend = pause

    def resume(self, nodes: Union[NodeRef, Iterable[NodeRef]]) -> Any:
        return self._action("resume", nodes)

    def hibernate(self, nodes: Union[NodeRef, Iterable[NodeRef]]) -> Any:
        return self._action("hibernate", nodes)

    def consolidate(self, nodes: Union[NodeRef, Iterable[NodeRef]]) -> Any:
        return self._action("consolidate", nodes)

    def wipe(self, nodes: Union[NodeRef, Iterable[NodeRef]]) -> Any:
        return self._action("wipe", nodes)

    def export_nodes(self, nodes: Union[NodeRef, Iterable[NodeRef]], export_to: str = "") -> Any:
        if isinstance(nodes, (str, VM)):
            ids = [_node_id(nodes)]
        else:
            ids = [_node_id(x) for x in nodes]
        body: dict[str, Any] = {"path": self.path, "nodes": ids}
        if export_to:
            body["export_to"] = export_to
        return self.client.request("POST", "/api/labs/session/nodes/export", json=body)

    def delete(self, nodes: Union[NodeRef, Iterable[NodeRef]]) -> Any:
        if isinstance(nodes, (str, VM)):
            ids = [_node_id(nodes)]
        else:
            ids = [_node_id(x) for x in nodes]
        return self.client.request(
            "POST", "/api/labs/session/nodes/delete",
            json={"path": self.path, "ids": ids},
        )

    def migrate(self, node: NodeRef, target_host: str) -> Any:
        return self.client.request(
            "POST", "/api/labs/session/nodes/migrate",
            json={"path": self.path, "id": _node_id(node), "target_host": target_host},
        )

    def status(self, nodes: Iterable[NodeRef]) -> Any:
        return self.client.request(
            "POST", "/api/labs/session/nodestatus",
            json={"path": self.path, "nodes": [_node_id(x) for x in nodes]},
        )

    def console_link(self, node: NodeRef) -> Any:
        return self.client.request(
            "GET", "/api/labs/session/console_guac_link",
            params={"path": self.path, "id": _node_id(node)},
        )

    def switch_status(self, node: NodeRef) -> Any:
        return self.client.request(
            "GET", "/api/labs/session/nodes/stratumswitch",
            params={"path": self.path, "id": _node_id(node)},
        )

    def switch_command(self, node: NodeRef, **command: Any) -> Any:
        body = {"path": self.path, "id": _node_id(node)}
        body.update(command)
        return self.client.request("POST", "/api/labs/session/nodes/stratumswitch", json=body)


class SnapshotManager:
    def __init__(self, client: Any, path: str, node_id: str) -> None:
        self.client, self.path, self.node_id = client, path, node_id

    def list(self) -> Any:
        return self.client.request(
            "GET", "/api/labs/session/nodes/snapshots",
            params={"path": self.path, "id": self.node_id},
        )

    def create(self, name: str = "", description: str = "", *, include_memory: bool = False) -> Any:
        return self.client.request(
            "POST", "/api/labs/session/nodes/snapshots/create",
            json={
                "path": self.path, "id": self.node_id, "name": name,
                "description": description, "include_memory": bool(include_memory),
            },
        )

    def revert(self, snapshot_id: str) -> Any:
        return self.client.request(
            "POST", "/api/labs/session/nodes/snapshots/revert",
            json={"path": self.path, "id": self.node_id, "snapshot_id": snapshot_id},
        )

    def delete(self, snapshot_id: str) -> Any:
        return self.client.request(
            "POST", "/api/labs/session/nodes/snapshots/delete",
            json={"path": self.path, "id": self.node_id, "snapshot_id": snapshot_id},
        )


class DiskManager:
    def __init__(self, client: Any, path: str, node_id: str) -> None:
        self.client, self.path, self.node_id = client, path, node_id

    def list(self) -> Any:
        return self.client.request(
            "GET", "/api/labs/session/nodes/disks",
            params={"path": self.path, "id": self.node_id},
        )

    def add(self, size_gib: float) -> Any:
        return self.client.request(
            "POST", "/api/labs/session/nodes/disks/add",
            json={"path": self.path, "id": self.node_id, "size_gib": float(size_gib)},
        )

    def grow(self, disk_name: str, size_gib: float) -> Any:
        return self.client.request(
            "POST", "/api/labs/session/nodes/disks/grow",
            json={
                "path": self.path, "id": self.node_id,
                "disk_name": disk_name, "size_gib": float(size_gib),
            },
        )

    def delete(self, disk_name: str) -> Any:
        return self.client.request(
            "POST", "/api/labs/session/nodes/disks/delete",
            json={"path": self.path, "id": self.node_id, "disk_name": disk_name},
        )
