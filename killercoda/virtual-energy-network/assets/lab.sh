#!/bin/bash
set -euo pipefail
LAB=$(cd "$(dirname "$0")" && pwd)
cd "$LAB"
mkdir -p "$LAB/run"

start_process() {
    local namespace=$1 name=$2 script=$3
    shift 3
    if [[ -f "$LAB/run/$name.pid" ]] &&
        kill -0 "$(cat "$LAB/run/$name.pid")" 2>/dev/null &&
        [[ $(ip netns identify "$(cat "$LAB/run/$name.pid")" 2>/dev/null) == "$namespace" ]]; then
        echo "$name is already running"
        return
    fi
    ip netns exec "$namespace" python3 -u "$LAB/$script" "$@" > "$LAB/run/$name.log" 2>&1 &
    echo $! > "$LAB/run/$name.pid"
}

case "${1:-help}" in
    start)
        bay=${2:?Supply bay 1 or 2}
        [[ "$bay" == 1 || "$bay" == 2 ]]
        [[ -f "$LAB/run/voltage$bay" ]] || printf '5\n' > "$LAB/run/voltage$bay"
        start_process "lab-ld$bay" "ld$bay" logical_device.py --name "LD$bay" -s eth0 -o eth1 -a 10
        start_process "lab-led$bay" "led$bay" alert_led.py "LED$bay" eth0
        start_process "lab-s$bay" "sensor$bay" sensor.py "S$bay" "$LAB/run/voltage$bay" -s eth0
        ;;
    voltage)
        bay=${2:?Supply bay 1 or 2}
        [[ "$bay" == 1 || "$bay" == 2 ]]
        value=${3:?Supply an integer}
        [[ "$value" =~ ^[0-9]+$ ]]
        printf '%s\n' "$value" > "$LAB/run/voltage$bay.tmp"
        mv "$LAB/run/voltage$bay.tmp" "$LAB/run/voltage$bay"
        ;;
    status)
        namespace=${2:?Supply namespace}
        address=${3:?Supply IP address}
        ip netns exec "$namespace" python3 "$LAB/supervisor.py" --address "$address"
        ;;
    stop)
        for namespace in lab-s1 lab-led1 lab-ld1 lab-s2 lab-led2 lab-ld2; do
            ip netns pids "$namespace" 2>/dev/null | xargs -r kill || true
        done
        rm -f "$LAB"/run/*.pid
        ;;
    reset)
        bash "$LAB/lab.sh" stop
        for namespace in lab-s1 lab-led1 lab-ld1 lab-s2 lab-led2 lab-ld2 lab-gw lab-sup; do
            ip netns del "$namespace" 2>/dev/null || true
        done
        for bridge in br-s1 br-s2 br-op; do
            ip link del "$bridge" 2>/dev/null || true
        done
        rm -f "$LAB"/run/*.log "$LAB"/run/*.json
        rm -f "$LAB/logical_devices.conf"
        printf '5\n' > "$LAB/run/voltage1"
        printf '5\n' > "$LAB/run/voltage2"
        ;;
    help) echo 'Usage: bash lab.sh start 1|2 | voltage 1|2 VALUE | status NAMESPACE IP | stop | reset' ;;
    *) echo 'Unknown command. Run bash lab.sh help.' >&2; exit 1 ;;
esac
