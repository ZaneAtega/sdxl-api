import json
import os
import random
import sys
from datetime import datetime

import requests

class Pose:
    def __init__(self, poses, outfit="", clothed_poses=(), min=5, max=10):
        self._original_poses = poses.copy()

        if "nude" not in outfit:
            self._original_poses.extend(clothed_poses)

        self._poses = self._original_poses.copy()
        random.shuffle(self._poses)

        self._pose = None

        self._min = min
        self._max = max
        self._limit = 0
        self._count = 0

        self._replacements = (
            ("1boy, ", "1boy, faceless male, hetero, veiny penis, "),
            (", anal, ", ", anal, sex, "),
            ("vaginal", "sex, vaginal")
        )

    def _expand_tags(self, pose):
        if "1boy" not in pose: # negative_prompt: 1boy
            pose += ", solo, looking at viewer"

        if "cowgirl" in pose or "straddling" in pose:
            pose += ", girl on top"

        if any(tag in pose for tag in ("prone bone", "doggystyle", "reverse cowgirl")):
            pose += ", sex from behind"

        """
        if "prone bone" in pose or "missionary" in pose:
            pose += ", lying"

        if "prone bone" in pose:
            pose += ", on stomach"

        if "missionary" in pose:
            pose += ", on back"
        """

        for tag, more in self._replacements:
            pose = pose.replace(tag, more)

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
    if "bra" in outfit and ("pussy" in pose or "1boy" in pose):
        outfit += ", clothing aside, panties aside, breasts out, bra pull, clothes pull, strap slip, strap pull"

    return outfit

def build_prompt(pose):
    return ", ".join((
        prompt["character"],
        build_outfit(prompt["outfit"], pose),
        scene, # location, background, environmental details, lighting, atmosphere

        random.choice(library["camera"]),
        # shot size: how much of the subject is visible
        # camera orientation: which side of the subject the camera faces
        # camera angle
        # composition: how the subject and other visual elements are arranged within the image

        pose, # pose, arm and leg positions, hand placement, gestures, actions, object interactions
        "blush, smile", # facial expression, emotion
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
scene = random.choice(library["scenes"])
pose = prompt.get("pose") or Pose(library["poses"], prompt["outfit"], library["clothed_poses"], *map(int, sys.argv[1:3]))

path = datetime.now().strftime("%Y-%m-%d %H")
os.makedirs(path, exist_ok=True)

for i in range(payload.pop("image_count")):
    generate()