import importlib
import random

try:
    DefaultPose = importlib.import_module("__main__").Pose
except AttributeError:
    DefaultPose = importlib.import_module("generate").Pose

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

def build_outfit(outfit, pose):
    if "bra" in outfit and ("pussy" in pose or "1boy" in pose):
        outfit += ", clothing aside, panties aside, breasts out, bra pull, clothes pull, strap slip, strap pull"

    return outfit