"""Small helpers that write GDevelop 5 project JSON.

The output is close to what the editor saves. tools/lib/build_html5.js then loads it
with GDevelop's own library and writes it back out (--normalize), so the final file
is exactly the editor's format.
"""
import json
import uuid

# ---------------------------------------------------------------- variables


def var(name, value=None, kind=None, children=None):
    """A variable. kind is guessed from the value: str, bool, int/float, dict, list."""
    if kind is None:
        if isinstance(value, bool):
            kind = "boolean"
        elif isinstance(value, (int, float)):
            kind = "number"
        elif isinstance(value, dict):
            kind = "structure"
        elif isinstance(value, list):
            kind = "array"
        else:
            kind = "string"
    v = {"name": name, "type": kind}
    if kind == "structure":
        v["children"] = [var(k, x) for k, x in (value or {}).items()]
    elif kind == "array":
        v["children"] = [dict(var("", x), name="") for x in (value or [])]
        for c in v["children"]:
            c.pop("name")
    else:
        v["value"] = "" if value is None else value
    return v


def vars_(d):
    return [var(k, v) for k, v in d.items()]


# ------------------------------------------------------------------- events


def q(text):
    """A GDevelop string literal: "text"."""
    return json.dumps(text)


def C(t, *params, inverted=False):
    return {"type": {"value": t, **({"inverted": True} if inverted else {})}, "parameters": [str(p) for p in params]}


def NOT(t, *params):
    return C(t, *params, inverted=True)


def A(t, *params):
    return {"type": {"value": t}, "parameters": [str(p) for p in params]}


def OR(*conds):
    return {"type": {"value": "BuiltinCommonInstructions::Or"}, "parameters": [], "subInstructions": list(conds)}


def AND(*conds):
    return {"type": {"value": "BuiltinCommonInstructions::And"}, "parameters": [], "subInstructions": list(conds)}


def ev(conds=(), acts=(), subs=(), local=None):
    e = {"type": "BuiltinCommonInstructions::Standard", "conditions": list(conds), "actions": list(acts)}
    if subs:
        e["events"] = list(subs)
    if local:
        e["variables"] = vars_(local)
    return e


def comment(text):
    return {"type": "BuiltinCommonInstructions::Comment",
            "color": {"r": 255, "g": 230, "b": 109, "textR": 0, "textG": 0, "textB": 0},
            "comment": text}


GROUP_COLOURS = [(74, 176, 228), (228, 151, 74), (120, 200, 120), (190, 120, 220), (230, 110, 110), (200, 200, 90)]


def group(name, events, colour=0, folded=False):
    r, g, b = GROUP_COLOURS[colour % len(GROUP_COLOURS)]
    return {"type": "BuiltinCommonInstructions::Group", "name": name, "source": "", "creationTime": 0,
            "colorR": r, "colorG": g, "colorB": b, "folded": folded, "events": list(events)}


def foreach(obj, conds=(), acts=(), subs=(), local=None):
    e = {"type": "BuiltinCommonInstructions::ForEach", "object": obj,
         "conditions": list(conds), "actions": list(acts)}
    if subs:
        e["events"] = list(subs)
    if local:
        e["variables"] = vars_(local)
    return e


def foreach_child(iterable, value_var, key_var="", conds=(), acts=(), subs=(), local=None):
    e = {"type": "BuiltinCommonInstructions::ForEachChildVariable", "iterableVariableName": iterable,
         "valueIteratorVariableName": value_var, "keyIteratorVariableName": key_var,
         "conditions": list(conds), "actions": list(acts)}
    if subs:
        e["events"] = list(subs)
    if local:
        e["variables"] = vars_(local)
    return e


def repeat(times, conds=(), acts=(), subs=(), local=None):
    e = {"type": "BuiltinCommonInstructions::Repeat", "repeatExpression": str(times),
         "conditions": list(conds), "actions": list(acts)}
    if subs:
        e["events"] = list(subs)
    if local:
        e["variables"] = vars_(local)
    return e


def link(external):
    return {"type": "BuiltinCommonInstructions::Link", "include": {"includeConfig": 0}, "target": external}


# --------------------------------------------------------- common shortcuts
# They keep the event code below readable. Each maps to one GDevelop instruction.

def key_down(k):
    return C("KeyFromTextPressed", "", q(k))


def key_just(k):
    return C("KeyFromTextJustPressed", "", q(k))


def pad_down(button, pad=1):
    return C("Gamepads::C_Button_pressed", "", pad, q(button), "")


def pad_just(button, pad=1):
    return C("Gamepads::IsButtonJustPressed", "", pad, q(button), "")


def obj_str_is(o, v, val, op="="):
    return C("StringObjectVariable", o, v, op, q(val))


def set_obj_str(o, v, val):
    return A("SetStringObjectVariable", o, v, "=", q(val))


def set_obj_str_expr(o, v, expr):
    return A("SetStringObjectVariable", o, v, "=", expr)


def obj_num(o, v, op, val):
    return C("NumberObjectVariable", o, v, op, val)


def set_obj_num(o, v, val, op="="):
    return A("SetNumberObjectVariable", o, v, op, val)


def obj_bool(o, v, val=True):
    return C("BooleanObjectVariable", o, v, "True" if val else "False", "")


def set_obj_bool(o, v, val=True):
    return A("SetBooleanObjectVariable", o, v, "True" if val else "False", "")


def num(v, op, val):
    return C("NumberVariable", v, op, val)


def set_num(v, val, op="="):
    return A("SetNumberVariable", v, op, val)


def str_is(v, val, op="="):
    return C("StringVariable", v, op, q(val))


def set_str(v, val):
    return A("SetStringVariable", v, "=", q(val))


def set_str_expr(v, expr):
    return A("SetStringVariable", v, "=", expr)


def boolv(v, val=True):
    return C("BooleanVariable", v, "True" if val else "False", "")


def set_bool(v, val=True):
    return A("SetBooleanVariable", v, "True" if val else "False", "")


def compare(a, op, b):
    return C("BuiltinCommonInstructions::CompareNumbers", a, op, b)


def timer_reset(o, name):
    return A("ResetObjectTimer", o, q(name))


def timer_over(o, name, secs, op=">="):
    return C("CompareObjectTimer", o, q(name), op, secs)


def anim(o, name_expr):
    return A("SetAnimationName", o, name_expr)


def text(o, expr):
    return A("TextContainerCapability::TextContainerBehavior::SetValue", o, "Text", "=", expr)


def create(o, x, y, layer='""'):
    return A("Create", "", o, x, y, layer)


def delete(o):
    return A("Delete", o, "")


def sound(name, volume=60, pitch=1):
    return A("PlaySound", "", name, "", volume, pitch)


def once():
    return C("BuiltinCommonInstructions::Once")


def scene_start():
    return C("SceneJustBegins", "")


def uid():
    return str(uuid.uuid4())
