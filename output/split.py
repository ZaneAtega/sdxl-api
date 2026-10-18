from PIL import Image
from pathlib import Path
import sys

path = Path(sys.argv[1])
img = Image.open(path)
w, h = img.size

for i in range(4): 
    img.crop((
        i * w // 4, 0, (i + 1) * w // 4, h
    )).save(path.with_name(f"{path.stem}-{i + 1}{path.suffix}"))