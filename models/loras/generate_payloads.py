import sys
from pathlib import Path

OUTPUT_ROOT = Path(__file__).resolve().parents[2] / "output"
PAYLOADS_DIR = OUTPUT_ROOT / "payloads"

MODE = int(sys.argv[3]) if len(sys.argv) > 3 else 1

# I know what I'm doing. I specifically need the raw text exactly as I typed it, not reformatted by json.dump().
with open(OUTPUT_ROOT / f"payload-{MODE}.json", encoding="utf-8") as f:
    TEMPLATE = f.read().replace('"character": "2"', f'"character": "{sys.argv[2]}"')

for lora in tuple(
    p.stem for p in Path(".").iterdir()
    if p.is_file() and sys.argv[1].lower() in p.name.lower()
):
    payload = TEMPLATE.replace('"character": "1"', f'"character": "{lora}"')

    if MODE == 1:
        (PAYLOADS_DIR / f"{lora} 0.5.json").write_text(payload, encoding="utf-8")
        (PAYLOADS_DIR / f"{lora} 0.8.json").write_text(payload.replace(" 0.5,", " 0.8,"), encoding="utf-8")
    else:
        (PAYLOADS_DIR / f"{lora}.json").write_text(payload.replace(" 0.5,", " 1.0,"), encoding="utf-8")