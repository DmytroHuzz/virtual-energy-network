import fcntl
import socket
import struct


ETHERTYPE = 0x88B5
MULTICAST_MAC = bytes.fromhex("03 00 00 00 00 01")
MULTICAST_GROUP = "224.0.0.1"
STATUS_PORT = 10000


def send_L2_multicast(interface: str, payload: bytes) -> None:
    """Send the lab's experimental Ethernet frame without an IP header."""
    with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETHERTYPE)) as sock:
        sock.bind((interface, 0))
        source = sock.getsockname()[4]

        frame = MULTICAST_MAC + source + ETHERTYPE.to_bytes(2, "big") + payload
        frame = frame.ljust(60, b"\x00")  # Ethernet minimum, excluding FCS
        sock.send(frame)


def get_interface_ipv4_address(interface: str) -> str:
    """Read an interface's primary IPv4 address using Linux SIOCGIFADDR."""
    interface_bytes = interface.encode("ascii")
    if len(interface_bytes) > 15:
        raise ValueError("Linux interface names must be at most 15 bytes")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        request = struct.pack("256s", interface_bytes)
        response = fcntl.ioctl(sock.fileno(), 0x8915, request)

    return socket.inet_ntoa(response[20:24])


def send_L3_multicast(interface: str, payload: bytes) -> None:
    """Publish a UDP alarm on the operator LAN's link-local all-hosts group."""
    interface_ip = get_interface_ipv4_address(interface)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(interface_ip),
        )
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        sock.sendto(payload, (MULTICAST_GROUP, STATUS_PORT))
