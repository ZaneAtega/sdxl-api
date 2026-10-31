import random
import sys
from base64 import b64encode
from io import BytesIO
from pathlib import Path
from time import time

import requests
from PIL import Image, ImageOps

def select_images(folder):
    portrait = None
    imgs = []

    paths = [*folder.glob("*.png"), *folder.glob("*/*.png")]
    random.shuffle(paths)

    for path in paths:
        if portrait and len(imgs) >= 2:
            break

        with Image.open(path) as img:
            w, h = img.size

        if not portrait and h > w:
            portrait = path
        elif w == h:
            imgs.append(path)

    return portrait, imgs

def censor(path, cell_size=None):
    if content := requests.post("http://127.0.0.1:7870/", json={
        "image": b64encode(path.read_bytes()).decode(),
        "require_both_genitals": True,
        "cell_size": cell_size
    }).content:
        return Image.open(BytesIO(content)).convert("RGBA")

def grid(portrait, imgs, should_censor=False):
    portrait = censor(portrait) if should_censor else Image.open(portrait).convert("RGBA")

    if not portrait:
        return

    w, _ = portrait.size
    grid = Image.new("RGBA", (w, w))
    grid.alpha_composite(ImageOps.fit(portrait, (grid.width // 2, grid.height), method=Image.Resampling.LANCZOS), (0, 0))
    dim = grid.width // 2

    for i, path in enumerate(imgs):
        img = Image.open(path).convert("RGBA")

        if should_censor and not (img := censor(path, max(img.size) // (dim / min(img.size)) // 100)):
            return

        grid.alpha_composite(
            ImageOps.fit(img, (dim, dim), method=Image.Resampling.LANCZOS),
            (dim, i * dim)
        )

    grid.convert("RGB").save(Path(__file__).with_name(f"{int(time())}{'_censored' if should_censor else ''}.png"))
    return True

def main(folder, count=5):
    for _ in range(count):
        result = None

        while not result:
            portrait, imgs = select_images(folder)
            result = grid(portrait, imgs, True)

        grid(portrait, imgs)

if __name__ == "__main__":
    main(
        Path(sys.argv[1]) if len(sys.argv) > 1 else max((p for p in Path.cwd().iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime),
        next((int(arg) for arg in sys.argv[1:] if arg.isdigit()), 5)
    )