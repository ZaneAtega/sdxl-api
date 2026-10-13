import json
import os
import random
import sys
from datetime import datetime

import requests

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:7869/"

class Pose:
    def __init__(self, poses):
        self._poses = poses
        self._count = 0
        self._limit = 0
        self._pose = None

    def next(self):
        if self._count < self._limit:
            return self._pose

        self._count = 0
        self._limit = random.randint(5, 10)
        self._pose = random.choice(self._poses)

        return self._pose

    def increment(self):
        self._count += 1

def build_prompt(pose):
    return ", ".join((
        prompt["character"],
        prompt["outfit"],
        scene, # location, background, environmental details, lighting, atmosphere

        random.choice(library["camera"]),
        # shot size: how much of the subject is visible
        # camera orientation: which side of the subject the camera faces
        # camera angle
        # composition: how the subject and other visual elements are arranged within the image

        f"{pose}, {'faceless male' if '1boy' in pose else 'solo'}", # pose, arm and leg positions, hand placement, gestures, actions, object interactions
        random.choice(library["expressions"]), # facial expression, emotion
    ))

def generate():
    try:
        response = requests.post(URL, json={"prompt": build_prompt(pose.next()), **payload})
    except requests.Timeout:
        return

    pose.increment()

    with open(f"{path}/{int(datetime.now().timestamp())}.png", "wb") as f:
        f.write(response.content)

with open("payload.json", encoding="utf-8") as f:
    payload = json.load(f)

with open("prompts.json", encoding="utf-8") as f:
    library = json.load(f)

prompt = payload.pop("prompt")
prompt["character"] = f"{prompt['character']}, {library['characters'][prompt['character']]}"
prompt["outfit"] = prompt.get("outfit") or random.choice(library["outfits"])
scene = random.choice(library["scenes"])
pose = Pose(library["poses"])

path = datetime.now().strftime("%Y-%m-%d %H")
os.makedirs(path, exist_ok=True)

for i in range(payload.pop("image_count")):
    generate()