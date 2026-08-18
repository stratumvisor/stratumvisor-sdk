"""Compute, GPU, storage, and Continuum network-fabric APIs."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable, Optional, Union

from .transport import ProgressCallback


class ComputeFabric:
    def __init__(self, client: Any) -> None:
        self.client = client

    def status(self) -> Any:
        return self.client.request("GET", "/api/stratum/compute-fabric")

    def workers(self) -> Any:
        return self.client.request("GET", "/api/stratum/execution/workers")

    def execution_capabilities(self) -> Any:
        return self.client.request("GET", "/api/stratum/execution/capabilities")

    def execution_inventory(self) -> Any:
        return self.client.request("GET", "/api/stratum/execution/inventory")

    def encrypted_runtime_capabilities(self) -> Any:
        return self.client.request("GET", "/api/stratum/encrypted-runtime/capabilities")

    def repair(self, **options: Any) -> Any:
        return self.client.request("POST", "/api/stratum/compute-fabric/repair", json=options or {})


class ExecutionFabric:
    """Native STRATUM execution-fabric inspection APIs."""
    def __init__(self, client: Any) -> None:
        self.client = client

    def workers(self) -> Any:
        return self.client.request("GET", "/api/stratum/execution/workers")

    def capabilities(self) -> Any:
        return self.client.request("GET", "/api/stratum/execution/capabilities")

    def inventory(self) -> Any:
        return self.client.request("GET", "/api/stratum/execution/inventory")


class GPUFabric:
    def __init__(self, client: Any) -> None:
        self.client = client

    def inventory(self) -> Any:
        return self.client.request("GET", "/api/stratum/gpu-fabric/inventory")

    def leases(self) -> Any:
        return self.client.request("GET", "/api/stratum/gpu-fabric/leases")

    def quote(self, *, gpu_type: str = "", count: int = 0, **query: Any) -> Any:
        params = dict(query)
        if gpu_type:
            params["type"] = gpu_type
        params["count"] = int(count)
        return self.client.request("GET", "/api/stratum/gpu-fabric/quote", params=params)


class StorageFabric:
    def __init__(self, client: Any) -> None:
        self.client = client

    def status(self) -> Any:
        return self.client.request("GET", "/api/stratum/storage-fabric/status")

    def place(self, image_names: Union[str, Iterable[str]], *, node_id: str = "") -> Any:
        names = [image_names] if isinstance(image_names, str) else list(image_names)
        body: dict[str, Any] = {"image_names": names}
        if node_id:
            body["node_id"] = node_id
        return self.client.request("POST", "/api/stratum/storage-fabric/placement", json=body)

    def bake(self, image_names: Union[str, Iterable[str]], *, node_id: str = "", force: bool = False) -> Any:
        names = [image_names] if isinstance(image_names, str) else list(image_names)
        body: dict[str, Any] = {"image_names": names, "force": bool(force)}
        if node_id:
            body["node_id"] = node_id
        return self.client.request("POST", "/api/stratum/storage-fabric/bake", json=body)


class NetworkFabric:
    def __init__(self, client: Any) -> None:
        self.client = client

    def status(self) -> Any:
        return self.client.request("GET", "/api/stratum/network-fabric/status")

    def settings(self, **settings: Any) -> Any:
        return self.client.request("POST", "/api/stratum/network-fabric/settings", json=settings)

    def rotate_token(self, **options: Any) -> Any:
        return self.client.request("POST", "/api/stratum/network-fabric/token/rotate", json=options or {})

    def download_token(self, destination: Union[str, os.PathLike]) -> Path:
        return self.client.transport.download("GET", "/api/stratum/network-fabric/token/download", destination)

    def download_controller_ca(self, destination: Union[str, os.PathLike]) -> Path:
        return self.client.transport.download("GET", "/api/stratum/network-fabric/controller-ca", destination)

    def update_node(self, **node: Any) -> Any:
        return self.client.request("POST", "/api/stratum/network-fabric/nodes/update", json=node)

    def remove_node(self, **node: Any) -> Any:
        return self.client.request("POST", "/api/stratum/network-fabric/nodes/remove", json=node)
