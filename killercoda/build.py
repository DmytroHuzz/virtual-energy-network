import pathlib
import shutil
import tarfile


ROOT = pathlib.Path(__file__).resolve().parent.parent
SCENARIO = ROOT / "killercoda" / "virtual-energy-network"

for name in ("helpers.py", "logical_device.py", "sensor.py", "alert_led.py", "superviser.py"):
    shutil.copyfile(ROOT / name, SCENARIO / "assets" / name)

for stage in range(1, 8):
    destination = SCENARIO / "checks" / f"{stage:02}.sh"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(
        f"#!/bin/bash\ncd /root/energy-lab && python3 check.py {stage}\n"
    )

archive = ROOT / "killercoda" / "virtual-energy-network.tar.gz"
with tarfile.open(archive, "w:gz") as bundle:
    bundle.add(SCENARIO, arcname=SCENARIO.name)
print(f"Built {archive}")
