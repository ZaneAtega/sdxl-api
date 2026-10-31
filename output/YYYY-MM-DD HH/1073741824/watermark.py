import sys
from pathlib import Path
from PIL import Image


TEXT_STROKE = 12
DESCENDER = 19

watermark = Image.open("watermark.png").convert("RGBA")

if "-t" in sys.argv:
    watermark.putalpha(watermark.getchannel("A").point(lambda a: a // 2))

for folder in sorted(
    (p for p in Path(".").iterdir() if p.is_dir()),
    key=lambda p: p.stat().st_mtime,
    reverse=True
)[:2]:
    output = folder / "Watermarked"
    output.mkdir(exist_ok=True)

    for path in sorted(folder.glob("*.png"))[:next((int(arg) for arg in sys.argv[1:] if arg.isdigit()), None)]:
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