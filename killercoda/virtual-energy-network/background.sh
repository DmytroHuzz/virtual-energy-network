#!/bin/bash
set -euo pipefail
trap 'if [[ $? != 0 ]]; then echo "Setup failed. Read /tmp/energy-lab-setup.log" > /tmp/energy-lab.failed; fi' EXIT
exec > /tmp/energy-lab-setup.log 2>&1
rm -f /tmp/energy-lab.ready /tmp/energy-lab.failed
files=(lab.sh check.py helpers.py logical_device.py sensor.py alert_led.py supervisor.py)
for attempt in $(seq 1 60); do
    missing=0
    for file in "${files[@]}"; do
        [[ -f /root/energy-lab/$file ]] || missing=1
    done
    [[ "$missing" == 0 ]] && break
    sleep 1
done
[[ "$missing" == 0 ]] || { echo 'Timed out waiting for scenario assets'; exit 1; }
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq iproute2 iptables tcpdump python3
chmod +x /root/energy-lab/*.sh
mkdir -p /root/energy-lab/run
printf '5\n' > /root/energy-lab/run/voltage1
printf '5\n' > /root/energy-lab/run/voltage2
touch /tmp/energy-lab.ready
