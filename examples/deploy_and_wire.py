import os

from stratumvisor import Stratum


with Stratum(
    os.environ["STRATUM_URL"],
    username=os.environ["STRATUM_USERNAME"],
    password=os.environ["STRATUM_PASSWORD"],
) as stratum:
    dc = stratum.datacenters.create("Python SDK Demo")
    a = dc.vms.deploy(template="ubuntu-24", name="a", x=200, y=200)
    b = dc.vms.deploy(template="ubuntu-24", name="b", x=500, y=200)
    dc.connect(a, "0", b, "0")
    a.power_on()
    b.power_on()
