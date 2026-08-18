# STRATUM 1.0 Python SDK

`stratumvisor-sdk` is the Python SDK for automating STRATUM 1.0 through its HTTPS API.

## Client

```python
import os
from stratumvisor import Stratum

stratum = Stratum(
    os.environ["STRATUM_URL"],
    username=os.environ["STRATUM_USERNAME"],
    password=os.environ["STRATUM_PASSWORD"],
)
```

The client supports HTTP Basic authentication, Bearer tokens, existing cookies, custom `requests` authentication, custom CA certificates, mutual TLS, configurable timeouts, and explicit insecure TLS operation when required.

## API namespaces

The main client exposes these Python interfaces:

- `stratum.datacenters` — datacenter create, list, open, update, archive, restore, import, and export
- `Datacenter.vms` — VM deployment, lifecycle, status, migration, console, disks, snapshots, and media
- `Datacenter.networks` — network creation, editing, wiring, interface settings, and link quality
- `stratum.templates` — template list, inspect, create, rename, delete, and import
- `stratum.arsenal` — Arsenal trees, items, revisions, files, images, jobs, and VM promotion
- `stratum.bundles` — bundle import and export
- `stratum.media` — ISO Library access and uploads
- `stratum.compute` — Compute Fabric status and operations
- `stratum.execution` — execution worker and capability information
- `stratum.gpu` — GPU Fabric inventory, leases, and quotes
- `stratum.storage_fabric` — Storage Fabric status, placement, and bake operations
- `stratum.network_fabric` — Continuum Network Fabric status and management
- `stratum.ai` — STRATUM AI requests and jobs
- `stratum.capture` — STRATUMswitch packet capture

## Raw requests

The SDK includes `stratum.request()` for authenticated access to STRATUM API endpoints without a dedicated Python convenience method.

```python
result = stratum.request("GET", "/api/example")
```

The raw request path uses the SDK transport, including authentication, TLS verification, timeouts, response decoding, and exception mapping.

## Package version

This release is `0.2.0`.

Copyright Cyber Ballistics Inc. / STRATUMvisor
