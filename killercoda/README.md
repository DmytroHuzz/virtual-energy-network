# Linux virtual networking for energy developers

[Start the published tutorial](https://killercoda.com/dmytrohuzz/course/killercoda/virtual-energy-network) · [GitHub repository](https://github.com/DmytroHuzz/virtual-energy-network)

The scenario in `virtual-energy-network/` follows the three stages in the project README: one Sensor LAN, multiple LANs connected through logical devices, and supervisor access through a translating gateway.

Seven checkpoints cover namespaces, veth and bridges, Ethernet alarm traffic, operator IP multicast, routing, DNAT and troubleshooting. Learners type or click the actual network commands. Only package installation and file delivery are automated. Runtime helpers start/stop Python applications, change input values and query status; they do not create the topology.

## Build

From the project root, run:

```bash
python3 killercoda/build.py
```

This copies the current five Python programs into the scenario's flat `assets/` directory, generates the seven check wrappers, and writes `killercoda/virtual-energy-network.tar.gz`. Rebuild after changing the source programs. The original README remains the project brief; the scenario Markdown is the learner-facing lesson.

The sample applications needed two compatibility fixes: the LED consumes `LOCAL_ON`/`LOCAL_OFF`, and the logical device ignores nonnumeric Ethernet frames instead of terminating its sensor listener. No third-party Python dependencies are needed.

## Publish on Killercoda

Copy the entire `virtual-energy-network/` folder into the GitHub repository and branch registered in your Killercoda Creator settings. Commit and push it. If that repository has `structure.json`, add the new folder there; otherwise it may be excluded. Configure repository access and the update webhook through Killercoda if they are not already present. Do not publish the archive or build script as scenarios.

See the official [creator documentation](https://killercoda.com/creators) and [repository setup](https://killercoda.com/creators/get-started). The manifest uses the documented Ubuntu backend, asset delivery, intro setup scripts, executable Markdown blocks, and per-step verification scripts.

## Validation

Run `python3 killercoda/validate.py` on any host for manifest paths, Python/Bash syntax and Markdown command checks. Run the generated `walkthrough.sh` inside a disposable root Ubuntu environment with `iproute2`, `iptables`, `tcpdump`, `iputils-ping` and Python installed. It executes the same commands learners see, runs every checkpoint, and exercises negative checks and recovery. Never run it on the macOS host.

Verification reads real namespace/link state, running processes, LED logs, multicast-derived alarm state and TCP status responses, including both NAT mappings. It retries briefly for asynchronous publication. It does not grade prose answers, prove a learner observed every capture, or prove all forms of network isolation.

Addresses `192.0.2.0/24` simulate the WAN inside namespaces; nothing is exposed to the actual Internet. Gateway firewall changes are scoped to `lab-gw`. Reset removes the eight `lab-*` namespaces and three `br-*` bridges reserved for this lab.

The protocols are educational. This lab does not implement IEC 61850 or production SCADA, electrical protection behavior, authentication, reliable alarm delivery or time synchronization. Plan for 45–60 minutes; classroom pacing still needs a human pilot.

## Technical references

- [Linux network namespaces manual](https://www.man7.org/linux/man-pages/man7/network_namespaces.7.html)
- [IPv4 link-local multicast scope, RFC 5771 section 4](https://www.rfc-editor.org/rfc/rfc5771.html#section-4)
- [Netfilter destination NAT explanation](https://www.netfilter.org/documentation/HOWTO/NAT-HOWTO-6.html)
