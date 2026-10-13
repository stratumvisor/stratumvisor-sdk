from stratumvisor import Stratum

with Stratum("https://stratum.example.net:8443", token="your-token") as stratum:
    print(stratum.datacenters.list())
    print(stratum.ai.missions.list())
