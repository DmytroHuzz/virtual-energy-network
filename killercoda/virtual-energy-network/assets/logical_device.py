import argparse
import json
import socket
import struct
import threading

from helpers import get_interface_ipv4_address, send_L2_multicast, send_L3_multicast


class IED:
    def __init__(
        self,
        name: str,
        sensor_lan_interface: str = "eth0",
        operator_lan_interface: str = "eth1",
        alert_threshold: int = 0,
    ):
        self.name = name
        # Track the alert status for only local subsystem (sensor LAN)
        self.alerted_local = False
        # Track the alert status for the whole system (if any sensor LAN triggers an alert)
        self.alerted_global: set[str] = set()

        self.sensor_lan_interface = sensor_lan_interface
        self.operator_lan_interface = operator_lan_interface

        self.local_alert_threshold = alert_threshold

    def listen_sensor_lan_interface(self):
        with socket.socket(
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x88B5)
        ) as sock:
            sock.bind((self.sensor_lan_interface, 0))

            while True:
                frame, _ = sock.recvfrom(65535)
                if len(frame) < 14 or frame[12:14] != b"\x88\xb5":
                    continue

                try:
                    payload = int(frame[14:].rstrip(b"\x00"))
                except ValueError:
                    continue
                if payload >= self.local_alert_threshold:
                    print(f"Trimming Alert on {self.name}")
                    send_L2_multicast(self.sensor_lan_interface, b"LOCAL_ON")
                    send_L3_multicast(
                        self.operator_lan_interface,
                        bytes(f"{self.name}_ON", "ascii"),
                    )
                    self.alerted_local = True
                else:
                    print(f"Untrimming Alert on {self.name}")
                    send_L2_multicast(self.sensor_lan_interface, b"LOCAL_OFF")
                    send_L3_multicast(
                        self.operator_lan_interface,
                        bytes(f"{self.name}_OFF", "ascii"),
                    )
                    self.alerted_local = False

    def listen_operator_lan_interface(self):
        with socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        ) as sock:
            sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1,
            )
            sock.bind(("", 10000))  # Bind to the multicast port

            mreq = struct.pack(
                "4s4s",
                socket.inet_aton("224.0.0.1"),
                socket.inet_aton(
                    get_interface_ipv4_address(self.operator_lan_interface)
                ),
            )
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            while True:
                data, _ = sock.recvfrom(65535)
                message = data.decode("ascii")
                if message.endswith("_ON"):
                    self.alerted_global.add(message[:-3])
                elif message.endswith("_OFF"):
                    self.alerted_global.discard(message[:-4])

    def listen_tcp_requests(self):
        operator_ip = get_interface_ipv4_address(self.operator_lan_interface)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((operator_ip, 10000))
            server_sock.listen()
            print(f"Listening for TCP requests on {operator_ip}:10000")

            while True:
                client_sock, _ = server_sock.accept()
                with client_sock:
                    request = client_sock.recv(1024).strip()
                    if request == b"GET":
                        response: dict[str, bool | list[str] | str] = {
                            "name": self.name,
                            "alerted_local": self.alerted_local,
                            "alerted_global": sorted(self.alerted_global),
                        }
                    else:
                        response = {"error": "unsupported request; send GET"}

                    client_sock.sendall((json.dumps(response) + "\n").encode("utf-8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IED arguments")

    def argument_value(name: str):
        def parse(value: str) -> str:
            if "=" not in value:
                return value
            key, value = value.split("=", 1)
            if key != name:
                raise argparse.ArgumentTypeError(f"expected {name}=VALUE")
            return value

        return parse

    parser.add_argument("--name", type=str, help="Name of the IED")
    parser.add_argument(
        "-s",
        "--sensor-lan-interface",
        type=str,
        help="Sensor network interface for the IED",
    )
    parser.add_argument(
        "-o",
        "--operator-lan-interface",
        type=str,
        help="Outer network interface for the IED",
    )
    parser.add_argument(
        "-a",
        "--alert_threshold",
        type=int,
        help="Initial alert threshold for the IED",
    )

    args = parser.parse_args()

    # parse ied name from argument and inner and outer interfaces
    ied_name = args.name
    inner_interface = args.sensor_lan_interface
    outer_interface = args.operator_lan_interface
    ied = IED(
        name=ied_name,
        sensor_lan_interface=inner_interface,
        operator_lan_interface=outer_interface,
        alert_threshold=args.alert_threshold,
    )

    threading.Thread(target=ied.listen_sensor_lan_interface, daemon=True).start()
    threading.Thread(target=ied.listen_operator_lan_interface, daemon=True).start()
    ied.listen_tcp_requests()
