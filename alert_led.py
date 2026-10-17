import argparse
import socket


class LED:
    def __init__(self, name: str, interface: str):
        self.state = False
        self.name = name
        self.interface = interface

    def turn_on(self):
        self.state = True

    def turn_off(self):
        self.state = False

    def is_on(self):
        return self.state

    def listen_command(self):
        # Listen for L2 multicast commands on the specified interface and update the LED state accordingly

        with socket.socket(
            socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x88B5)
        ) as sock:
            sock.bind((self.interface, 0))

            while True:
                frame, _ = sock.recvfrom(65535)
                if len(frame) < 14 or frame[12:14] != b"\x88\xb5":
                    continue

                payload = frame[14:].rstrip(b"\x00")
                if payload == b"LOCAL_ON":
                    print(f"Turning LED on {self.name}")
                    self.turn_on()
                elif payload == b"LOCAL_OFF":
                    print(f"Turning LED off {self.name}")
                    self.turn_off()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LED arguments")
    parser.add_argument("name", type=str, help="Name of the LED")
    parser.add_argument("interface", type=str, help="Network interface for the LED")
    args = parser.parse_args()

    led = LED(name=args.name, interface=args.interface)
    led.listen_command()
