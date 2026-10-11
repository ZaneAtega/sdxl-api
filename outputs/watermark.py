from pathlib import Path
from PIL import Image

folder = max((p for p in Path.cwd().iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime)

output = folder / "Watermarked"
output.mkdir(exist_ok=True)

watermark = Image.open("watermark.png").convert("RGBA")
watermark.putalpha(watermark.getchannel("A").point(lambda a: a // 2))

for path in sorted(folder.glob("*.png"))[:4]:
    with Image.open(path) as img:
        img = img.convert("RGBA")

    img.alpha_composite(watermark,
        # (0, 0)
        # (img.width - watermark.width, 0)
        # (0, img.height - watermark.height)
        (img.width - watermark.width, img.height - watermark.height)
    )

    img.convert("RGB").save(output / path.name)