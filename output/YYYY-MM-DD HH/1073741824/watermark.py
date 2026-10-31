import argparse
from pathlib import Path
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--all", action="store_true")
parser.add_argument("-t", action="store_true")
args = parser.parse_args()

TEXT_STROKE = 12
DESCENDER = 19

FOLDER = max((p for p in Path.cwd().iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime)

output = FOLDER / "Watermarked"
output.mkdir(exist_ok=True)

watermark = Image.open("watermark.png").convert("RGBA")

if args.t:
    watermark.putalpha(watermark.getchannel("A").point(lambda a: a // 2))

for path in sorted(FOLDER.glob("*.png"))[:None if args.all else 4]:
    with Image.open(path) as img:
        img = img.convert("RGBA")

    scale = max(img.width, img.height) / watermark.width * 0.25
    scaled_watermark = watermark.resize((int(watermark.width * scale), int(watermark.height * scale)), Image.Resampling.LANCZOS)

    margin = img.width / 328 * 4 # 328 * 4, 414 * 16
    margin -= TEXT_STROKE * scale

    margin = (
        int(margin) if img.width < img.height else int(margin - DESCENDER * scale),
        int(margin),
    )

    img.alpha_composite(scaled_watermark,
        # (0, 0)
        # (img.width - scaled_watermark.width, 0)
        # (0, img.height - scaled_watermark.height)
        (
            img.width - scaled_watermark.width - margin[1],
            img.height - scaled_watermark.height - margin[0]
        )
    )

    img.convert("RGB").save(output / path.name)