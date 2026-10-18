from importlib import import_module
import random

try:
    DefaultPose = import_module("__main__").Pose
except AttributeError:
    DefaultPose = import_module("generate").Pose

class Pose(DefaultPose):
    def __init__(self, poses, min=5, max=10, outfit="", clothed_poses=()):
        self._original_poses = poses.copy() + ([] if "nude" in outfit else clothed_poses)
        self._poses = self._original_poses.copy()
        random.shuffle(self._poses)
        self._pose = None
        self._finished_poses = {""}

        self._min = min
        self._max = max
        self._limit = 0
        self._count = 0

        self._replacements = (
            ("1boy, ", "1boy, faceless male, hetero, veiny penis, "),
            (", anal, ", ", anal, sex, "),
            ("vaginal", "sex, vaginal"),
            ("guided breast grab", "guided breast grab, grabbing another's breast, groping, pov, pov hands")
        )

    def _expand_tags(self, pose):
        pose = f"1girl, {pose}, {'solo focus' if '1boy' in pose else 'solo, looking at viewer'}"

        if "cowgirl" in pose or "straddling" in pose:
            pose += ", girl on top"

        if any(tag in pose for tag in ("prone bone", "doggystyle", "reverse cowgirl", "full nelson")):
            pose += ", sex from behind"

        for tag, more in self._replacements:
            pose = pose.replace(tag, more)

        return pose

def build_pose(pose, scene):
    if "bed" in scene and "prone bone" in pose and random.random() < 0.5:
        pose += ", pillow grab, pillow hug"

    return pose

def build_outfit(outfit, pose):
    if "nude" in outfit:
        return outfit
    elif "underwear" in outfit:
        outfit += ", underwear only"

    if any(tag in pose for tag in ("pussy", "1boy", "covering")):
        outfit += ", breasts out, clothes lift, clothes pull, clothing aside"

        if "bra," in outfit:
            outfit += ", bra pull, panties aside, panty pull, strap pull, strap slip"

            if "sports bra" in outfit:
                outfit += ", sports bra lift"
            else:
                outfit += ", bra lift"
        elif "bikini" in outfit:
            outfit += ", bikini pull, bikini bottom aside, bikini top aside, bikini top lift"
        else:
            outfit += ", no bra"

            if "shirt" in outfit:
                outfit += ", shirt lift"
            elif "dress" in outfit:
                outfit += ", dress lift"

        if "pants" in outfit:
            outfit += ", pants pull"
        elif "shorts" in outfit:
            outfit += ", shorts pull"
    elif random.random() < 0.5:
        outfit += f", cameltoe, {random.choice(('covered nipples', 'areola slip, nipple slip', 'one breast out'))}"

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