import json
import os
import random
import sys
from datetime import datetime

import requests

HENTAI = True

class Pose:
    def __init__(self, poses, min=5, max=10):
        self._original_poses = poses.copy()
        self._poses = self._original_poses.copy()
        random.shuffle(self._poses)
        self._pose = None

        self._min = min
        self._max = max
        self._limit = 0
        self._count = 0

        self._replacements = ()

    def _expand_tags(self, pose):
        return pose

    def next(self):
        if self._count < self._limit:
            return self._pose

        self._count = 0
        self._limit = random.randint(self._min, self._max)

        if not self._poses:
            self._poses = self._original_poses.copy()
            random.shuffle(self._poses)

        pose = self._poses.pop()
        pose = random.choice(pose) if isinstance(pose, list) else pose
        self._pose = self._expand_tags(pose)

        return self._pose

    def increment(self):
        self._count += 1

def build_outfit(outfit, pose):
    return outfit

if HENTAI:
    from hentai_prompts import build_outfit, Pose

def build_prompt(pose):
    return ", ".join((
        prompt["character"],
        build_outfit(prompt["outfit"], pose),
        prompt["scene"], # location, background, environmental details, lighting, atmosphere

        random.choice(library["camera"]),
        # shot size: how much of the subject is visible
        # camera orientation: which side of the subject the camera faces
        # camera angle
        # composition: how the subject and other visual elements are arranged within the image

        pose, # pose, arm and leg positions, hand placement, gestures, actions, object interactions
        prompt["expression"], # facial expression, emotion
    ))

def generate():
    try:
        response = requests.post("http://127.0.0.1:7869/", json={
            "prompt": build_prompt(pose.next() if isinstance(pose, Pose) else pose), **payload
        })
    except requests.Timeout:
        return

    if isinstance(pose, Pose):
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
prompt["scene"] = prompt.get("scene") or random.choice(library["scenes"])
prompt["expression"] = prompt.get("expression", "blush, smile")

pose = prompt.get("pose") or Pose(
    library["poses"],
    *map(int, sys.argv[1:3]),
    outfit=prompt["outfit"],
    clothed_poses=library["clothed_poses"]
)

path = datetime.now().strftime("%Y-%m-%d %H")
os.makedirs(path, exist_ok=True)

for i in range(payload.pop("image_count")):
    generate()