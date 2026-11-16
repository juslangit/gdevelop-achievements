"""Build help/index.html, the extension's help page (its "help" link in GDevelop).

Usage: python3 tools/build_help.py

The reference tables come from the same FUNCTIONS list as the extension, so the page never drifts from it.
Published on GitHub Pages from the gh-pages branch (see README).
"""
import html
import re
import shutil
from pathlib import Path

from build_extension import EXTENSION, FUNCTIONS, VERSION

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "help"
SHOTS = {"toast.png": "build/shots/ex-hero.png", "toast-malay.png": "build/shots/ex-toast-malay.png"}
PARAM_KIND = {"string": "text", "expression": "number", "yesorno": "yes / no", "color": "color",
              "stringWithSelector": "choice", "imageResource": "image", "audioResource": "sound"}
GROUPS = ["Setup", "Unlock and progress", "Information", "Toast"]


def e(s):
    return html.escape(str(s))


def prose(s):
    """Curly quotes for running text (the extension's own descriptions)."""
    return e(re.sub(r'"([^"]*)"', "\u201c\\1\u201d", str(s)))


def sentence(f):
    """The action's sentence as GDevelop shows it, with the parameter names in place of _PARAMn_."""
    names = [p["description"].split(" (")[0] for p in f["parameters"]]
    return re.sub(r"_PARAM(\d+)_", lambda m: f"<var>{e(names[int(m.group(1)) - 1])}</var>", e(f["sentence"]))


def row(f):
    kind = {"Action": "Action", "Condition": "Condition", "Expression": "Expression",
            "StringExpression": "Text expression"}[f["functionType"]]
    if f["functionType"] in ("Expression", "StringExpression"):
        args = ", ".join(p["name"] for p in f["parameters"])
        shown = f"<code>Achievements::{e(f['name'])}({e(args)})</code>"
    else:
        shown = f"<span class=sentence>{sentence(f)}</span>"
    params = "".join(f"<li><b>{e(p['description'])}</b> <span class=kind>{PARAM_KIND.get(p['type'], p['type'])}"
                     f"{', default ' + e(p['defaultValue']) if p.get('defaultValue') else ''}</span></li>"
                     for p in f["parameters"])
    return (f"<tr><td><span class='tag tag-{kind.split()[-1].lower()}'>{kind}</span></td>"
            f"<td><div class=fname>{e(f['fullName'])}</div>{shown}<p>{prose(f['description'])}</p>"
            f"{'<ul class=params>' + params + '</ul>' if params else ''}</td></tr>")


def reference():
    out = []
    for g in GROUPS:
        fs = [f for f in FUNCTIONS if f.get("group") == g]
        slug = g.lower().replace(" ", "-")
        out.append(f"<h3 id={slug}>{e(g.title().replace(' And ', ' and '))}</h3><table class=ref><tbody>{''.join(row(f) for f in fs)}</tbody></table>")
    return "\n".join(out)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Achievements extension for GDevelop</title>
