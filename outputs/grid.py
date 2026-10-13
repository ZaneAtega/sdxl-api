from pathlib import Path
from PIL import Image, ImageOps
import random

portrait = None
imgs = []

folder = max((p for p in Path.cwd().iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime)

for path in sorted(folder.glob("*.png"), key=lambda _: random.random()):
    if portrait and len(imgs) >= 2:
        break

    with Image.open(path) as img:
        w, h = img.size

    if not portrait and h > w:
        portrait = path
    else:
        imgs.append(path)

with Image.open(portrait) as img:
    portrait = img.convert("RGBA")

w, _ = portrait.size
grid = Image.new("RGBA", (w, w))

grid.alpha_composite(
    ImageOps.fit(portrait, (grid.width // 2, grid.height), method=Image.Resampling.LANCZOS),
    (0, 0)
)

dim = grid.width // 2

for i, path in enumerate(imgs):
    with Image.open(path) as img:
        img = img.convert("RGBA")

    grid.alpha_composite(
        ImageOps.fit(img, (dim, dim), method=Image.Resampling.LANCZOS),
        (dim, i * dim)
    )

grid.convert("RGB").save(Path(__file__).with_name(f"{folder.name}.png"))