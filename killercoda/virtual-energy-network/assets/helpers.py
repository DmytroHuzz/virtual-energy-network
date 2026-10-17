import fcntl
import socket
import struct


def send_L2_multicast(interface: str, payload: bytes) -> None:

    destination = bytes.fromhex("03 00 00 00 00 01")  # Local multicast MAC
    ethertype = bytes.fromhex("88 b5")  # Experimental protocol

    with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x88B5)) as sock:
        sock.bind((interface, 0))
        source = sock.getsockname()[4]

        frame = destination + source + ethertype + payload
        frame = frame.ljust(60, b"\x00")  # Ethernet minimum, excluding FCS
        sock.send(frame)


def get_interface_ipv4_address(interface: str) -> str:
    interface_bytes = interface.encode("ascii")
    if len(interface_bytes) > 15:
        raise ValueError("Linux interface names must be at most 15 bytes")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        request = struct.pack("256s", interface_bytes)
        response = fcntl.ioctl(sock.fileno(), 0x8915, request)

    return socket.inet_ntoa(response[20:24])


def send_L3_multicast(interface: str, payload: bytes) -> None:
    multicast_group = ("224.0.0.1", 10000)  # Example multicast group and port
    interface_ip = get_interface_ipv4_address(interface)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(interface_ip),
        )
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(payload, multicast_group)
