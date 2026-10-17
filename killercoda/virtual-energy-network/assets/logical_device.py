import argparse
import json
import socket
import struct
import threading

from helpers import (
    ETHERTYPE,
    MULTICAST_GROUP,
    STATUS_PORT,
    get_interface_ipv4_address,
    send_L2_multicast,
    send_L3_multicast,
)


class IED:
    def __init__(
        self,
        name: str,
        sensor_lan_interface: str = "eth0",
        operator_lan_interface: str = "eth1",
        alert_threshold: int = 0,
    ):
        self.name = name
        self.alerted_local = False
        self.alerted_global: set[str] = set()
        self.state_lock = threading.Lock()

        self.sensor_lan_interface = sensor_lan_interface
        self.operator_lan_interface = operator_lan_interface

        self.local_alert_threshold = alert_threshold

    def listen_sensor_lan_interface(self):
        """Convert numeric measurements into local and operator-LAN alarm messages."""
        with socket.socket(
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETHERTYPE)
        ) as sock:
            sock.bind((self.sensor_lan_interface, 0))

            while True:
                frame, _ = sock.recvfrom(65535)
                if len(frame) < 14 or frame[12:14] != ETHERTYPE.to_bytes(2, "big"):
                    continue

                try:
                    payload = int(frame[14:].rstrip(b"\x00"))
                except ValueError:
                    continue
                alerted = payload >= self.local_alert_threshold
                with self.state_lock:
                    changed = alerted != self.alerted_local
                    self.alerted_local = alerted
                command = "ON" if alerted else "OFF"
                if changed:
                    print(f"Local alarm {'triggered' if alerted else 'cleared'} on {self.name}")
                send_L2_multicast(self.sensor_lan_interface, f"LOCAL_{command}".encode("ascii"))
                send_L3_multicast(self.operator_lan_interface, f"{self.name}_{command}".encode("ascii"))

    def listen_operator_lan_interface(self):
        with socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        ) as sock:
            sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1,
            )
            sock.bind(("", STATUS_PORT))

            mreq = struct.pack(
                "4s4s",
                socket.inet_aton(MULTICAST_GROUP),
                socket.inet_aton(
                    get_interface_ipv4_address(self.operator_lan_interface)
                ),
            )
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            while True:
                data, _ = sock.recvfrom(65535)
                try:
                    message = data.decode("ascii")
                except UnicodeDecodeError:
                    continue
                with self.state_lock:
                    if message.endswith("_ON"):
                        self.alerted_global.add(message[:-3])
                    elif message.endswith("_OFF"):
                        self.alerted_global.discard(message[:-4])

    def listen_tcp_requests(self):
        operator_ip = get_interface_ipv4_address(self.operator_lan_interface)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((operator_ip, STATUS_PORT))
            server_sock.listen()
            print(f"Listening for TCP requests on {operator_ip}:{STATUS_PORT}")

            while True:
                client_sock, _ = server_sock.accept()
                with client_sock:
                    client_sock.settimeout(3)
                    try:
                        with client_sock.makefile("rb") as reader:
                            request = reader.readline(1025)
                        if request == b"GET\n":
                            with self.state_lock:
                                response = {
                                    "name": self.name,
                                    "alerted_local": self.alerted_local,
                                    "alerted_global": sorted(self.alerted_global),
                                }
                        else:
                            response = {"error": "unsupported request; send GET followed by a newline"}
                        client_sock.sendall((json.dumps(response) + "\n").encode("utf-8"))
                    except OSError:
                        continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bridge sensor measurements and operator alarms")
    parser.add_argument("--name", required=True, help="ASCII name of the logical device")
    parser.add_argument(
        "-s",
        "--sensor-lan-interface",
        type=str,
        required=True,
        help="Sensor network interface for the IED",
    )
    parser.add_argument(
        "-o",
        "--operator-lan-interface",
        type=str,
        required=True,
        help="Operator network interface for the IED",
    )
    parser.add_argument(
        "-a",
        "--alert-threshold",
        type=int,
        required=True,
        help="Measurements at or above this value trigger the local alarm",
    )

    args = parser.parse_args()

    if not args.name.isascii() or not args.name.isalnum():
        parser.error("--name must contain only ASCII letters and digits")
    ied = IED(
        name=args.name,
        sensor_lan_interface=args.sensor_lan_interface,
        operator_lan_interface=args.operator_lan_interface,
        alert_threshold=args.alert_threshold,
    )

    threading.Thread(target=ied.listen_sensor_lan_interface, daemon=True).start()
    threading.Thread(target=ied.listen_operator_lan_interface, daemon=True).start()
    ied.listen_tcp_requests()
