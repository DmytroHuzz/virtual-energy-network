# Build a small system before a whole substation

You know how IP addresses, switches and routers work. Now you need several devices and LANs to test energy software, but you have one Linux machine. How can each program have its own interfaces and routes? Where do the cables and switches come from?

We will build those boundaries with **network namespaces**, **veth pairs** and **Linux bridges**. These are useful building blocks beneath container networking, and you can use them directly for local integration tests.

Our example grows in three stages:

1. A sensor publishes measurements; a logical device compares them with a threshold and commands an alarm LED on the same LAN.
2. A second bay gets its own Sensor LAN. The logical devices exchange alarm notifications on an operator LAN.
3. A supervisor queries their status from another IP network through a routing and NAT gateway.

```text
Sensor1 ─┐
         br-s1 ─ LD1 ─┐
LED1 ────┘           │
                   br-op ─ gateway ─ supervisor
Sensor2 ─┐           │
         br-s2 ─ LD2 ─┘
LED2 ────┘
```

Here a **bay** means one repeated sensor/device/indicator subsystem. **LD1** and **LD2** are small Python applications playing the role of an intelligent device; their names do not imply a complete IEC 61850 logical-device model. A logical device has two interfaces because it participates in two LANs. Its application translates information between them; it does not automatically act as an IP router.

## How to use the lesson

Allow about **45–60 minutes for the guided path**, with more time for optional exploration. Watch Killercoda's expiry timer. A fresh session starts with an empty topology, so keep notes if you plan to continue later or use your own Linux VM.

For an unhurried local session, the [closing lesson's VM setup](https://github.com/DmytroHuzz/virtual-energy-network/blob/main/killercoda/virtual-energy-network/finish.md#continue-on-your-own-linux-machine) prepares the same files on Ubuntu so you can follow these commands without the browser timer.

- Wait for **Ready** in the terminal. Setup installs tools and puts the programs in `/root/energy-lab`; you create all network connections.
- Run blocks in order, once. Click a runnable block or type its commands. Do not type the shell prompt shown in the terminal.
- Read the expected result before moving on. Interface indices, MAC addresses and timestamps will vary.
- Use **Check** at the end of each lesson. A failed check gives a hint; it does not repair the network. **Back** changes the lesson page and does not undo commands.

All commands run as root in the **host network namespace** unless they explicitly use `ip -n NAME` or `ip netns exec NAME ...`. In this tutorial, *host* means the disposable Ubuntu machine inside Killercoda, not your laptop. Those prefixes affect that command only; your shell stays in the host namespace.

If a command reports **File exists**, you may have already run that creation command. Inspect the named object rather than repeatedly running the whole block. If a named namespace or interface is missing, return to the block that creates it. For a complete restart after setup, `bash /root/energy-lab/lab.sh reset` clears the lab so you can begin again at lesson 1.

The simulated sensor values are integers from files, without calibrated electrical units. The LED is software with a state log. The protocols are intentionally small teaching formats, not IEC 61850 GOOSE, Sampled Values, MMS or a production SCADA service. This lets you focus on the network boundaries before learning real protocol behavior.

By the end, you should be able to sketch a topology, decide which Linux objects represent it, launch existing software inside that topology, and find where a packet stops.
