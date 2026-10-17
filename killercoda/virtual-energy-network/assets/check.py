import json
import pathlib
import subprocess
import sys
import time


LAB = pathlib.Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def command(*arguments):
    result = subprocess.run(arguments, text=True, capture_output=True, timeout=8)
    if result.returncode:
        error = result.stderr.strip().splitlines()
        raise AssertionError(error[-1] if error else f"Command failed: {' '.join(arguments)}")
    return result.stdout


def interface(namespace, name):
    prefix = ["ip", "-n", namespace] if namespace else ["ip"]
    return json.loads(command(*prefix, "-j", "link", "show", "dev", name))[0]


def up(namespace, name):
    require("UP" in interface(namespace, name)["flags"], f"Bring {namespace or 'host'}/{name} up")


def attached(name, bridge):
    require(interface(None, name).get("master") == bridge, f"Attach {name} to {bridge}")
    up(None, name)


def status(namespace, address):
    script = (
        "import json,sys; "
        f"sys.path.insert(0,{str(LAB)!r}); "
        "from supervisor import get_ied_status; "
        f"print(json.dumps(get_ied_status({address!r},timeout=2)))"
    )
    return json.loads(command("ip", "netns", "exec", namespace, "python3", "-c", script))


def process(namespace, script):
    pids = command("ip", "netns", "pids", namespace).split()
    require(any(
        script.encode() in pathlib.Path(f"/proc/{pid}/cmdline").read_bytes()
        for pid in pids
        if pathlib.Path(f"/proc/{pid}/cmdline").exists()
    ), f"Start {script} inside {namespace}")


def led(bay, expected):
    process(f"lab-led{bay}", "alert_led.py")
    lines = (LAB / "run" / f"led{bay}.log").read_text().splitlines()
    require(
        lines and f"Turning LED {expected} LED{bay}" == lines[-1],
        f"LED{bay} should be {expected}",
    )


def verify(stage):
    require(pathlib.Path("/tmp/energy-lab.ready").exists(), "Wait for setup to finish")
    for namespace in ("lab-s1", "lab-ld1", "lab-led1"):
        up(namespace, "lo")
    if stage < 2:
        return
    up(None, "br-s1")
    for port in ("s1-p", "ld1-p", "led1-p"):
        attached(port, "br-s1")
    for namespace in ("lab-s1", "lab-ld1", "lab-led1"):
        up(namespace, "eth0")
    if stage < 3:
        return
    process("lab-ld1", "logical_device.py")
    process("lab-s1", "sensor.py")
    first = status("lab-ld1", "10.20.0.11")
    require(first["alerted_local"] is True, "Set bay 1 voltage to 15")
    led(1, "on")
    if stage < 4:
        return
    for bridge in ("br-s2", "br-op"):
        up(None, bridge)
    for port in ("s2-p", "ld2-p", "led2-p"):
        attached(port, "br-s2")
    for port in ("op1-p", "op2-p"):
        attached(port, "br-op")
    for namespace in ("lab-s2", "lab-ld2", "lab-led2"):
        up(namespace, "eth0")
    up("lab-ld1", "eth1")
    up("lab-ld2", "eth1")
    process("lab-s2", "sensor.py")
    second = status("lab-ld2", "10.20.0.12")
    require(second["alerted_local"] is False, "Leave bay 2 voltage at 5")
    require("LD1" in second["alerted_global"], "LD2 has not received LD1 multicast")
    require("LD2" not in first["alerted_global"], "Clear bay 2's alarm")
    led(2, "off")
    if stage < 5:
        return
    for namespace in ("lab-gw", "lab-sup"):
        up(namespace, "lo")
        up(namespace, "eth0")
    up("lab-gw", "eth1")
    require(
        command("ip", "netns", "exec", "lab-gw", "sysctl", "-n", "net.ipv4.ip_forward").strip() == "1",
        "Enable forwarding inside lab-gw",
    )
    require(status("lab-sup", "10.20.0.11")["name"] == "LD1", "Private address should reach LD1")
    require(status("lab-sup", "10.20.0.12")["name"] == "LD2", "Private address should reach LD2")
    if stage < 6:
        return
    require(status("lab-sup", "192.0.2.10")["name"] == "LD1", "First WAN alias should reach LD1")
    require(status("lab-sup", "192.0.2.11")["name"] == "LD2", "Second WAN alias should reach LD2")
    for public, private in (("192.0.2.10", "10.20.0.11"), ("192.0.2.11", "10.20.0.12")):
        command("ip", "netns", "exec", "lab-gw", "iptables", "-t", "nat", "-C", "PREROUTING", "-i", "eth1", "-d", public, "-p", "tcp", "--dport", "10000", "-j", "DNAT", "--to-destination", f"{private}:10000")
    if stage >= 7:
        up("lab-led1", "eth0")
        require(
            "LD1" in status("lab-sup", "192.0.2.11")["alerted_global"],
            "LD2 should report LD1's alarm through NAT",
        )


if __name__ == "__main__":
    stage = int(sys.argv[1])
    if stage not in range(1, 8):
        sys.exit("Expected a step number from 1 to 7")
    for attempt in range(5):
        try:
            verify(stage)
            print(f"Step {stage} passed")
            sys.exit(0)
        except (AssertionError, OSError, ValueError, subprocess.SubprocessError) as error:
            failure = str(error)
            time.sleep(1)
    print(f"Not yet: {failure}")
    sys.exit(1)
