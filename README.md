# STRATUMvisor Python SDK

The STRATUMvisor Python SDK provides a synchronous Python interface for automating STRATUM through its HTTPS API.

## Install

From the source package:

```bash
python -m pip install .
```

Python code imports the package as `stratumvisor`:

```python
from stratumvisor import Stratum
```

## Connect

```python
import os
from stratumvisor import Stratum

stratum = Stratum(
    os.environ["STRATUM_URL"],
    username=os.environ["STRATUM_USERNAME"],
    password=os.environ["STRATUM_PASSWORD"],
)
```

Bearer tokens, cookies, custom `requests` authentication, private CA files, and optional client certificates are also supported.

TLS certificate verification is enabled by default. For environments where certificate verification must be disabled explicitly, use `insecure=True`.

## Datacenters and VMs

```python
with stratum:
    dc = stratum.datacenters.create(
        "SDK Demo",
        description="Created by Python automation",
        tags=["sdk", "demo"],
    )

    server = dc.vms.deploy(
        template="ubuntu-24",
        name="server1",
        x=250,
        y=200,
        ethernet=2,
    )

    client = dc.vms.deploy(
        template="ubuntu-24",
        name="client1",
        x=600,
        y=200,
    )

    dc.connect(server, "0", client, "0")
    server.power_on()
    client.power_on()
```

The SDK supports common VM lifecycle operations including deploy, edit, move, power on/off, pause/resume, hibernate, migrate, wipe, delete, status, and console access.

## Disks and snapshots

```python
vm.disks.add(40)
vm.disks.grow("disk1.qcow2", 80)

vm.snapshots.create("before-upgrade", include_memory=False)
print(vm.snapshots.list())
vm.snapshots.revert("snapshot-id")
```

## ISO Library and removable media

```python
iso = stratum.media.upload_iso("/isos/install.iso")
vm.mount_iso(iso, boot_once=True)
vm.eject_media()
```

Large uploads and downloads are streamed instead of being loaded entirely into memory.

## Datacenter import and export

```python
stratum.datacenters.export("SDK Demo.unl", "/backups/sdk-demo.zip")

stratum.datacenters.import_(
    "/backups/sdk-demo.zip",
    name="SDK Demo Copy",
    reset_macs=True,
)
```

## Templates and Arsenal

```python
for template in stratum.templates.list():
    print(template.name)

created = stratum.templates.create(
    "ubuntu-24-custom",
    cpu="4",
    ram="8192",
    ethernet=2,
    console="vnc",
    qemuArch="x86_64",
)
```

The SDK also provides Arsenal file, image, revision, bundle, template, and media operations.

## Fabrics

```python
print(stratum.compute.status())
print(stratum.execution.workers())
print(stratum.gpu.inventory())
print(stratum.storage_fabric.status())
print(stratum.network_fabric.status())
```

## STRATUM AI

```python
print(stratum.ai.status())

job = stratum.ai.start(
    path="Demo.unl",
    messages=[
        {
            "role": "user",
            "content": "Troubleshoot why server1 cannot reach client1",
        }
    ],
)

print(stratum.ai.job(job["job_id"]))
```

## Packet capture

```python
interfaces = stratum.capture.interfaces("Demo.unl", "switch1")

stratum.capture.start("Demo.unl", "switch1", "eth1", direction="both")
packets = stratum.capture.packets("Demo.unl", "switch1", "eth1")
stratum.capture.stop("Demo.unl", "switch1", "eth1")
stratum.capture.export(
    "Demo.unl",
    "switch1",
    "eth1",
    "/tmp/switch1-eth1.pcap",
)
```

## Raw API access

For endpoints without a dedicated convenience wrapper, use the authenticated raw request method:

```python
payload = stratum.request(
    "POST",
    "/api/labs/session/nodes/edit",
    json={"path": "Demo.unl", "id": "1", "ram": "16384"},
)
```

Raw requests use the same authentication, TLS, timeout, and error handling as the rest of the SDK.

## Errors

HTTP and transport failures are mapped to STRATUM SDK exceptions:

```python
from stratumvisor import (
    StratumAuthenticationError,
    StratumAuthorizationError,
    StratumConflictError,
    StratumValidationError,
)
```

Read-only requests may retry connection-establishment failures. Mutating requests are not automatically retried.

Copyright Cyber Ballistics Inc. / STRATUMvisor