<meta name="description" content="{short}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#f7f6f2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#14161f" media="(prefers-color-scheme: dark)">
<style>
:root {{ --bg:#f7f6f2; --fg:#1d2030; --muted:#5b6070; --line:#e2e0d8; --card:#ffffff; --accent:#b7790f; --accent-bg:#fff3d6; --code:#f0eee7; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#14161f; --fg:#eceef5; --muted:#a3a8b8; --line:#2b2f3d; --card:#1b1e2a; --accent:#ffc83d; --accent-bg:#2c2614; --code:#232736; }} }}
* {{ box-sizing:border-box; }}
html {{ -webkit-text-size-adjust:100%; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }}
a {{ color:var(--accent); text-underline-offset:3px; text-decoration-thickness:1px; }}
a:hover {{ text-decoration-thickness:2px; color:var(--fg); }}
.skip {{ position:absolute; left:-9999px; top:8px; background:var(--card); padding:8px 12px; border-radius:6px; }}
.skip:focus {{ left:12px; }}
a:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; border-radius:3px; }}
.wrap {{ max-width:880px; margin:0 auto; padding:0 20px; }}
header {{ border-bottom:1px solid var(--line); padding:40px 0 28px; }}
header .eyebrow {{ color:var(--accent); font-weight:600; font-size:.85rem; letter-spacing:.06em; text-transform:uppercase; margin:0; }}
h1 {{ font-size:clamp(2rem,5vw,2.8rem); line-height:1.1; margin:.3em 0 .4em; text-wrap:balance; }}
.lead {{ font-size:1.15rem; color:var(--muted); max-width:62ch; margin:0; }}
nav.toc {{ display:flex; flex-wrap:wrap; gap:6px 18px; margin-top:22px; font-size:.95rem; }}
h2 {{ font-size:1.6rem; margin:2.2em 0 .5em; scroll-margin-top:16px; }}
h3 {{ font-size:1.15rem; margin:1.8em 0 .6em; scroll-margin-top:16px; }}
code, var {{ /* code tokens */ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.88em; }}
code {{ background:var(--code); padding:.1em .35em; border-radius:4px; overflow-wrap:anywhere; }}
var {{ font-style:normal; background:var(--accent-bg); color:var(--fg); padding:0 .3em; border-radius:4px; }}
ol.steps {{ padding-left:1.3em; }} ol.steps li {{ margin:.5em 0; }}
.sentence {{ display:inline-block; background:var(--code); padding:.25em .6em; border-radius:6px; font-size:.95rem; }}
figure {{ margin:1.2em 0; }}
figure img {{ width:100%; height:auto; border-radius:10px; border:1px solid var(--line); display:block; }}
figcaption {{ color:var(--muted); font-size:.9rem; margin-top:.4em; }}
table.ref {{ width:100%; border-collapse:collapse; background:var(--card); border:1px solid var(--line); border-radius:10px; overflow:hidden; }}
table.ref td {{ border-top:1px solid var(--line); padding:14px 16px; vertical-align:top; }}
table.ref tr:first-child td {{ border-top:0; }}
table.ref td:first-child {{ width:120px; }}
table.ref p {{ margin:.5em 0 0; color:var(--muted); font-size:.95rem; }}
.fname {{ font-weight:600; margin-bottom:.3em; }}
.tag {{ display:inline-block; font-size:.75rem; font-weight:600; padding:.15em .55em; border-radius:999px; white-space:nowrap; background:var(--code); }}
.tag-action {{ background:var(--accent-bg); color:var(--accent); }}
ul.params {{ margin:.5em 0 0; padding-left:1.1em; font-size:.92rem; }}
.kind {{ color:var(--muted); }}
@media (max-width:640px) {{ table.ref td {{ display:block; width:auto !important; }} table.ref td:first-child {{ padding-bottom:0; }} table.ref td + td {{ border-top:0; }} }}
.note {{ background:var(--accent-bg); border-left:3px solid var(--accent); padding:12px 16px; border-radius:6px; }}
footer {{ border-top:1px solid var(--line); margin-top:3em; padding:24px 0 40px; color:var(--muted); font-size:.9rem; }}
</style>
</head>
<body>
<a class=skip href="#content">Skip to content</a>
<header><div class=wrap>
  <p class=eyebrow>GDevelop extension · version {version}</p>
  <h1>Achievements</h1>
  <p class=lead>{short}</p>
  <nav class=toc aria-label="On this page">
    <a href="#start">Get Started</a><a href="#toast">The Toast</a><a href="#secret">Secret Achievements</a>
    <a href="#screen">An Achievements Screen</a><a href="#saving">Saving</a><a href="#reference">Reference</a>
  </nav>
