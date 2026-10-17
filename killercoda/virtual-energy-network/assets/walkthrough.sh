#!/bin/bash

set -euo pipefail

cd /root/energy-lab

bash lab.sh reset

mkdir -p run

touch /tmp/energy-lab.ready

if python3 check.py 1; then echo 'Empty topology incorrectly passed'; exit 1; fi

cd /root/energy-lab
ip -br link
ip route

for device in lab-s1 lab-ld1 lab-led1; do
  ip netns add "$device"
  ip -n "$device" link set lo up
done
ip netns list
ip -n lab-s1 -br link

ip netns exec lab-s1 ls /root/energy-lab

python3 check.py 1

ip link add br-s1 type bridge
ip link set br-s1 up
for pair in s1:lab-s1 ld1:lab-ld1 led1:lab-led1; do
  port=${pair%%:*}
  device=${pair#*:}
  ip link add "$port-p" type veth peer name "$port-n"
  ip link set "$port-n" netns "$device"
  ip -n "$device" link set "$port-n" name eth0
  ip -n "$device" link set eth0 up
  ip link set "$port-p" master br-s1
  ip link set "$port-p" up
done
bridge link show master br-s1

ip -n lab-ld1 -br link
bridge fdb show br br-s1

python3 check.py 2

ip link add op1-p type veth peer name op1-n
ip link set op1-n netns lab-ld1
ip -n lab-ld1 link set op1-n name eth1
ip -n lab-ld1 addr add 10.20.0.11/24 dev eth1
ip -n lab-ld1 link set eth1 up
ip link set op1-p up
bash lab.sh start 1

ip netns exec lab-led1 timeout 8 tcpdump -l -eni eth0 -A -c 6 'ether proto 0x88b5'

bash lab.sh voltage 1 15
sleep 2
tail -n 4 run/led1.log
bash lab.sh status lab-ld1 10.20.0.11

bash lab.sh voltage 1 5
sleep 2
tail -n 2 run/led1.log
bash lab.sh voltage 1 15

python3 check.py 3

for device in lab-s2 lab-ld2 lab-led2; do
  ip netns add "$device"
  ip -n "$device" link set lo up
done
ip link add br-s2 type bridge
ip link set br-s2 up
for pair in s2:lab-s2 ld2:lab-ld2 led2:lab-led2; do
  port=${pair%%:*}
  device=${pair#*:}
  ip link add "$port-p" type veth peer name "$port-n"
  ip link set "$port-n" netns "$device"
  ip -n "$device" link set "$port-n" name eth0
  ip -n "$device" link set eth0 up
  ip link set "$port-p" master br-s2
  ip link set "$port-p" up
done
ip link add br-op type bridge
ip link set br-op up
ip link set op1-p master br-op
ip link add op2-p type veth peer name op2-n
ip link set op2-n netns lab-ld2
ip -n lab-ld2 link set op2-n name eth1
ip -n lab-ld2 addr add 10.20.0.12/24 dev eth1
ip -n lab-ld2 link set eth1 up
ip link set op2-p master br-op
ip link set op2-p up
bash lab.sh start 2
sleep 2
bash lab.sh status lab-ld2 10.20.0.12

ip netns exec lab-ld2 timeout 8 tcpdump -l -ni eth1 -A -c 4 'udp port 10000'

bash lab.sh voltage 2 15
sleep 2
bash lab.sh status lab-ld1 10.20.0.11
tail -n 2 run/led2.log
bash lab.sh voltage 2 5
sleep 2
bash lab.sh status lab-ld2 10.20.0.12

python3 check.py 4

for device in lab-gw lab-sup; do
  ip netns add "$device"
  ip -n "$device" link set lo up
done
ip link add gw-p type veth peer name gw-n
ip link set gw-n netns lab-gw
ip -n lab-gw link set gw-n name eth0
ip -n lab-gw addr add 10.20.0.1/24 dev eth0
ip -n lab-gw link set eth0 up
ip link set gw-p master br-op
ip link set gw-p up
ip link add wan-g type veth peer name wan-s
ip link set wan-g netns lab-gw
ip link set wan-s netns lab-sup
ip -n lab-gw link set wan-g name eth1
ip -n lab-sup link set wan-s name eth0
ip -n lab-gw addr add 192.0.2.1/24 dev eth1
ip -n lab-sup addr add 192.0.2.2/24 dev eth0
ip -n lab-gw link set eth1 up
ip -n lab-sup link set eth0 up

ip netns exec lab-gw sysctl -w net.ipv4.ip_forward=1
ip -n lab-sup route add 10.20.0.0/24 via 192.0.2.1
ip -n lab-ld1 route add default via 10.20.0.1
ip -n lab-ld2 route add default via 10.20.0.1
ip -n lab-sup route get 10.20.0.11
bash lab.sh status lab-sup 10.20.0.11
bash lab.sh status lab-sup 10.20.0.12

printf '10.20.0.11\n10.20.0.12\n' > logical_devices.conf
ip netns exec lab-sup python3 superviser.py

python3 check.py 5

ip -n lab-gw addr add 192.0.2.10/24 dev eth1
ip -n lab-gw addr add 192.0.2.11/24 dev eth1
ip netns exec lab-gw iptables -t nat -A PREROUTING -i eth1 -d 192.0.2.10 -p tcp --dport 10000 -j DNAT --to-destination 10.20.0.11:10000
ip netns exec lab-gw iptables -t nat -A PREROUTING -i eth1 -d 192.0.2.11 -p tcp --dport 10000 -j DNAT --to-destination 10.20.0.12:10000
ip netns exec lab-gw iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
ip netns exec lab-gw iptables -A FORWARD -i eth1 -o eth0 -d 10.20.0.0/24 -p tcp --dport 10000 -j ACCEPT
ip netns exec lab-gw iptables -P FORWARD DROP
printf '192.0.2.10\n192.0.2.11\n' > logical_devices.conf
ip netns exec lab-sup python3 superviser.py

ip netns exec lab-gw timeout 3 tcpdump -l -ni any 'tcp port 10000' || [[ $? == 124 ]]

ip netns exec lab-gw iptables -t nat -nvL PREROUTING
ip netns exec lab-gw iptables -nvL FORWARD

python3 check.py 6

ip -n lab-led1 link set eth0 down
bash lab.sh voltage 1 5
sleep 2
bash lab.sh status lab-sup 192.0.2.10
tail -n 2 run/led1.log

ip -n lab-led1 link set eth0 up
bash lab.sh start 1
sleep 2
tail -n 2 run/led1.log
bash lab.sh voltage 1 15

ip -n lab-ld1 route del default
timeout 4 bash lab.sh status lab-sup 192.0.2.10 || echo 'Expected: no completed TCP response'
ip -n lab-ld1 route show
ip -n lab-gw route show
ip -n lab-ld1 route add default via 10.20.0.1
bash lab.sh status lab-sup 192.0.2.10

python3 check.py 7

ip -n lab-led1 link set eth0 down

if python3 check.py 7; then echo 'Broken LED incorrectly passed'; exit 1; fi

ip -n lab-led1 link set eth0 up

bash lab.sh start 1

sleep 2

python3 check.py 7

ip -n lab-ld1 route del default

if python3 check.py 6; then echo 'Missing return route incorrectly passed'; exit 1; fi

ip -n lab-ld1 route add default via 10.20.0.1

python3 check.py 7

echo 'All seven checkpoints, negative checks and repairs passed.'
