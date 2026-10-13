import base64
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent

EXCLUDE = {tag.strip() for tag in (ROOT / "exclude.txt").read_text().split(",")} | (
    {tag.strip() for tag in sys.argv[1].split(",")} if len(sys.argv) > 1 else set()
)

EXPRESSIONS = {
    "ahegao", "blush",
    "closed mouth", "open mouth", "parted lips", "smile", "saliva",
    "closed eyes", "half-closed eyes", "rolling eyes"
}

EXTENSIONS = {".jpg", ".jpeg", ".png"}

output = []

for folder in ROOT.iterdir():
    if not folder.is_dir():
        continue

    tags = set()

    for path in folder.iterdir():
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            continue

        with open(path, "rb") as file:
            image = base64.b64encode(file.read()).decode("utf-8")

        response = requests.post("http://127.0.0.1:7861/tagger/v1/interrogate", json={
            "image": image,
            "model": "wd-vit-tagger-v3"
        })

        tags.update(
            tag.replace("_", " ")
            for tag, value in response.json()["caption"]["tag"].items()
            if value >= 0.35
        )

    if not tags:
        continue

    tags -= EXCLUDE

    output.append(
        f"{folder.name}\n\n"
        f"{', '.join(sorted(tags - EXPRESSIONS))}\n\n"
        f"{', '.join(sorted(tags & EXPRESSIONS))}"
    )

(ROOT / f"{ROOT.name}.txt").write_text("\n\n".join(output), encoding="utf-8")