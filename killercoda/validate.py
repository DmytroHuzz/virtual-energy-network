import ast
import json
import pathlib
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit


ROOT = pathlib.Path(__file__).resolve().parent.parent
SCENARIO = ROOT / "killercoda" / "virtual-energy-network"
ASSETS = SCENARIO / "assets"
REQUIRED_ASSETS = {
    "helpers.py", "logical_device.py", "sensor.py", "alert_led.py",
    "supervisor.py", "lab.sh", "check.py",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def bash_blocks(text):
    fences = re.finditer(
        r"^```(?P<language>\w*)\n(?P<body>.*?)^```(?P<action>\{\{exec\}\})?[ \t]*$",
        text, re.MULTILINE | re.DOTALL,
    )
    return [match for match in fences if match["language"] == "bash"]


def validate():
    manifest = json.loads((SCENARIO / "index.json").read_text())
    details = manifest["details"]
    require(manifest["backend"]["imageid"] == "ubuntu", "Expected the Ubuntu backend")
    require(len(details["steps"]) == 10, "Expected ten lessons")
    for section in [details["intro"], *details["steps"], details["finish"]]:
        for key in ("text", "verify", "foreground", "background"):
            if key in section:
                require((SCENARIO / section[key]).is_file(), f"Missing manifest file: {section[key]}")
    delivered = set()
    for asset in details["assets"]["host01"]:
        require(asset["target"] == "/root/energy-lab/", "Unexpected asset target")
        delivered.update(path.name for path in ASSETS.glob(asset["file"]) if path.is_file())
    require(delivered == REQUIRED_ASSETS, f"Unexpected asset set: {delivered ^ REQUIRED_ASSETS}")

    for source in ROOT.rglob("*.py"):
        if ".git" not in source.parts and "dist" not in source.parts:
            ast.parse(source.read_text(), filename=str(source))
    for source in SCENARIO.rglob("*.sh"):
        subprocess.run(["bash", "-n", str(source)], check=True)
    for source in ROOT.rglob("*.md"):
        if ".git" in source.parts or "dist" in source.parts:
            continue
        for block in bash_blocks(source.read_text()):
            subprocess.run(["bash", "-n"], input=block["body"], text=True, check=True)
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", source.read_text()):
            parsed = urlsplit(link)
            if not parsed.scheme and parsed.path:
                require((source.parent / unquote(parsed.path)).exists(), f"Broken link in {source}: {link}")
    for name in ("sensor.py", "logical_device.py", "alert_led.py", "supervisor.py"):
        subprocess.run([sys.executable, str(ASSETS / name), "--help"], check=True, capture_output=True)

    walkthrough = [
        "#!/bin/bash", "set -euo pipefail", "cd /root/energy-lab",
        "[[ -f /tmp/energy-lab.ready ]] || { echo 'Run background.sh first'; exit 1; }",
        "bash lab.sh reset",
        "if python3 check.py 1; then echo 'Empty topology incorrectly passed'; exit 1; fi",
    ]
    capture = "ip netns exec lab-gw timeout 15 tcpdump -l -ni any 'tcp port 10000'"
    automated_capture = (
        "ip netns exec lab-gw timeout 5 tcpdump -l -ni any 'tcp port 10000' > run/nat-capture.log 2>&1 &\n"
        "capture_pid=$!\nsleep 1\n"
        "ip netns exec lab-sup python3 supervisor.py\n"
        "wait \"$capture_pid\" || [[ $? == 124 ]]\n"
        "cat run/nat-capture.log\n"
        "grep -q '192.0.2.10' run/nat-capture.log\n"
        "grep -q '10.20.0.11' run/nat-capture.log"
    )
    for stage, section in enumerate(details["steps"], start=1):
        wrapper = SCENARIO / section["verify"]
        require(
            wrapper.read_text() == f"#!/bin/bash\ncd /root/energy-lab && python3 check.py {stage}\n",
            f"Checkpoint wrapper does not match lesson {stage}",
        )
        blocks = [
            match["body"].rstrip("\n")
            for match in bash_blocks((SCENARIO / section["text"]).read_text())
            if match["action"]
        ]
        require(bool(blocks), f"No executable blocks in lesson {stage}")
        for block in blocks:
            subprocess.run(["bash", "-n"], input=block, text=True, check=True)
            walkthrough.append(block.replace(capture, automated_capture))
        walkthrough.append(f"bash /root/scenario-source/virtual-energy-network/checks/{stage:02}.sh")
        if stage == 2:
            walkthrough.extend([
                "ip -n lab-s1 link set eth0 down",
                "if python3 check.py 2; then echo 'Disabled cable incorrectly passed'; exit 1; fi",
                "ip -n lab-s1 link set eth0 up", "python3 check.py 2",
            ])
    walkthrough.extend([
        "ip -n lab-led1 link set eth0 down",
        "if python3 check.py 10; then echo 'Broken LED incorrectly passed'; exit 1; fi",
        "ip -n lab-led1 link set eth0 up", "bash lab.sh start 1", "sleep 2", "python3 check.py 10",
        "ip -n lab-ld1 route del default",
        "if python3 check.py 9; then echo 'Missing return route incorrectly passed'; exit 1; fi",
        "ip -n lab-ld1 route add default via 10.20.0.1", "python3 check.py 10",
        "echo 'All ten checkpoints, negative checks and repairs passed.'",
    ])
    destination = ROOT / "dist" / "walkthrough.sh"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text("\n\n".join(walkthrough) + "\n")
    subprocess.run(["bash", "-n", str(destination)], check=True)
    print("Manifest, assets, links, Python/Bash syntax, CLI entry points and lesson commands passed.")
    print(f"Generated {destination}")


if __name__ == "__main__":
    validate()
