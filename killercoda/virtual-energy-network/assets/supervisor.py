import argparse
import json
import socket
from pathlib import Path

from helpers import STATUS_PORT


def get_ied_status(
    operator_ip: str, port: int = STATUS_PORT, timeout: float = 3
) -> dict[str, bool | list[str] | str]:
    """Read one complete newline-delimited JSON response, even across TCP segments."""
    with socket.create_connection((operator_ip, port), timeout=timeout) as sock:
        sock.sendall(b"GET\n")
        with sock.makefile("rb") as reader:
            response = reader.readline(65537)
    if len(response) > 65536 or not response.endswith(b"\n"):
        raise ValueError("Incomplete or oversized status response")
    return json.loads(response.decode("utf-8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query logical-device status over TCP")
    parser.add_argument("--address", help="Query one address instead of the config file")
    parser.add_argument(
        "--config", type=Path,
        default=Path(__file__).resolve().with_name("logical_devices.conf"),
        help="File containing one logical-device IPv4 address per line",
    )
    args = parser.parse_args()
    try:
        addresses = [args.address] if args.address else args.config.read_text().splitlines()
        for address in addresses:
            address = address.strip()
            if address:
                print(f"Status of IED at {address}: {get_ied_status(address)}")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Status query failed: {error}\n")
