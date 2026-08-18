import os

from stratumvisor import Stratum


def progress(done, total):
    if total:
        print(f"{done}/{total} ({done * 100 / total:.1f}%)")


with Stratum(
    os.environ["STRATUM_URL"],
    username=os.environ["STRATUM_USERNAME"],
    password=os.environ["STRATUM_PASSWORD"],
) as stratum:
    iso = stratum.media.upload_iso("/isos/install.iso", progress=progress)
    print("media id:", iso.id)
    print(stratum.bundles.candidates())
