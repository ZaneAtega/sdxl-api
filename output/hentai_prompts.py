import random
from hashlib import md5
from importlib import import_module

try:
    DefaultPose = import_module("__main__").Pose
except AttributeError:
    DefaultPose = import_module("generate").Pose

__all__ = [
    "Pose",
    "build_pose",
    "build_outfit",
    "build_negative_prompt",
    "build_folder_name",
]

NO_HANDS = "hands++++, grabbing++++, grabbing another's breast++++, grabbing another's ass++++, ass grab++++, hands on another's hips++++"

POSE_ORDERS = {
    "footjob": 901,
    "after sex": 900,
    "mating press": 801,
    "full nelson": 800,
    "imminent penetration": 301,
    "presenting": 300,
    "irrumatio": 201,
    "fellatio": 200,
    "guided breast grab": 102,
    "covering": 101,
    "undressing": 100
}

girl_on_top, other_pose = (500, 600) if random.random() < 0.5 else (600, 500)
missionary, sex_from_behind = (400, other_pose) if random.random() < 0.5 else (other_pose, 400)

FLEXIBLE_POSE_ORDERS = {
    "girl on top": girl_on_top,
    "missionary": missionary,
    "sex from behind": sex_from_behind
}

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
            ("1boy", "1boy, faceless male, hetero, veiny penis"),
            (", anal, ", ", anal, sex, "),
            (", vaginal, ", ", vaginal, sex, "),
            ("after vaginal", "after sex, after vaginal"),
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

def build_outfit(outfit, pose, camera):
    if "nude" in outfit:
        return outfit if "behind" in camera else f"{outfit}, nipples"
    elif "underwear" in outfit:
        outfit += ", underwear only"

    if any(tag in pose for tag in ("pussy", "1boy", "covering")):
        outfit += ", breasts out"

        if "behind" not in camera:
            outfit += ", nipples"

        if "bra," in outfit:
            outfit += ", " + (
                "bra pull" if random.random() < 0.5 else
                "sports bra lift" if "sports bra" in outfit else
                "bra lift"
            )
            outfit += f", {'panties aside' if random.random() < 0.5 else 'panty pull'}"
        elif "bikini" in outfit:
            outfit += ", " + (
                "bikini pull" if random.random() < 0.5 else
                f"bikini bottom aside, {'bikini top lift' if random.random() < 0.5 else 'bikini top aside'}"
            )
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
        outfit += ", cameltoe"

        if "behind" not in camera:
            outfit += f", {random.choice(('covered nipples', 'areola slip', 'one breast out'))}"

    return outfit

def build_negative_prompt(prompt):
    negative_tags = []

    if "1boy" in prompt:
        negative_tags.append("2boys")

        if not any(tag in prompt for tag in ("grab", "fellatio")):
            negative_tags.append(NO_HANDS)
    else:
        negative_tags.append("1boy++++")

    if "sex" in prompt:
        negative_tags.append("double penetration")

    if "indoors" in prompt:
        negative_tags.append("looking through window, painting (object), picture frame")

    if "pov" not in prompt:
        negative_tags.append("pov hands++")

    return ", ".join(negative_tags)

def get_order_and_main_tag(pose):
    for tag, order in POSE_ORDERS.items():
        if tag in pose:
            return f"{order} {tag}"

    for tag, order in FLEXIBLE_POSE_ORDERS.items():
        if tag in pose:
            return f"{order + random.randrange(0, 99)} {tag}"

    if "1boy" not in pose:
        return f"0 {pose.split(', ')[1]}"

    return f"{random.randrange(400, 800)} {pose.split(', ')[5]}"

def build_folder_name(pose):
    return f"{get_order_and_main_tag(pose)} {md5(pose.encode()).hexdigest()[:12]}"