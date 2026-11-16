"""Build example/Achievements Example.json: a one-screen game that shows every part of the extension.

Usage: python3 tools/build_example.py      (then tools/build.sh normalizes, checks and exports it)

  SPACE  jump            -> "First Step" (unlock) and "Jumper" (progress, goal 10)
  C      find a coin     -> "Coin Hunter" (progress, goal 5)
  wait 15 seconds        -> "Patience" (set progress from a timer)
  all four               -> "Completionist" (set progress from UnlockedCount())
  B      toasts at the bottom-right    M  toast label in Malay    R  reset all achievements
"""
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gd.dsl import A, C, NOT, comment, ev, group, key_just, q, repeat, scene_start, set_num, set_str_expr, text, vars_  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
W, H = 1280, 720
NS = "Achievements::"
H0 = ""  # extension instructions have a hidden first and last parameter (the scene and the events context)


def ach(name, *params):
    return A(NS + name, H0, *params, "")


def ach_cond(name, *params, inverted=False):
    return C(NS + name, H0, *params, "", inverted=inverted)


def text_object(name, size, colour="255;255;255", bold=False):
    r, g, b = [int(c) for c in colour.split(";")]
    return {"assetStoreId": "", "bold": bold, "italic": False, "name": name, "smoothed": True,
            "type": "TextObject::Text", "underlined": False, "variables": [], "effects": [], "behaviors": [],
            "string": name, "font": "", "textAlignment": "left", "characterSize": size, "color": {"r": r, "g": g, "b": b},
            "content": {"bold": bold, "isOutlineEnabled": False, "isShadowEnabled": False, "italic": False,
                        "outlineColor": "0;0;0", "outlineThickness": 2, "shadowAngle": 90, "shadowBlurRadius": 2,
                        "shadowColor": "0;0;0", "shadowDistance": 4, "shadowOpacity": 127, "smoothed": True,
                        "underlined": False, "text": name, "font": "", "textAlignment": "left",
                        "verticalTextAlignment": "top", "characterSize": size, "lineHeight": 0, "color": colour}}


def inst(name, x, y):
    return {"angle": 0, "customSize": False, "height": 0, "keepRatio": True, "layer": "", "name": name,
            "persistentUuid": str(uuid.uuid5(uuid.NAMESPACE_URL, "achievements-example/" + name)), "width": 0,
            "x": x, "y": y, "zOrder": 1, "numberProperties": [], "stringProperties": [], "initialVariables": []}


def layer(name):
    return {"ambientLightColorB": 200, "ambientLightColorG": 200, "ambientLightColorR": 200,
            "camera2DPlaneMaxDrawingDistance": 5000, "camera3DFarPlaneDistance": 10000,
            "camera3DFieldOfView": 45, "camera3DNearPlaneDistance": 3, "cameraType": "",
            "followBaseLayerCamera": False, "isLightingLayer": False, "isLocked": False, "name": name,
            "renderingType": "", "visibility": True,
            "cameras": [{"defaultSize": True, "defaultViewport": True, "height": 0, "viewportBottom": 1,
                         "viewportLeft": 0, "viewportRight": 1, "viewportTop": 0, "width": 0}],
            "effects": []}


ACHIEVEMENTS = [
    ("first_step", "First Step", "Press SPACE for the first time.", 1),
    ("jumper", "Jumper", "Jump 10 times.", 10),
    ("coin_hunter", "Coin Hunter", "Find 5 coins (press C).", 5),
    ("patience", "Patience", "Stay in the game for 15 seconds.", 15),
    ("completionist", "Completionist", "Unlock every other achievement.", 4),
]


def item(expr_id, what):
    return f"{NS}{what}({expr_id})"


