# Use the same tools for your own system

You built two sensor LANs, an operator LAN and a routed supervisor network on one Linux host. The applications used real Linux sockets and interfaces; the cables, switches and device network stacks were virtual.

| Linux object | What it represented | What it did not provide automatically |
|---|---|---|
| Network namespace | A device's interfaces, sockets, routes and firewall | A separate kernel or filesystem |
| veth pair | A two-ended Ethernet connection | A switch, address or route |
| Bridge | A shared Ethernet LAN | An IP router between subnets |
| Gateway namespace with two IP interfaces | A machine connected to two subnets | Forwarding enabled or endpoint return routes |
| DNAT plus connection tracking | A service address translated to an endpoint | An application server or complete security policy |

Explain two journeys without looking at the commands:

1. A file changes, Sensor1 publishes a measurement, LD1 raises an alarm, LED1 changes, and LD2 learns of the alarm. Which parts are new application messages rather than the original frame being forwarded?
2. The supervisor connects to `192.0.2.10`. Where does that address become `10.20.0.11`, and what route lets LD1's reply return?

## A design recipe for local integration tests

Start from your application's topology rather than from a list of Linux commands:

1. **List the roles and interfaces.** Which devices need independent addresses, port spaces or route tables? Give each one a namespace.
2. **Draw the Ethernet segments.** Use one bridge per LAN. Use veth pairs to connect namespace interfaces to bridge ports; a direct pair can join two endpoints without a switch.
3. **Add IP only where needed.** Assign addresses and routes to IP endpoints. A bridge used only for switching and an Ethernet-only sensor do not need IPv4 addresses.
4. **Choose what crosses boundaries.** Is a process creating a new message, a bridge forwarding a frame, or a router forwarding an IP packet? Configure forwarding and return routes only for the last case.
5. **Launch the software with explicit context.** `ip netns exec NAME COMMAND` gives it the intended network stack. Keep configuration files and interface arguments consistent with your drawing.
6. **Check behavior, then introduce a fault.** Observe a known input, packet path and output before changing a link or route. A topology diagram alone does not prove the system works.

The repeated pattern can represent more bays, an engineering workstation, a test client, or a simulated remote control centre. `lab.sh` supports only the two supplied bays; for another role, launch your own application explicitly with `ip netns exec`, as demonstrated for LD1.

## Continue on your own Linux machine

Use a **disposable Ubuntu 24.04 VM** for a longer session. A VM gives you the Linux networking features and root access used here; an ordinary unprivileged container may lack the permissions for namespaces, raw sockets or firewall rules. Native macOS and Windows shells do not provide these Linux interfaces.

In that VM, enter a root shell with `sudo -i`, then prepare the same lab files:

```bash
apt-get update
apt-get install -y git
git clone https://github.com/DmytroHuzz/virtual-energy-network.git /root/virtual-energy-network
mkdir -p /root/energy-lab
cp /root/virtual-energy-network/killercoda/virtual-energy-network/assets/* /root/energy-lab/
bash /root/virtual-energy-network/killercoda/virtual-energy-network/background.sh
cd /root/energy-lab
```

Follow the lesson commands in order using the Markdown files in the repository. Each lesson's native check is also available as `python3 check.py NUMBER` from `/root/energy-lab`, where NUMBER is 1–10. The maintainer guide describes the automated walkthrough if you want to validate changes to the tutorial itself.

**Optional challenge:** sketch a third bay first. It should have its own sensor bridge and a logical device on the operator LAN. Predict which existing devices should hear its operator notification and which LEDs should remain unaffected. Then implement and capture that path using explicit commands, rather than adding a second copy of the whole system to the same LAN.

These are foundations for studying substation process/station networks and SCADA communication. Real protocol semantics, redundancy, time synchronization, authentication and stale-data handling remain future exercises. Keep notes or download changes before Killercoda expires. To remove the supplied lab topology, run `bash /root/energy-lab/lab.sh reset`.
