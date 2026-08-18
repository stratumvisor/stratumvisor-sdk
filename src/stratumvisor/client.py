"""Top-level STRATUM client."""
from __future__ import annotations

from typing import Any, Mapping, Optional

from requests import Session
from requests.auth import AuthBase

from .transport import CertValue, TimeoutValue, Transport, VerifyValue


class Stratum:
    """Synchronous STRATUM controller client.

    ``verify=False`` or ``insecure=True`` intentionally disables certificate,
    hostname, trust-chain, and expiration validation. Keep verification enabled
    for production whenever a trusted controller CA is available.
    """

    def __init__(
        self,
        base_url: str,
        *,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        cookies: Optional[Mapping[str, str]] = None,
        auth: Optional[AuthBase] = None,
        verify: VerifyValue = True,
        insecure: bool = False,
        cert: Optional[CertValue] = None,
        timeout: TimeoutValue = (10.0, 60.0),
        transfer_timeout: TimeoutValue = (30.0, None),
        retry_reads: int = 2,
        suppress_insecure_warnings: bool = True,
        session: Optional[Session] = None,
    ) -> None:
        if insecure:
            verify = False
        self.transport = Transport(
            base_url,
            username=username,
            password=password,
            token=token,
            cookies=cookies,
            auth=auth,
            verify=verify,
            cert=cert,
            timeout=timeout,
            transfer_timeout=transfer_timeout,
            retry_reads=retry_reads,
            suppress_insecure_warnings=suppress_insecure_warnings,
            session=session,
        )
        from .arsenal import ArsenalManager, BundleManager, MediaManager, TemplateManager
        from .datacenters import DatacenterManager
        from .ai import AIManager
        from .capture import CaptureManager
        from .fabrics import ComputeFabric, ExecutionFabric, GPUFabric, NetworkFabric, StorageFabric

        self.datacenters = DatacenterManager(self)
        self.templates = TemplateManager(self)
        self.arsenal = ArsenalManager(self)
        self.bundles = BundleManager(self)
        self.media = MediaManager(self)
        self.compute = ComputeFabric(self)
        self.execution = ExecutionFabric(self)
        self.gpu = GPUFabric(self)
        self.storage_fabric = StorageFabric(self)
        self.network_fabric = NetworkFabric(self)
        self.ai = AIManager(self)
        self.capture = CaptureManager(self)

    @property
    def base_url(self) -> str:
        return self.transport.base_url

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Raw HTTP escape hatch using the SDK's auth/TLS/error handling."""
        return self.transport.send(method, path, **kwargs)

    def health(self) -> Any:
        return self.request("GET", "/healthz")

    def auth_context(self) -> Any:
        return self.request("GET", "/api/stratum/auth/context")

    def whoami(self) -> Any:
        return self.request("GET", "/api/auth")

    def close(self) -> None:
        self.transport.close()

    def __enter__(self) -> "Stratum":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()
