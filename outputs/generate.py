import json
import os
import random
from datetime import datetime

import requests

URL = "http://127.0.0.1:7869/"

def generate():
    try:
        response = requests.post(URL, json={"prompt": random.choice(prompts), **payload})
    except requests.Timeout:
        return

    with open(f"{int(datetime.now().timestamp())}.png", "wb") as f:
        f.write(response.content)

with open("payload.json", encoding="utf-8") as f:
    payload = json.load(f)

prompts = payload.pop("prompts")

path = datetime.now().strftime("%Y-%m-%d %H")
os.makedirs(path, exist_ok=True)
os.chdir(path)

for i in range(payload.pop("image_count")):
    generate()