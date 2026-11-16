"""Build extension/Achievements.json, the GDevelop extension.

Usage: python3 tools/build_extension.py

The runtime core lives in src/core.js and is pasted into the "onFirstSceneLoaded" lifecycle function.
Every action, condition and expression below is a small JavaScript event that calls that core.
"""
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.0.0"
NS = "Achievements"

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="#ffc83d" d="M7 2h10v2h4v3a5 5 0 0 1-4.6 5A5 5 0 0 1 13 15v3h3v3H8v-3h3v-3a5 5 0 0 1-3.4-3A5 5 0 0 1 3 7V4h4V2zm0 4H5v1a3 3 0 0 0 2 2.8V6zm10 0v3.8A3 3 0 0 0 19 7V6h-2z"/></svg>"""


def js(code, objects=""):
    """A JavaScript event. The first line gets the shared core."""
    lines = ["const A = runtimeScene.getGame().__achievements;", "if (!A) return;"] + code.strip().split("\n")
    return {"type": "BuiltinCommonInstructions::JsCode", "inlineCode": "\n".join(lines),
            "parameterObjects": objects, "useStrict": True, "eventsSheetExpanded": False}


def arg(name):
    return f'eventsFunctionContext.getArgument("{name}")'


def p(name, description, kind="string", extra=None, default=None, long_description=None):
    d = {"description": description, "name": name, "type": kind}
    if extra is not None:
        d["supplementaryInformation"] = extra
    if default is not None:
        d["defaultValue"] = default
        d["optional"] = True
    if long_description:
        d["longDescription"] = long_description
    return d


ID = p("Id", "Achievement identifier (for example: \"first_coin\")")


def fn(name, kind, full, description, sentence, code, params=(), group="", private=False):
    f = {"fullName": full, "functionType": kind, "name": name, "sentence": sentence, "description": description,
         "group": group, "events": [js(code)], "parameters": list(params), "objectGroups": []}
    if private:
        f["private"] = True
    if kind == "Expression":
        f["expressionType"] = {"type": "expression"}
    if kind == "StringExpression":
        f["expressionType"] = {"type": "string"}
    return f


def lifecycle(name, code, raw=False):
    ev = {"type": "BuiltinCommonInstructions::JsCode", "inlineCode": code, "parameterObjects": "",
          "useStrict": True, "eventsSheetExpanded": False} if raw else js(code)
    return {"fullName": "", "functionType": "Action", "name": name, "sentence": "", "description": "",
            "events": [ev], "parameters": [], "objectGroups": []}


G_SETUP, G_PROGRESS, G_INFO, G_TOAST = "Setup", "Unlock and progress", "Information", "Toast"

FUNCTIONS = [
    lifecycle("onFirstSceneLoaded", (ROOT / "src" / "core.js").read_text(), raw=True),
    lifecycle("onScenePreEvents", "A.preEvents();"),
    lifecycle("onScenePostEvents", "A.postEvents(runtimeScene);"),

    # ------------------------------------------------------------ setup
    fn("DefineAchievement", "Action", "Define an achievement",
       "Define an achievement: its title, description and goal. Do this at the start of the first scene, "
       "before unlocking anything. Use a goal of 1 for an achievement that unlocks in one go, or a bigger goal "
       "(like 10) for one that unlocks when its progress reaches it. Progress is saved on the player's device.",
       "Define achievement _PARAM1_: _PARAM2_ (goal: _PARAM4_)",
       f"A.define({arg('Id')}, {arg('Title')}, {arg('Description')}, {arg('Goal')});",
       [ID, p("Title", "Title"), p("Description", "Description"), p("Goal", "Goal (1 to unlock in one go)", "expression", default="1")],
       G_SETUP),
    fn("ResetAchievement", "Action", "Reset an achievement",
       "Lock an achievement again and set its progress back to 0.",
       "Reset achievement _PARAM1_", f"A.reset({arg('Id')});", [ID], G_SETUP),
    fn("ResetAll", "Action", "Reset all achievements",
       "Lock every achievement again and erase all saved progress. Useful for a \"reset progress\" button or while testing.",
       "Reset all achievements", "A.resetAll();", [], G_SETUP),

    # ------------------------------------------------------------ unlock and progress
    fn("Unlock", "Action", "Unlock an achievement",
       "Unlock an achievement now. Nothing happens if it is already unlocked.",
       "Unlock achievement _PARAM1_", f"A.unlock({arg('Id')});", [ID], G_PROGRESS),
    fn("AddProgress", "Action", "Add progress to an achievement",
       "Add to an achievement's progress. It unlocks when the progress reaches its goal.",
       "Add _PARAM2_ to the progress of achievement _PARAM1_",
       f"A.addProgress({arg('Id')}, {arg('Amount')});",
       [ID, p("Amount", "Amount to add", "expression", default="1")], G_PROGRESS),
    fn("SetProgress", "Action", "Set the progress of an achievement",
       "Set an achievement's progress to a value (for example the best score or the level reached). "
       "It unlocks when the progress reaches its goal. Progress never goes down once the achievement is unlocked.",
       "Set the progress of achievement _PARAM1_ to _PARAM2_",
       f"A.setProgress({arg('Id')}, {arg('Value')});",
       [ID, p("Value", "Progress", "expression")], G_PROGRESS),
    fn("IsUnlocked", "Condition", "Achievement is unlocked",
       "Check if an achievement is unlocked.",
       "Achievement _PARAM1_ is unlocked",
       f"eventsFunctionContext.returnValue = A.isUnlocked({arg('Id')});", [ID], G_PROGRESS),
    fn("JustUnlocked", "Condition", "Achievement was just unlocked",
       "Check if an achievement was just unlocked. This is true for one frame only: use it to play a sound or "
       "give a reward.",
       "Achievement _PARAM1_ was just unlocked",
       f"eventsFunctionContext.returnValue = A.just.includes(String({arg('Id')}));", [ID], G_PROGRESS),
    fn("AnyJustUnlocked", "Condition", "Any achievement was just unlocked",
       "Check if any achievement was just unlocked. This is true for one frame only. "
       "The expression LastUnlocked() tells which one.",
       "Any achievement was just unlocked",
       "eventsFunctionContext.returnValue = A.just.length > 0;", [], G_PROGRESS),

    # ------------------------------------------------------------ information
    fn("Progress", "Expression", "Progress", "The progress of an achievement (0 up to its goal).", "",
       f"eventsFunctionContext.returnValue = A.progress({arg('Id')});", [ID], G_INFO),
    fn("Goal", "Expression", "Goal", "The goal of an achievement.", "",
       f"eventsFunctionContext.returnValue = A.goal({arg('Id')});", [ID], G_INFO),
    fn("ProgressPercent", "Expression", "Progress in percent",
       "The progress of an achievement in percent (0 to 100). Handy for progress bars.", "",
       f"eventsFunctionContext.returnValue = A.percent({arg('Id')});", [ID], G_INFO),
    fn("Count", "Expression", "Number of achievements", "The number of achievements defined.", "",
       "eventsFunctionContext.returnValue = A.order.length;", [], G_INFO),
    fn("UnlockedCount", "Expression", "Number of unlocked achievements",
       "The number of defined achievements that are unlocked.", "",
       "eventsFunctionContext.returnValue = A.unlockedCount();", [], G_INFO),
    fn("IdAt", "StringExpression", "Achievement identifier by position",
       "The identifier of the achievement at a position (0 is the first one defined). "
       "Use it with a Repeat event to build an achievements screen.", "",
       f"eventsFunctionContext.returnValue = A.order[Math.floor(Number({arg('Index')}))] || '';",
       [p("Index", "Position (0 is the first achievement)", "expression")], G_INFO),
    fn("Title", "StringExpression", "Title", "The title of an achievement.", "",
       f"eventsFunctionContext.returnValue = A.def(String({arg('Id')})).title;", [ID], G_INFO),
    fn("Description", "StringExpression", "Description", "The description of an achievement.", "",
       f"eventsFunctionContext.returnValue = A.def(String({arg('Id')})).desc;", [ID], G_INFO),
    fn("LastUnlocked", "StringExpression", "Last unlocked achievement",
       "The identifier of the achievement unlocked most recently in this game session.", "",
       "eventsFunctionContext.returnValue = A.last;", [], G_INFO),

    # ------------------------------------------------------------ toast
    fn("EnableToast", "Action", "Show toasts",
       "Show (or hide) the pop-up that slides in when an achievement is unlocked. It is shown by default.",
       "Show a toast when an achievement is unlocked: _PARAM1_",
       f"A.style.enabled = !!{arg('Enable')};", [p("Enable", "Show toasts", "yesorno", default="yes")], G_TOAST),
    fn("SetToastPosition", "Action", "Toast position",
       "Change where the toast appears on the screen.",
       "Show toasts at the _PARAM1_ of the screen",
       f"A.style.position = String({arg('Position')}) || 'Top';",
       [p("Position", "Position", "stringWithSelector",
          json.dumps(["Top", "Top-left", "Top-right", "Bottom", "Bottom-left", "Bottom-right"]), default='"Top"')],
       G_TOAST),
    fn("SetToastDuration", "Action", "Toast duration",
       "Change how long the toast stays on screen.",
       "Show toasts for _PARAM1_ seconds",
       f"A.style.duration = Math.max(0, Number({arg('Seconds')}) || 0);",
       [p("Seconds", "Duration (in seconds)", "expression", default="3")], G_TOAST),
    fn("SetToastColors", "Action", "Toast colors",
       "Change the colors of the toast.",
       "Toast colors: background _PARAM1_, text _PARAM2_, accent _PARAM3_",
       f"A.setColors({arg('Background')}, {arg('Text')}, {arg('Accent')});",
       [p("Background", "Background color", "color", default='"30;34;51"'),
        p("Text", "Text color", "color", default='"255;255;255"'),
        p("Accent", "Accent color (border, star and label)", "color", default='"255;200;61"')], G_TOAST),
    fn("SetToastLabel", "Action", "Toast label",
       "Change the small label above the title (\"Achievement unlocked\" by default). "
       "Use it to translate the toast, for example \"Pencapaian dibuka\".",
       "Toast label: _PARAM1_", f"A.style.label = String({arg('Label')});",
       [p("Label", "Label")], G_TOAST),
    fn("ShowToast", "Action", "Show the toast of an achievement",
       "Show the toast of an achievement without unlocking it. Useful to preview the toast's look.",
       "Show the toast of achievement _PARAM1_", f"A.queue.push(String({arg('Id')}));", [ID], G_TOAST),
]

EXTENSION = {
    "author": "Luqman Hakeem",
    "category": "Game mechanic",
    "extensionNamespace": "",
    "fullName": "Achievements",
    "gdevelopVersion": ">=5.5.222",
    "helpPath": "",
    "iconUrl": "data:image/svg+xml;base64," + base64.b64encode(ICON_SVG.encode()).decode(),
    "name": NS,
    "previewIconUrl": "https://resources.gdevelop-app.com/assets/Icons/trophy-outline.svg",
    "shortDescription": "Define achievements, unlock them or track their progress, save them on the device, "
                        "and show a toast when one is unlocked.",
    "version": VERSION,
    "description": "\n".join([
        "Add achievements to your game, with no setup.",
        "",
        "- Define each achievement once, at the start of the first scene: an identifier, a title, a description and a goal.",
        "- Unlock it in one go, or add progress (\"collect 10 coins\") and it unlocks when the goal is reached.",
        "- Progress is saved on the player's device automatically.",
        "- A toast slides in when an achievement is unlocked. Change its position, colors, duration and label (to translate it).",
        "- Expressions give the title, description, progress and goal of each achievement, so you can build your own achievements screen.",
        "",
        "Achievements are local to the device: they are not linked to Steam, Game Jolt or another platform.",
    ]),
    "tags": "achievement,achievements,trophy,toast,progress,unlock,reward",
    "authorIds": [],
    "dependencies": [],
    "globalVariables": [],
    "sceneVariables": [],
    "eventsFunctions": FUNCTIONS,
    "eventsBasedBehaviors": [],
    "eventsBasedObjects": [],
}

if __name__ == "__main__":
    out = ROOT / "extension" / f"{NS}.json"
    out.write_text(json.dumps(EXTENSION, indent=2) + "\n")
    print(f"{out.relative_to(ROOT)}: {len(FUNCTIONS)} functions, version {VERSION}")
