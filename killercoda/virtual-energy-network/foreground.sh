#!/bin/bash
set -euo pipefail
for attempt in $(seq 1 300); do
    if [[ -f /tmp/energy-lab.failed ]]; then
        cat /tmp/energy-lab.failed
        exit 1
    fi
    [[ -f /tmp/energy-lab.ready ]] && break
    sleep 1
done
[[ -f /tmp/energy-lab.ready ]] || { echo 'Setup timed out. Read /tmp/energy-lab-setup.log'; exit 1; }
cd /root/energy-lab
echo 'Ready. Start with step 1; the network has not been built for you.'