def events():
    I = f"{NS}IdAt(i)"
    return [
        comment("Achievements extension example. Every achievement is defined once, when the game starts. "
                "Progress is saved on this device, so it is still here when you play again (press R to reset)."),
        group("Define the achievements", [
            ev([scene_start()], [ach("DefineAchievement", q(i), q(t), q(d), g) for i, t, d, g in ACHIEVEMENTS]),
        ]),
        group("Unlock and add progress", [
            comment("Unlock an achievement in one go, or add progress: it unlocks when the progress reaches the goal."),
            ev([key_just("Space")], [ach("Unlock", q("first_step")), ach("AddProgress", q("jumper"), 1)]),
            ev([key_just("c")], [ach("AddProgress", q("coin_hunter"), 1)]),
            comment("Set the progress from any number: here the time spent in the scene, and how many are unlocked."),
            ev([], [ach("SetProgress", q("patience"), "floor(TimeFromStart())"),
                    ach("SetProgress", q("completionist"), f"{NS}UnlockedCount()")]),
        ]),
        group("React to an unlock", [
            comment("\"Any achievement was just unlocked\" is true for one frame: play a sound or give a reward here."),
            ev([ach_cond("AnyJustUnlocked")],
               [text("LastText", f'"Last unlocked: " + {NS}Title({NS}LastUnlocked())')]),
        ]),
        group("Achievements screen", [
            comment("Build the list with a Repeat event: IdAt(i) gives the identifier of each achievement."),
            ev([], [set_num("i", 0), set_str_expr("list", '""')]),
            repeat(f"{NS}Count()", subs=[
                ev([ach_cond("IsUnlocked", I)], [set_str_expr("mark", '"[X]  "')]),
                ev([ach_cond("IsUnlocked", I, inverted=True)], [set_str_expr("mark", '"[  ]  "')]),
                ev([], [set_str_expr("list", f'list + mark + {item(I, "Title")} + "  -  " + {item(I, "Description")}'
                                             f' + "  (" + ToString({item(I, "Progress")}) + " / " + ToString({item(I, "Goal")}) + ")" + NewLine()'),
                        set_num("i", 1, "+")]),
            ]),
            ev([], [text("ListText", "list"),
                    text("CountText", f'"Unlocked: " + ToString({NS}UnlockedCount()) + " / " + ToString({NS}Count())'
                                      f' + "      Jumps: " + ToString({item(q("jumper"), "Progress")})'
                                      f' + "      Coins: " + ToString({item(q("coin_hunter"), "Progress")})')]),
        ]),
        group("Toast settings", [
            comment("The toast works with no setup. These actions change its look."),
            ev([key_just("b")], [ach("SetToastPosition", q("Bottom-right"))]),
            ev([key_just("m")], [ach("SetToastLabel", q("Pencapaian dibuka")),
                                 ach("SetToastColors", q("20;60;40"), q("255;255;255"), q("120;230;140"))]),
            ev([key_just("r")], [ach("ResetAll"), A("Scene", "", q("Example"), "")]),
        ]),
    ]


HELP = ("SPACE  jump        C  find a coin        B  toasts at the bottom-right        "
        "M  toast in Malay        R  reset all")


def build():
    objects = [text_object("TitleText", 44, "255;200;61", bold=True), text_object("HelpText", 20, "190;196;220"),
               text_object("CountText", 24), text_object("ListText", 24), text_object("LastText", 22, "255;200;61")]
    objects[0]["string"] = objects[0]["content"]["text"] = "Achievements example"
    objects[1]["string"] = objects[1]["content"]["text"] = HELP
    for o in objects[2:]:
        o["string"] = o["content"]["text"] = ""
    scene = {"b": 40, "disableInputWhenNotFocused": True, "mangledName": "Example", "name": "Example", "r": 22,
             "standardSortMethod": True, "stopSoundsOnStartup": True, "title": "", "v": 34, "uiSettings": {},
             "objectsGroups": [], "variables": vars_({"i": 0, "list": "", "mark": ""}),
             "instances": [inst("TitleText", 60, 50), inst("HelpText", 60, 120), inst("CountText", 60, 190),
                           inst("ListText", 60, 250), inst("LastText", 60, 600)],
             "objects": objects, "events": events(), "layers": [layer("")], "behaviorsSharedData": []}
    return {
        "firstLayout": "Example",
        "gdVersion": {"build": 287, "major": 5, "minor": 6, "revision": 0},
        "properties": {
            "adaptGameResolutionAtRuntime": True, "antialiasingMode": "MSAA", "antialisingEnabledOnMobile": False,
            "folderProject": False, "orientation": "landscape", "packageName": "com.example.achievements",
            "pixelsRounding": False, "projectUuid": str(uuid.uuid5(uuid.NAMESPACE_URL, "achievements-example")),
            "scaleMode": "linear", "sizeOnStartupMode": "adaptWidth", "templateSlug": "", "version": "1.0.0",
            "name": "Achievements Example", "description": "Example for the Achievements extension.",
            "author": "", "windowWidth": W, "windowHeight": H, "latestCompilationDirectory": "",
            "maxFPS": 60, "minFPS": 20, "verticalSync": False, "platformSpecificAssets": {},
            "loadingScreen": {"backgroundColor": 0x162228, "backgroundFadeInDuration": 0.2,
                              "backgroundImageResourceName": "", "gdevelopLogoStyle": "light",
                              "logoAndProgressFadeInDuration": 0.2, "logoAndProgressLogoFadeInDelay": 0,
                              "minDuration": 0, "progressBarColor": 0xffc83d, "progressBarHeight": 8,
                              "progressBarMaxWidth": 200, "progressBarMinWidth": 40, "progressBarWidthPercent": 40,
                              "showGDevelopSplash": False, "showProgressBar": True},
            "watermark": {"placement": "bottom-left", "showWatermark": True},
            "authorIds": [], "authorUsernames": [], "categories": [], "playableDevices": ["keyboard"],
            "extensionProperties": [], "platforms": [{"name": "GDevelop JS platform"}],
            "currentPlatform": "GDevelop JS platform"},
        "resources": {"resources": [], "resourceFolders": []},
        "objects": [], "objectsGroups": [], "variables": [], "layouts": [scene], "externalEvents": [],
        "eventsFunctionsExtensions": [json.loads((ROOT / "extension" / "Achievements.json").read_text())],
        "externalLayouts": [],
    }


if __name__ == "__main__":
    out = ROOT / "example" / "Achievements Example.json"
    out.write_text(json.dumps(build(), indent=1))
    print(out.relative_to(ROOT))
