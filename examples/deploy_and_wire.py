from stratumvisor import Stratum

s = Stratum(
    "https://stratum.example.net:8443",
    username="automation",
    password="change-me",
)

with s:
    dc = s.datacenters.create("Python SDK Demo")
    a = dc.vms.deploy(template="ubuntu-24", name="a", x=200, y=200)
    b = dc.vms.deploy(template="ubuntu-24", name="b", x=500, y=200)
    dc.connect(a, "0", b, "0")
    a.power_on()
    b.power_on()
