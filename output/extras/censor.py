from base64 import b64encode
from pathlib import Path

import requests

for path in Path(".").glob("*.png"):
    content = requests.post("http://127.0.0.1:7870/",json={
        "image": b64encode(path.read_bytes()).decode(),
        "require_both_genitals": False
    }).content

    if content:
        path.with_name(f"{path.stem}_censored.png").write_bytes(content)