import json
import pathlib
import subprocess
import sys
import tarfile


ROOT = pathlib.Path(__file__).resolve().parent.parent
SCENARIO = ROOT / "killercoda" / "virtual-energy-network"


def main():
    subprocess.run([sys.executable, str(ROOT / "killercoda" / "validate.py")], check=True)
    details = json.loads((SCENARIO / "index.json").read_text())["details"]
    sources = {SCENARIO / "index.json"}
    for section in [details["intro"], *details["steps"], details["finish"]]:
        sources.update(
            SCENARIO / section[key]
            for key in ("text", "verify", "foreground", "background")
            if key in section
        )
    for asset in details["assets"]["host01"]:
        sources.update((SCENARIO / "assets").glob(asset["file"]))
    archive = ROOT / "dist" / "virtual-energy-network.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        for source in sorted(sources):
            if source.is_file():
                bundle.add(source, arcname=str(pathlib.Path(SCENARIO.name) / source.relative_to(SCENARIO)))
    print(f"Built {archive}")


if __name__ == "__main__":
    main()
