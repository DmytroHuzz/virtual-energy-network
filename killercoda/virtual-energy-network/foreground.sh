#!/bin/bash
while [[ ! -f /tmp/energy-lab.ready ]]; do
    if [[ -f /tmp/energy-lab.failed ]]; then
        cat /tmp/energy-lab.failed
        exit 1
    fi
    sleep 1
done
cd /root/energy-lab
echo 'Ready. Start with step 1; the network has not been built for you.'
