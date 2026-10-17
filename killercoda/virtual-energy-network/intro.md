# The grid is a network of networks

When we write software to monitor, control or simulate the grid, we also need a network of networks. We could fill a room with devices, switches and routers. Let's first build the same network boundaries inside one Linux machine.

You are a software developer joining an energy automation team. Your first task is to connect a voltage sensor, a logical device and an alarm LED. Then you will add a second sensor LAN, an operator LAN and a supervisor behind a gateway.

By the end you will be able to explain what a namespace isolates, connect devices with veth pairs and bridges, distinguish Ethernet multicast from IP multicast, trace a TCP request across a router, and inspect destination NAT.

Allow **45–60 minutes**. You need basic shell and Python knowledge; no Kubernetes or Docker experience is required. Open a second terminal tab for packet captures if useful. Commands run as root in this disposable environment.

```text
Sensor1 ─┐                              ┌─ Sensor2
         ├─ br-s1 ─ LD1 ─┐  ┌─ LD2 ─ br-s2 ┤
LED1 ────┘              br-op             └─ LED2
                          │
                    gateway (NAT)
                          │
                      supervisor
```

The Python programs are deliberately small. They exchange numeric Ethernet payloads, alarm messages over UDP multicast, and JSON over TCP. These are teaching protocols, not IEC 61850 GOOSE, Sampled Values, MMS or a production SCADA implementation. A namespace gives a separate network stack; it does not create a separate machine, filesystem or clock. The LED is a software state with a log, not physical hardware.

Setup installs tools and copies the programs into `/root/energy-lab`. It does **not** create the topology. Wait for the terminal to say **Ready**, then start.
