# You built a network of networks

You used one Linux machine to represent two sensor LANs, two logical devices, an operator LAN, a router and a remote supervisor.

You can now connect these tools to physical concepts:

| Linux primitive | Concept in this exercise |
|---|---|
| Network namespace | A device's network stack |
| veth pair | An Ethernet cable |
| Bridge | An Ethernet switch |
| Two gateway interfaces plus routes and forwarding | A router |
| DNAT and connection tracking | A published address with translated traffic and replies |

Before moving on, explain the path of one sensor value and one supervisor request without reading the commands. Why does a remote bay alarm appear in LD2's global state without changing LED2? Why does a missing return route break the supervisor request?

This is a foundation for studying substation process/station networks and SCADA communication. The example roles are analogies, not a standards-compliant substation model. Next lessons could replace the teaching payloads with real protocol tooling, add VLANs and redundant paths, introduce time synchronisation, or explore stale data and lost messages.

The environment is temporary. Download any notes or changes before it expires. Run `bash /root/energy-lab/lab.sh reset` if you want to remove the lab topology now.
