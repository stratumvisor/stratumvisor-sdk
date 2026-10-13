# STRATUM Python SDK 0.3.0

A Python client for the STRATUM HTTPS API.

## Installation

Requires Python 3.9 or newer.

```bash
python -m pip install stratumvisor_sdk-0.3.0-py3-none-any.whl
```

## Connection

```python
from stratumvisor import Stratum

with Stratum("https://stratum.example.net:8443", token="your-token") as stratum:
    print(stratum.datacenters.list())
```

Use the authentication method supported by your STRATUM deployment. TLS certificate verification is required. For private certificate authorities, set `verify="/path/to/ca.pem"`.

## Common operations

```python
with Stratum("https://stratum.example.net:8443", token="your-token") as stratum:
    dc = stratum.datacenters.create("Example")
    vm = dc.vms.deploy(template="ubuntu-24", name="web-01", x=200, y=200)
    vm.power_on()
    print(vm.status())
```

Additional methods cover networks, disks, snapshots, images, file transfers, schedules, and AI Missions. Use `stratum.operations.list()` to see the included operations or `stratum.operations.call(operation_id, ...)` to invoke one by name.

