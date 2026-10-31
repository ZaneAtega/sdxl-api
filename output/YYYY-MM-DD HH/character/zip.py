from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from natsort import natsorted

ROOT = Path(".")

items = natsorted(
    [*ROOT.glob("*.png"), *ROOT.glob("*/*.png")],
    key=lambda p: str(p.relative_to(ROOT))
)

with ZipFile(ROOT / f"{ROOT.resolve().name}.zip", "w", ZIP_DEFLATED) as z:
    for i, p in enumerate(items, 1):
        z.write(p, f"{i:03}.png")