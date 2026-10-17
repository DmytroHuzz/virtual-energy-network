==============================
Intro
==============================
As we already know the grid is a network of networks. 

Therefore, when we work with software that need to follow the structure of the system: control, operate, protect, simulate,
etc, we need to work with network of networks as well. And our system becames the system of systems. 
In order to be able to recreate that topology we can use hardware and rebuild it as connections of servers, nodes, LANs, switches and routers.
But there is another way to achive the same. We can use only one machine and thanksfully to virtualisations tools of Linux we can reconstract the complicated network locally. We can use docker for that, but I would really like to show the firts principles that lays behind all virtualisation tools on Linux
Let's go!

==============================
THE LOCAL NETWORK
==============================

Let's build a system.
One LAN (let's call it Sensor LAN) in which we have:
1) One source of voltage and a SENSOR that measures voltage every second and send data into local network as l2 multicast message. 
2) One Logical device that listens the local network and moment when SENSOR's data reaches some threshold triggers allert and sends a multicast message into the LAN that alert is triggered. 
3) One LED with microcontroller that listens to the LAN and moment when alert is triggered it turns on. 

We can easily simulate this system on one PC by using simple scripts. 

==============================
Multiple LOCAL networks
==============================
Now let's make it more complicated. 

We have multiple LANs like this. More than that. We have one additional LAN (Operator LAN) where
1) Each Logical device of all local networks is connected to with another network interface. 
2) Each time when the Logica device triggers alert in the local network it also sends L3 multicast message that notify about it.
3) All Logical devices in the LAN receive that information and save it Locally

Now for that setup we need multiple devices with multiple interfaces and multiple switches.
But now we can look into how we can make it locally by using network namespaces and veth.


==============================
Befind the NAT
==============================

Now let's make it more difficult. Let's add one more requirements. 
The superviser should be able to connect to our system from global LAN by using public IPs and get the status of each device. 
therefore now we need to add a gateway that would translate global IPs into local once and redirect requests to defined Logical devices. 
In the physical word we would need a router with NAT settings. 
But let's see how we can use iptables and virtual bridge for that. 


The end topology:
![alt text](<network tompology-1.jpg>)