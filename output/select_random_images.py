import random
import sys
from base64 import b64encode
from io import BytesIO
from pathlib import Path
from shutil import copy

import requests
from PIL import Image, ImageOps

def censor(path):
    return requests.post("http://127.0.0.1:7870/", json={
        "image": b64encode(path.read_bytes()).decode(),
        "require_both_genitals": True
    }).content

def select_random_images(folder, max_total=15):
    output_dir = folder.parent / str(random.randint(0, 2147483647))
    uncensored_dir = output_dir / "uncensored"
    censored_dir = output_dir / "censored"
    uncensored_dir.mkdir(parents=True)
    censored_dir.mkdir()

    subfolders = [p for p in folder.iterdir() if p.is_dir()]

    while len(subfolders) > max_total / 1.5:
        subfolders.pop(random.randrange(len(subfolders)))

    grand_total = 0

    for subfolder in subfolders:
        if grand_total >= max_total:
            break

        count = 0
        limit = random.randint(1, 2)

        paths = list(subfolder.glob("*.png"))
        random.shuffle(paths)

        for path in paths:
            if count >= limit or grand_total >= max_total:
                break

            filename = f"{grand_total} {path.name}"

            if float(subfolder.name.split()[0]) < 200:
                copy(path, censored_dir / filename)
                copy(path, uncensored_dir / filename)
            elif censored := censor(path):
                with Image.open(BytesIO(censored)) as img:
                    img.save(censored_dir / filename)

                copy(path, uncensored_dir / filename)
            else:
                continue

            count += 1
            grand_total += 1

def main(folder, count=3):
    for _ in range(count):
        select_random_images(folder)

if __name__ == "__main__":
    main(
        Path(sys.argv[1]) if len(sys.argv) > 1 else max((p for p in Path(".").iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime),
        next((int(arg) for arg in sys.argv[1:] if arg.isdigit()), 3)
    )