import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("filter", nargs="?", type=str.lower)
parser.add_argument("count", nargs="?", type=int)
parser.add_argument("P", nargs="?", type=int, default=12345)
parser.add_argument("ip", nargs="?", default="123.123.123.123")
args = parser.parse_args()

files = sorted(
     (p for p in Path(".").iterdir() if p.is_file() and (args.filter in p.name.lower() if args.filter else True)),
     key=lambda p: p.stat().st_ctime,
     reverse=True
)[:args.count]

print(f'scp -P {args.P} "' + '" "'.join(str(p.resolve()) for p in files) + f'" root@{args.ip}:/root/sdxl-api/models/loras/')