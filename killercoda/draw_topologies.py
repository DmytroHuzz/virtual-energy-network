"""Render the existing topology at the start of each lesson (requires Pillow).

These are authored snapshots, not runtime discovery. Keep their states aligned
with the commands in the preceding lessons. Learners and CI use the committed
PNGs; Pillow is needed only when regenerating the illustrations.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


DESTINATION = Path(__file__).resolve().parent / "virtual-energy-network" / "steps" / "images"
SCALE = 2
INK = "#173346"
MUTED = "#526879"
TEAL = "#087f83"
PALE = "#edf7f7"
BORDER = "#c9d8e0"
AMBER = "#a55c00"
WARM = "#fff4dd"
GREEN = "#236646"


class Diagram:
    def __init__(self, step, height, subtitle):
        self.height = height
        self.image = Image.new("RGB", (800 * SCALE, height * SCALE), "#ffffff")
        self.draw = ImageDraw.Draw(self.image)
        self.text(26, 20, f"START OF STEP {step:02}", size=24)
        self.text(26, 54, subtitle, size=18, color=MUTED)
        self.rectangle((14, 88, 786, height - 98), fill="#f8fbfc", outline=BORDER)
        self.step = step

    def text(self, x, y, value, size=18, color=INK, anchor=None):
        font = ImageFont.load_default(size=size * SCALE)
        position = (round(x * SCALE), round(y * SCALE))
        bounds = self.draw.textbbox(position, value, font=font, anchor=anchor)
        if bounds[0] < 0 or bounds[2] > self.image.width or bounds[3] > self.image.height:
            raise ValueError(f"Step {self.step}: text extends beyond the image: {value}")
        self.draw.text(
            position, value, font=font, fill=color, anchor=anchor,
        )

    def rectangle(self, bounds, fill="white", outline=BORDER, radius=12, width=2):
        self.draw.rounded_rectangle(
            tuple(round(v * SCALE) for v in bounds), radius=radius * SCALE,
            fill=fill, outline=outline, width=width * SCALE,
        )

    def line(self, points, color=TEAL, width=3):
        self.draw.line(
            [(round(x * SCALE), round(y * SCALE)) for x, y in points],
            fill=color, width=width * SCALE, joint="curve",
        )

    def node(self, x, y, width, lines, fill="white", outline=TEAL, height=78):
        self.rectangle((x, y, x + width, y + height), fill=fill, outline=outline)
        for index, value in enumerate(lines):
            self.text(x + width / 2, y + 15 + index * 23, value,
                      size=21 if index == 0 else 16, anchor="mt")

    def bridge(self, x, y, width, name, subnet=None):
        self.rectangle((x, y, x + width, y + 58), fill=PALE, outline=TEAL)
        self.text(x + width / 2, y + 9, name, size=21, anchor="mt")
        self.text(x + width / 2, y + 35, subnet or "Ethernet only / no IPv4", size=16, anchor="mt")

    def bay(self, number, x, y, running=False, operator=False, parked=False):
        """One bay: LD above its bridge, sensor and LED below the bridge."""
        self.rectangle((x, y, x + 370, y + 370), outline=BORDER)
        self.text(x + 14, y + 12, f"Bay {number}", size=19)
        self.text(x + 354, y + 14, "running" if running else "wired / stopped",
                  size=15, color=GREEN if running else MUTED, anchor="rt")
        center = x + 185
        self.line([(center, y + 126), (center, y + 176)])
        self.text(center + 12, y + 140, f"eth0 / ld{number}-p", size=15)
        for port_x, label in ((x + 98, f"s{number}-p"), (x + 277, f"led{number}-p")):
            self.line([(port_x, y + 234), (port_x, y + 280)])
            self.text(port_x + 10, y + 244, label, size=15)
        if parked:
            self.line([(center, y + 42), (center, y - 12)])
            self.draw.ellipse(
                ((center - 5) * SCALE, (y - 17) * SCALE,
                 (center + 5) * SCALE, (y - 7) * SCALE),
                fill="white", outline=AMBER, width=2 * SCALE,
            )
            self.text(center, y - 42, "op1-p: unattached", size=17, color=AMBER, anchor="mt")
        ld_lines = [f"LD{number}", f"lab-ld{number}"]
        if operator or parked:
            ld_lines.append(f"eth1: 10.20.0.{10 + number}")
        self.node(x + 95, y + 42, 180, ld_lines, height=84)
        self.bridge(x + 30, y + 176, 310, f"Sensor LAN {number} / br-s{number}")
        self.node(x + 18, y + 280, 160,
                  [f"Sensor{number}", f"lab-s{number} / eth0"], height=70)
        led_title = f"LED{number}"
        if running:
            led_title += " / ON" if number == 1 else " / OFF"
        self.node(x + 197, y + 280, 160,
                  [led_title, f"lab-led{number} / eth0"],
                  fill=WARM if running and number == 1 else "white", height=70)

    def operator(self, y, bay_y):
        for bridge_x, device_x in ((300, 205), (500, 595)):
            self.line([(bridge_x, y + 58), (bridge_x, bay_y + 28),
                       (device_x, bay_y + 28), (device_x, bay_y + 42)])
        self.bridge(250, y, 300, "Operator LAN / br-op", "10.20.0.0/24")

    def footer(self, first, second, warning=False):
        y = self.height - 82
        self.text(26, y, first, size=18, color=AMBER if warning else GREEN)
        self.text(26, y + 27, second, size=16, color=MUTED)
        self.text(26, y + 54, "Device boxes: namespaces   |   Bars: bridges   |   Lines: veth connections",
                  size=15, color=MUTED)

    def save(self):
        DESTINATION.mkdir(parents=True, exist_ok=True)
        self.image.save(DESTINATION / f"where-we-are-{self.step:02}.png", optimize=True)


def render():
    diagram = Diagram(1, 360, "Setup supplied the programs; the lab topology is still empty.")
    diagram.text(400, 132, "One Linux host", size=25, anchor="mt")
    diagram.text(400, 181, "No lab namespaces, cables or bridges yet", size=21, anchor="mt")
    diagram.text(400, 218, "Programs are ready in /root/energy-lab", size=18, color=MUTED, anchor="mt")
    diagram.footer("No lab network built yet.", "The host's existing access interfaces are omitted.")
    diagram.save()

    diagram = Diagram(2, 360, "Three independent network stacks exist; none has an Ethernet connection.")
    for x, role, namespace in ((34, "Sensor1", "lab-s1"), (296, "LD1", "lab-ld1"), (558, "LED1", "lab-led1")):
        diagram.node(x, 140, 208, [role, namespace, "lo UP / no Ethernet"], height=96)
    diagram.footer("3 namespaces / 0 veth pairs / 0 bridges", "The device programs have not been started.")
    diagram.save()

    diagram = Diagram(3, 520, "The sensor has one cable; its host end is not attached to a switch.")
    diagram.node(44, 136, 210, ["Sensor1", "lab-s1 / eth0"], height=86)
    diagram.line([(254, 179), (490, 179)])
    diagram.text(367, 148, "veth pair", size=18, color=TEAL, anchor="mt")
    diagram.node(490, 136, 260, ["s1-p / free end", "in the host namespace"], outline=AMBER, fill=WARM, height=86)
    diagram.node(120, 288, 220, ["LD1", "lab-ld1 / lo only"], height=78)
    diagram.node(460, 288, 220, ["LED1", "lab-led1 / lo only"], height=78)
    diagram.footer("Both veth ends are UP, but no LAN exists yet.", "LD1 and LED1 remain disconnected; the programs are stopped.", warning=True)
    diagram.save()

    diagram = Diagram(4, 580, "The first Sensor LAN is wired; its programs have not been started.")
    diagram.bay(1, 215, 96)
    diagram.footer("3 namespaces / 3 veth pairs / 1 bridge", "No operator interface exists yet; sensor-facing links have no IPv4.")
    diagram.save()

    for step in (5, 6):
        diagram = Diagram(step, 640, "Bay 1 is running; LD1's prepared operator cable still has a free host end.")
        diagram.bay(1, 20 if step == 6 else 215, 150, running=True, parked=True)
        if step == 6:
            diagram.bay(2, 410, 150)
        diagram.footer(
            "Bay 1 input: 15 / local alarm ON. " + ("Bay 2 is wired, but stopped." if step == 6 else "Bay 2 does not exist yet."),
            "op1-p is not on a bridge; " + ("no Operator LAN exists yet." if step == 6 else "there is no Operator LAN yet."),
            warning=True,
        )
        diagram.save()

    diagram = Diagram(7, 680, "Both bays run and exchange alarm notifications on the Operator LAN.")
    diagram.bay(1, 20, 194, running=True, operator=True)
    diagram.bay(2, 410, 194, running=True, operator=True)
    diagram.operator(106, 194)
    diagram.footer("Bay 1: local alarm ON / Bay 2: local alarm OFF, LD1 alarm known.",
                   "6 namespaces / 3 bridges. No gateway or supervisor exists yet.")
    diagram.save()

    for step in (8, 9, 10):
        diagram = Diagram(step, 800, {
            8: "All links and addresses exist; the supervisor cannot yet reach the devices.",
            9: "Routing works in both directions; no NAT aliases or rules exist yet.",
            10: "The supervisor reaches both status services through gateway-owned aliases.",
        }[step])
        diagram.line([(310, 146), (490, 146)])
        diagram.text(400, 103, "Direct WAN veth", size=16, anchor="mt")
        diagram.text(400, 124, "192.0.2.0/24", size=15, color=MUTED, anchor="mt")
        diagram.line([(180, 201), (180, 214), (400, 214), (400, 240)])
        diagram.node(50, 96, 260,
                     ["Gateway / lab-gw", "eth0: 10.20.0.1/24", "eth1: 192.0.2.1/24"], height=105)
        diagram.node(490, 96, 260,
                     ["Supervisor", "lab-sup", "eth0: 192.0.2.2/24"], height=105)
        diagram.bay(1, 20, 310, running=True, operator=True)
        diagram.bay(2, 410, 310, running=True, operator=True)
        diagram.operator(240, 310)
        if step == 8:
            diagram.footer("Cabled only: gateway forwarding and endpoint routes are not set.",
                           "The Operator LAN works; the end-to-end TCP path is incomplete.", warning=True)
        elif step == 9:
            diagram.footer("Forwarding ON / supervisor route and LD return routes configured.",
                           "Supervisor queries 10.20.0.11 and 10.20.0.12 directly; no NAT yet.")
        else:
            diagram.footer("DNAT: WAN .10 -> 10.20.0.11   |   WAN .11 -> 10.20.0.12",
                           "Aliases are on 192.0.2.0/24. LD return routes remain; supervisor's private route is removed.")
        diagram.save()


if __name__ == "__main__":
    render()
    print(f"Rendered ten lesson-start diagrams in {DESTINATION}")