</div></header>
<main class=wrap id=content>
  <figure><img fetchpriority="high" src="toast.png" width="1280" height="720" alt="The example game: a list of six achievements, and a toast at the bottom-right saying Achievement unlocked: First Step, with a footprint icon."><figcaption>The example project: an achievements list built with events, and a toast with the achievement's own icon.</figcaption></figure>

  <h2 id=start>Get Started</h2>
  <ol class=steps>
    <li>In GDevelop, open the extension store (Project Manager › Extensions), search <b>Achievements</b> and install it.</li>
    <li>At the beginning of your <b>first scene</b>, define each achievement once:<br>
      <span class=sentence>Define achievement <var>"coin_hunter"</var>: <var>"Coin Hunter"</var> (goal: <var>5</var>)</span><br>
      The identifier is how your events refer to it. Use a goal of 1 for an achievement that unlocks in one go.</li>
    <li>Unlock it in one go: <span class=sentence>Unlock achievement <var>"first_step"</var></span><br>
      or add progress, and it unlocks when the progress reaches the goal:
      <span class=sentence>Add <var>1</var> to the progress of achievement <var>"coin_hunter"</var></span></li>
    <li>Optional: react to it with the condition <span class=sentence>Achievement <var>"coin_hunter"</var> was just unlocked</span>: play a sound, give a reward. It is true for one frame only.</li>
  </ol>
  <p class=note>Use <b>Set progress</b> for numbers you already keep, like the best score or the level reached: <span class=sentence>Set the progress of achievement <var>"high_score"</var> to <var>BestScore</var></span>.</p>

  <h2 id=toast>The Toast</h2>
  <p>A toast slides in when an achievement is unlocked. It needs no object in your scene: the extension draws it on its own layer, above everything else, in 2D and 3D games. When several achievements unlock together, their toasts are shown one after another.</p>
  <ul>
    <li><b>Icon</b>: <span class=sentence>Use image <var>coin.png</var> as the icon of achievement <var>"coin_hunter"</var></span>. Without an icon, the toast shows a star.</li>
    <li><b>Sound</b>: <span class=sentence>Play <var>unlock.ogg</var> (volume: <var>70</var>) when a toast appears</span></li>
    <li><b>Position</b>: top, bottom, or one of the four corners. <b>Duration</b> in seconds. <b>Colors</b>: background, text, and the accent used for the border, star and label.</li>
    <li><b>Label</b>: the small text above the title, “Achievement unlocked” by default. Change it to translate the toast.</li>
    <li><b>Show toasts: no</b> turns the toast off, to show your own instead with “Any achievement was just unlocked”.</li>
  </ul>
  <figure><img loading="lazy" src="toast-malay.png" width="1280" height="720" alt="A green toast with the label Pencapaian dibuka, which is Malay for Achievement unlocked."><figcaption>The label translated to Malay, with custom colors.</figcaption></figure>

  <h2 id=secret>Secret Achievements</h2>
  <p><span class=sentence>Make achievement <var>"curious"</var> secret: <var>yes</var></span> hides its title and description until it is unlocked: the expressions <code>Title</code> and <code>Description</code> give “Secret achievement” and “???” instead (change these with <b>Secret achievement text</b>). The toast shows the real title when it unlocks.</p>

  <h2 id=screen>An Achievements Screen</h2>
  <p>Build your own list with a <b>Repeat</b> event: repeat <code>Achievements::Count()</code> times, and for each position <code>i</code> (a variable from 0), <code>Achievements::IdAt(i)</code> gives the identifier. Use it with <code>Title</code>, <code>Description</code>, <code>Progress</code>, <code>Goal</code>, <code>ProgressPercent</code> for a progress bar, and the condition <b>Achievement is unlocked</b>. The example project has a complete one.</p>

  <h2 id=saving>Saving</h2>
  <p>Progress is saved on the player's device as soon as it changes, in the browser's local storage, under a key with your game's name. It works in web, desktop and mobile exports. Definitions (titles, goals) are not saved: they come from your events every time the game starts, so you can change them in an update. If you make a goal smaller, players who already reached it get the achievement.</p>
  <p>Achievements are local to the device: they are not linked to Steam, Game Jolt or another platform. <b>Reset all achievements</b> erases them, which is handy for a “reset progress” button and while testing.</p>

  <h2 id=reference>Reference</h2>
  <p>Every action, condition and expression, as you find them in GDevelop. <var>Highlighted</var> parts are what you fill in.</p>
  {reference}

  <h2 id=example>Example and Source</h2>
  <p>Download the <a href="https://github.com/juslangit/gdevelop-achievements/releases/latest">example project</a> (open <code>Achievements Example.json</code> in GDevelop). The source, tests and issue tracker are on <a href="https://github.com/juslangit/gdevelop-achievements">GitHub</a>.</p>
</main>
<footer><div class=wrap>Achievements {version} · MIT licence · by {author}. Example sound: “Music Jingles” by Kenney (CC0).</div></footer>
</body>
</html>
"""

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, src in SHOTS.items():
        shutil.copy(ROOT / src, OUT / name)
    page = PAGE.format(short=e(EXTENSION["shortDescription"]), version=VERSION, author=e(EXTENSION["author"]),
                       reference=reference())
    page = page.replace("<code>", '<code translate="no">').replace("<var>", '<var translate="no">')
    (OUT / "index.html").write_text(page)
    print(f"help/index.html: {len(FUNCTIONS) - 3} functions documented")
