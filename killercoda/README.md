# Maintain the energy networking tutorial

[Live tutorial](https://killercoda.com/dmytrohuzz/course/killercoda/virtual-energy-network) · [Repository](https://github.com/DmytroHuzz/virtual-energy-network)

## Edit the source

Edit the programs directly in `virtual-energy-network/assets/`. They are both the application source and the files delivered to learners; there is no second copy to synchronize. Edit lessons in `steps/` and checkpoint entry points in `checks/`. Keep command examples, filenames and the manifest consistent.

The supported runtime is disposable Ubuntu 24.04 with root access. The applications require Python 3.10 or later and use only its standard library. Raw Ethernet sockets and namespace operations require Linux and elevated privileges. Source validation and packaging also work on macOS.

## Validate and package

From the repository root:

```bash
python3 killercoda/validate.py
python3 killercoda/build.py
```

Validation checks manifest references, asset delivery, local Markdown links, Python and Bash syntax, CLI entry points and the seven checkpoint wrappers. It extracts the executable lesson blocks into `dist/walkthrough.sh`. Packaging runs validation and creates `dist/virtual-energy-network.tar.gz`. Generated outputs and runtime files are ignored by Git.

GitHub Actions runs static validation on pushes and pull requests. Static checks cannot prove packet forwarding; run the walkthrough after changing programs, topology commands or checkpoints.

## Run the full walkthrough

Use a fresh Ubuntu VM or Killercoda playground with root access. The walkthrough resets the lab's reserved namespaces and bridges, so use a disposable environment.

Copy the generated archive and `dist/walkthrough.sh` into that environment, then run:

```bash
mkdir -p /root/scenario-source /root/energy-lab
tar -xzf virtual-energy-network.tar.gz -C /root/scenario-source
cp /root/scenario-source/virtual-energy-network/assets/* /root/energy-lab/
bash /root/scenario-source/virtual-energy-network/background.sh
bash walkthrough.sh
```

The walkthrough executes learner commands and runs every checkpoint. It also verifies that an empty topology, a disconnected LED interface and a missing return route fail, then restores the network. Packet captures are bounded; the NAT capture runs alongside a supervisor query so both interfaces show traffic.

Checkpoints inspect links, processes, LED logs, multicast-derived alarm state, TCP responses and NAT rules. They retry briefly for sensor publication. They do not grade prose answers or prove every isolation property. After testing, use `bash /root/energy-lab/lab.sh reset` to leave a clean environment.

Reserved names: `lab-s1`, `lab-s2`, `lab-ld1`, `lab-ld2`, `lab-led1`, `lab-led2`, `lab-gw`, `lab-sup`, `br-s1`, `br-s2` and `br-op`. Firewall changes occur inside `lab-gw`. The WAN subnet `192.0.2.0/24` is simulated inside the lab; nothing is published to the real Internet.

## Publish changes

The repository's `main` branch is connected to Killercoda profile `dmytrohuzz`. A read-only deploy key allows cloning, and an authenticated push webhook triggers updates. Keep credentials in service settings, never in the repository.

After validation and runtime checks, commit and push. Check sync status in Killercoda Creator settings, then launch a fresh scenario and verify assets, the Ready message, executable Markdown and a native Check button. Running environments do not automatically receive changed files. Classroom pacing and learner comprehension still need a human pilot.

For another creator profile, register your own repository and branch, add its read-only deploy key, and configure the webhook. Preserve the scenario folder path to keep lesson links working. If you add a root `structure.json`, include the scenario there.

## Protocols and application behavior

| Network | Format | Destination |
|---|---|---|
| Sensor LAN | Numeric ASCII value or `LOCAL_ON` / `LOCAL_OFF` in an experimental Ethernet frame | MAC `03:00:00:00:00:01`, EtherType `0x88b5` |
| Operator LAN | `<device>_ON` / `<device>_OFF` over UDP | `224.0.0.1:10000`, TTL 1 |
| Supervisor | `GET` plus a newline; one newline-delimited JSON response | Logical-device IPv4 address, TCP port 10000 |

The sensor publishes once per second. Measurements at or above the threshold trigger an alarm. Logical devices repeatedly publish their local state and track received operator alarms separately; a remote alarm does not drive the local LED. Status queries use timeouts and handle TCP segmentation. Shared logical-device state is protected by a lock.

The raw-socket listeners can exit when their interface goes down. Lesson 7 demonstrates that repairing a link may also require restarting an application. The example has no reliable delivery, state expiry or listener-health reporting; those are useful follow-up exercises.

## References

- [Killercoda creator documentation](https://killercoda.com/creators)
- [Killercoda repository setup](https://killercoda.com/creators/get-started)
- [Linux network namespaces manual](https://www.man7.org/linux/man-pages/man7/network_namespaces.7.html)
- [Link-local IPv4 multicast scope, RFC 5771 section 4](https://www.rfc-editor.org/rfc/rfc5771.html#section-4)
- [Netfilter destination NAT explanation](https://www.netfilter.org/documentation/HOWTO/NAT-HOWTO-6.html)
