import argparse
import time
from pathlib import Path

from helpers import send_L2_multicast


class Sensor:
    def __init__(self, name: str, source: Path, interface: str = "eth0"):
        self.name = name
        self.source = source
        self.interface = interface

    def read_value(self) -> int:
        return int(self.source.read_text().strip())

    def send_value(self, value: int) -> None:
        payload = str(value).encode()
        send_L2_multicast(self.interface, payload)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish a sensor value once per second")
    parser.add_argument("name", type=str, help="Name of the sensor")
    parser.add_argument("source", type=Path, help="Source path of the sensor")
    parser.add_argument(
        "-s",
        "--sensor-lan-interface",
        type=str,
        default="eth0",
        help="Network interface for sending sensor values",
    )
    args = parser.parse_args()

    sensor = Sensor(
        name=args.name,
        source=args.source,
        interface=args.sensor_lan_interface,
    )
    print(f"Sensor created: {sensor.name} with source {sensor.source}")
    value = sensor.read_value()
    while True:
        previous_value = value
        value = sensor.read_value()
        if value != previous_value:
            print(f"Sensor value changed: {previous_value} -> {value}")
        sensor.send_value(value)
        time.sleep(1)
