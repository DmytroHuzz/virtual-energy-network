import ast
import json
import pathlib
import re
import subprocess


ROOT = pathlib.Path(__file__).resolve().parent
SCENARIO = ROOT / "virtual-energy-network"
manifest = json.loads((SCENARIO / "index.json").read_text())
details = manifest["details"]
for section in [details["intro"], *details["steps"], details["finish"]]:
    for key in ("text", "verify", "foreground", "background"):
        if key in section:
            assert (SCENARIO / section[key]).is_file(), section[key]

for source in SCENARIO.rglob("*.py"):
    ast.parse(source.read_text(), filename=str(source))
for source in SCENARIO.rglob("*.sh"):
    subprocess.run(["bash", "-n", str(source)], check=True)

walkthrough = [
    "#!/bin/bash",
    "set -euo pipefail",
    "cd /root/energy-lab",
    "bash lab.sh reset",
    "mkdir -p run",
    "touch /tmp/energy-lab.ready",
    "if python3 check.py 1; then echo 'Empty topology incorrectly passed'; exit 1; fi",
]
for stage, section in enumerate(details["steps"], start=1):
    text = (SCENARIO / section["text"]).read_text()
    blocks = re.findall(r"```bash\n(.*?)\n```\{\{exec\}\}", text, re.DOTALL)
    assert blocks, section["text"]
    for block in blocks:
        subprocess.run(["bash", "-n"], input=block, text=True, check=True)
        walkthrough.append(block.replace(
            "ip netns exec lab-gw timeout 15 tcpdump -l -ni any 'tcp port 10000'",
            "ip netns exec lab-gw timeout 3 tcpdump -l -ni any 'tcp port 10000' || [[ $? == 124 ]]",
        ))
    walkthrough.append(f"python3 check.py {stage}")

walkthrough.extend([
    "ip -n lab-led1 link set eth0 down",
    "if python3 check.py 7; then echo 'Broken LED incorrectly passed'; exit 1; fi",
    "ip -n lab-led1 link set eth0 up",
    "bash lab.sh start 1",
    "sleep 2",
    "python3 check.py 7",
    "ip -n lab-ld1 route del default",
    "if python3 check.py 6; then echo 'Missing return route incorrectly passed'; exit 1; fi",
    "ip -n lab-ld1 route add default via 10.20.0.1",
    "python3 check.py 7",
    "echo 'All seven checkpoints, negative checks and repairs passed.'",
])
destination = SCENARIO / "assets" / "walkthrough.sh"
destination.write_text("\n\n".join(walkthrough) + "\n")
subprocess.run(["bash", "-n", str(destination)], check=True)
print("Manifest paths, Python syntax, Bash syntax and lesson commands passed.")
print(f"Generated {destination}")
