import argparse
import base64
import json
from pathlib import Path

import requests

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--character")
parser.add_argument("-o", "--outfit")
parser.add_argument("-s", "--scene")
parser.add_argument("-e", "--exclude")
args = parser.parse_args()

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent

LIBRARY = json.loads((PARENT.parent / "output" / "prompts.json").read_text())

CHARACTER_TAGS, OUTFIT_TAGS, SCENE_TAGS = (
    {tag.strip() for tag in (
        LIBRARY[f"{arg}s"][getattr(args, arg)] if arg == "character" else
        LIBRARY[f"{arg}s"][int(getattr(args, arg))]
    ).split(", ")} if getattr(args, arg) else set()
    for arg in ("character", "outfit", "scene")
)
CHARACTER_AND_OUTFIT_TAGS = CHARACTER_TAGS | OUTFIT_TAGS

EXPRESSIONS = {
    "ahegao", "blush",
    "closed mouth", "open mouth", "parted lips", "saliva", "smile",
    "closed eyes", "half-closed eyes", "rolling eyes"
}

EXCLUDED_TAGS = CHARACTER_TAGS | OUTFIT_TAGS | SCENE_TAGS | EXPRESSIONS | {
    tag.strip() for tag in (PARENT / "excluded_tags.txt").read_text().split(",")
} | (
    {tag.strip() for tag in args.exclude.split(",")} if args.exclude else set()
)

CONDITIONAL_EXCLUSIONS = json.loads((PARENT / "hentai_conditional_exclusions.json").read_text())

COLORS = ("red", "orange", "yellow", "green", "purple", "black", "grey", "white")

CLOTHING = (
    "bow", "hairband", "ribbon", "scrunchie",
    "choker", "collar",
    "shirt", "bra", "tank top", "dress",
    "garter belt", "garter straps",
    "pants", "panties", "shorts", "thighhighs", "socks"
)

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

    tags -= {
        clothing for tag in CHARACTER_AND_OUTFIT_TAGS
        for color, _, clothing in [tag.partition(" ")]
        if color in COLORS and clothing in CLOTHING
    }

    for tag, associated_tags in CONDITIONAL_EXCLUSIONS.items():
        if tag in tags or tag in CHARACTER_AND_OUTFIT_TAGS:
            tags.difference_update(associated_tags)

    tags -= EXCLUDED_TAGS

    if tags:
        output.append(f"{folder.name}: {', '.join(sorted(tags))}")

(ROOT / f"{ROOT.name}.txt").write_text("\n\n".join(output), encoding="utf-8")