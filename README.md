# Build an energy network with Linux

The grid is a network of networks. Software that monitors, controls or simulates it needs to work with those boundaries too. Let's build them on one Linux machine, starting with the tools underneath containers.

**[Start the hands-on tutorial on Killercoda](https://killercoda.com/dmytrohuzz/course/killercoda/virtual-energy-network)**

This tutorial is for software developers working in the energy industry. You need basic shell and Python knowledge. Allow 45–60 minutes; the browser environment supplies Ubuntu, root access and the required tools.

## What you build

Start with a voltage sensor, a logical device and a simulated alarm LED on one LAN. Add a second bay and an operator LAN so the logical devices can share alarm information. Finally, query their status from a supervisor through a routing and NAT gateway.

| Lesson | Practice |
|---|---|
| 1. Separate the devices | Network namespaces and loopback interfaces |
| 2. Connect the Sensor LAN | veth pairs and a Linux bridge |
| 3. Follow a measurement | Ethernet multicast, packet capture and local alarms |
| 4. Add another bay | Separate LANs and UDP multicast on the operator LAN |
| 5. Connect a supervisor | IPv4 addressing, forwarding and return routes |
| 6. Publish status | Destination NAT, connection tracking and firewall counters |
| 7. Diagnose faults | Broken links, stopped processes and missing routes |

Every lesson includes runnable commands, questions and a checkpoint. The setup supplies the programs; you build the network yourself.

## Repository layout

```text
killercoda/
  README.md                      # Maintainer and validation instructions
  build.py                       # Package the scenario
  validate.py                    # Validate source and generate a walkthrough
  virtual-energy-network/
    index.json                   # Killercoda scenario definition
    intro.md, finish.md           # Opening and closing lessons
    steps/                       # Seven learner exercises
    checks/                      # Native checkpoint entry points
    background.sh, foreground.sh # Tool installation and readiness
    assets/                      # The single source of truth for lab programs
```

The five applications live only in `assets/`: `sensor.py`, `logical_device.py`, `alert_led.py`, `supervisor.py` and `helpers.py`. `lab.sh` manages their processes and input values; `check.py` verifies the exercises. Generated archives and historical copies are excluded from the published source tree. See the [maintainer guide](killercoda/README.md) for editing, validation and publication.

## What the example represents

The device roles introduce ideas used in substation and SCADA networks. The programs exchange numeric Ethernet payloads, UDP alarm messages and newline-delimited JSON status over TCP. They do not implement IEC 61850 GOOSE, Sampled Values, MMS or a production SCADA service.

Sensor values are integers read from files, without calibrated electrical units. The LED is an in-memory state reported in a log. Namespaces share the host's kernel and filesystem. Alarm delivery has no authentication, persistence or expiry; a stopped sender can leave stale state. These choices keep packet flow and network boundaries visible while you learn the tools.

## Run and reset

Use the [Killercoda tutorial](https://killercoda.com/dmytrohuzz/course/killercoda/virtual-energy-network) for the supported environment. Its setup installs tools and opens `/root/energy-lab`. Follow lessons in order and wait for **Ready** before running commands.

Inside that disposable environment, `bash /root/energy-lab/lab.sh reset` stops the lab applications and removes its named namespaces, bridges, logs and generated configuration. Return to lesson 1 to rebuild it. Download anything you want to keep before the environment expires.
