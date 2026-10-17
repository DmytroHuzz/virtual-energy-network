# Build an energy network with Linux

The grid is a network of networks. Software that monitors, controls or simulates it needs to work with those boundaries too. Let's build them on one Linux machine, starting with the tools underneath containers.

**[Start the hands-on tutorial on Killercoda](https://killercoda.com/dmytrohuzz/course/killercoda/virtual-energy-network)**

This tutorial is for software developers who are new to the energy industry. It assumes basic shell/Python skills, familiarity with IP addresses and switches, and a basic understanding of what a substation does. It teaches the Linux virtualization tools from the beginning; prior namespace, container or IEC 61850 experience is unnecessary. Allow about 45–60 minutes for the guided path, with more time for optional exploration.

## What you build

Start with a voltage sensor, a logical device and a simulated alarm LED on one LAN. Add a second bay and an operator LAN so the logical devices can share alarm information. Finally, query their status from a supervisor through a routing and NAT gateway.

| Lesson | Practice |
|---|---|
| 1. Separate the devices | Network namespaces and loopback interfaces |
| 2. Follow one cable | Create, move, rename and enable the two veth ends |
| 3. Connect the Sensor LAN | Bridge membership, Ethernet boundaries and the forwarding database |
| 4. Follow a measurement | Launch applications, read captures and trigger local alarms |
| 5. Repeat one bay | Build a second LAN without connecting the sensor segments |
| 6. Connect the operator LAN | Dual-interface devices, connected IP routes and UDP multicast |
| 7. Cable the supervisor network | Address the gateway and supervisor before routing |
| 8. Complete the round trip | Forwarding, next hops and endpoint return routes |
| 9. Publish status | Destination NAT, connection tracking and packet/counter evidence |
| 10. Diagnose faults | Broken links, stopped processes and missing routes |

Every lesson includes a goal, small command blocks, expected observations, reasoning questions and a checkpoint. Host commands and device-namespace commands are distinguished throughout. The setup supplies the programs; you build the network yourself. The closing lesson explains how to adapt the pattern to another system and run it in your own disposable Linux VM.

## Repository layout

```text
killercoda/
  README.md                      # Maintainer and validation instructions
  build.py                       # Package the scenario
  draw_topologies.py             # Render lesson-start topology snapshots
  validate.py                    # Validate source and generate a walkthrough
  virtual-energy-network/
    index.json                   # Killercoda scenario definition
    intro.md, finish.md           # Opening and closing lessons
    steps/                       # Ten focused learner exercises
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

The browser environment has an expiry timer. For an unhurried session, use the [local VM instructions](killercoda/virtual-energy-network/finish.md#continue-on-your-own-linux-machine). Going Back in the browser does not undo network changes, and repeated creation commands may report that an object already exists.

Inside that disposable environment, `bash /root/energy-lab/lab.sh reset` stops the lab applications and removes its named namespaces, bridges, logs and generated configuration. Return to lesson 1 to rebuild it. Download anything you want to keep before the environment expires.
