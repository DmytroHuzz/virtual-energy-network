#!/bin/bash
set -euo pipefail
trap 'echo "Setup failed. Read /tmp/energy-lab-setup.log" > /tmp/energy-lab.failed' ERR
exec > /tmp/energy-lab-setup.log 2>&1
for attempt in $(seq 1 60); do
    [[ -f /root/energy-lab/lab.sh && -f /root/energy-lab/logical_device.py ]] && break
    sleep 1
done
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq iproute2 iptables tcpdump python3 iputils-ping
chmod +x /root/energy-lab/*.sh
mkdir -p /root/energy-lab/run
printf '5\n' > /root/energy-lab/run/voltage1
printf '5\n' > /root/energy-lab/run/voltage2
touch /tmp/energy-lab.ready
