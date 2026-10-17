from importlib import import_module
import random

try:
    DefaultPose = import_module("__main__").Pose
except AttributeError:
    DefaultPose = import_module("generate").Pose

class Pose(DefaultPose):
    def __init__(self, poses, min=5, max=10, outfit="", clothed_poses=()):
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
        pose = f"1girl, {pose}, {'solo focus' if '1boy' in pose else 'solo, looking at viewer'}"

        if "cowgirl" in pose or "straddling" in pose:
            pose += ", girl on top"

        if any(tag in pose for tag in ("prone bone", "doggystyle", "reverse cowgirl")):
            pose += ", sex from behind"

        for tag, more in self._replacements:
            pose = pose.replace(tag, more)

        return pose

def build_outfit(outfit, pose):
    if "bra" in outfit:
        if any(tag in pose for tag in ("pussy", "1boy", "covering")):
            outfit += ", bra lift, bra pull, breasts out, clothes lift, clothes pull, clothing aside, panties aside, panty pull, strap pull, strap slip"
        elif random.random() < 0.5:
            outfit += ", covered nipples"             

    return outfit

def build_negative_prompt(prompt):
    negative_tags = []

    if "1boy" in prompt:
        negative_tags.append("2boys")
    else:
        negative_tags.append("1boy++++")

    if "sex" in prompt:
        negative_tags.append("double penetration")

    if "indoors" in prompt:
        negative_tags.append("looking through window, painting (object), picture frame")

    return ", ".join(negative_tags)