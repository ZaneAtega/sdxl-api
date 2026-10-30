import json
import random
import sys
from datetime import datetime
from hashlib import md5
from pathlib import Path

import requests

DRY_RUN = "--dry" in sys.argv
HENTAI = "--sfw" not in sys.argv

with open(Path(__file__).with_name("prompts.json"), encoding="utf-8") as f:
    LIBRARY = json.loads("".join(line.split("//")[0] for line in f))

class Pose:
    def __init__(self, poses, min=5, max=10):
        self._original_poses = poses.copy()
        self._poses = self._original_poses.copy()
        random.shuffle(self._poses)
        self._pose = None
        self._finished_poses = {""}

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

        pose = ""

        while pose in self._finished_poses:
            if not self._poses:
                self._poses = self._original_poses.copy()
                random.shuffle(self._poses)

            pose = self._poses.pop()

            while isinstance(pose, list):
                pose = random.choice(pose)

        self._pose = self._expand_tags(pose)

        return self._pose

    def increment(self):
        self._count += 1

def build_pose(pose, scene):
    return pose

def build_outfit(outfit, pose, camera):
    return outfit

def build_negative_prompt(prompt):
    return ""

def build_folder_name(pose):
    return md5(pose.encode()).hexdigest()[:12]

if HENTAI:
    from hentai_prompts import *

def load_payloads(file_paths, pose_limits=(5, 10)):
    payloads = {}

    for file_path in file_paths:
        with open(file_path, encoding="utf-8") as f:
            payloads[file_path] = json.load(f)

        complete_prompt(payloads[file_path]["prompt"], pose_limits)

    return payloads

def complete_prompt(prompt, pose_limits=(5, 10)):
    prompt["character"] = (
        f"{prompt['character']}, {LIBRARY['characters'][prompt['character']]}" +
        (", deltoids, biceps, abs" if "toned" in prompt["character"] else "")
    )

    prompt["outfit"] = prompt.get("outfit") or random.choice(LIBRARY["outfits"])
    prompt["scene"] = prompt.get("scene") or random.choice(LIBRARY["scenes"])
    prompt["expression"] = prompt.get("expression", "blush, smile")

    prompt["pose"] = prompt.get("pose") or Pose(
        LIBRARY["poses"],
        *pose_limits,
        outfit=prompt["outfit"],
        clothed_poses=LIBRARY["clothed_poses"]
    )

def build_prompt(prompt):
    pose = prompt["pose"]
    camera = random.choice(LIBRARY["camera"]) if "pov" not in pose and ", from" not in pose else ""

    return ", ".join(filter(None, (
        prompt["character"],
        build_outfit(prompt["outfit"], pose, camera),
        prompt["scene"], # location, background, environmental details, lighting, atmosphere

        camera,
        # shot size: how much of the subject is visible
        # camera orientation: which side of the subject the camera faces
        # camera angle
        # composition: how the subject and other visual elements are arranged within the image

        build_pose(pose, prompt["scene"]), # pose, arm and leg positions, hand placement, gestures, actions, object interactions
        prompt["expression"], # facial expression, emotion
    )))

def generate(payload, output_dir=Path(".")):
    pose = payload["prompt"]["pose"]
    prompt = payload["prompt"].copy()
    prompt["pose"] = pose.next() if isinstance(pose, Pose) else pose

    if DRY_RUN:
        content = b""
    else:
        try:
            response = requests.post("http://127.0.0.1:7869/", json={
                **payload,
                "prompt": build_prompt(prompt),
                "negative_prompt": build_negative_prompt(prompt)
            })
        except requests.Timeout:
            return

        content = response.content

    if isinstance(pose, Pose):
        pose.increment()

    path = output_dir / payload['character'] / build_folder_name(prompt['pose'])
    path.mkdir(parents=True, exist_ok=True)

    with open(path / f"{int(datetime.now().timestamp())}.png", "wb") as f:
        f.write(content)

def main():
    output_dir = Path(datetime.now().strftime("%Y-%m-%d %H"))
    output_dir.mkdir(exist_ok=True)

    payloads = load_payloads(Path("payloads").iterdir(), tuple([int(arg) for arg in sys.argv[1:] if arg.isnumeric()]))

    for payload in payloads.values():
        for _ in range(payload.pop("image_count")):
            generate(payload, output_dir)

if __name__ == "__main__":
    main()