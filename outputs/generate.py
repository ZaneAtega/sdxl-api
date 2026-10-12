import json
import os
import random
from datetime import datetime

import requests

URL = "http://127.0.0.1:7869/"

with open("payload.json", encoding="utf-8") as f:
    payload = json.load(f)

with open("prompts.json", encoding="utf-8") as f:
    library = json.load(f)

prompt = payload.pop("prompt")
prompt["character"] = f"{prompt['character']}, {library['characters'][prompt['character']]}"

if "outfit" not in prompt:
    prompt["outfit"] = random.choice(library["outfits"])

scene = random.choice(library["scenes"])

path = datetime.now().strftime("%Y-%m-%d %H")
os.makedirs(path, exist_ok=True)

def build_prompt():
    return ", ".join((
        prompt["character"],
        prompt["outfit"],
        scene, # location, background, environmental details, lighting, atmosphere

        random.choice(library["camera"]),
        # shot size: how much of the subject is visible
        # camera orientation: which side of the subject the camera faces
        # camera angle
        # composition: how the subject and other visual elements are arranged within the image

        random.choice(library["poses"]), # pose, arm and leg positions, hand placement, gestures, character actions, environmental interactions
        random.choice(library["expressions"]), # facial expression, emotion
    ))

def generate():
    try:
        response = requests.post(URL, json={"prompt": build_prompt(), **payload})
    except requests.Timeout:
        return

    with open(f"{path}/{int(datetime.now().timestamp())}.png", "wb") as f:
        f.write(response.content)

for i in range(payload.pop("image_count")):
    generate()