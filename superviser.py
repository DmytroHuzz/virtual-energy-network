# Superviser script for the IED system
import json
import socket


def get_ied_status(
    operator_ip: str, port: int = 10000
) -> dict[str, bool | list[str] | str]:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((operator_ip, port))
        sock.sendall(b"GET")
        response = sock.recv(1024)
    return json.loads(response.decode("utf-8"))


if __name__ == "__main__":
    # Read ips of logical devices from configuration file
    with open("logical_devices.conf", "r") as f:
        logical_devices = [line.strip() for line in f if line.strip()]
        # logical_devices is now populated from the configuration file
        for device_ip in logical_devices:
            status = get_ied_status(device_ip)
            print(f"Status of IED at {device_ip}: {status}")
