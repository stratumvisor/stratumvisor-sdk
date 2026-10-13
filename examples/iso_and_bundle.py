from stratumvisor import Stratum


def progress(done, total):
    if total:
        print(f"{done}/{total} ({done * 100 / total:.1f}%)")


with Stratum("https://stratum.example.net:8443", username="automation", password="change-me") as s:
    iso = s.media.upload_iso("/tmp/install.iso", progress=progress)
    print("media id:", iso.id)

    print(s.bundles.candidates())
