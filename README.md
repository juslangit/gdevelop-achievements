# Achievements — a GDevelop extension

Define achievements, unlock them or track their progress, save them on the player's device, and show a
toast when one is unlocked. No objects to add and no setup: install the extension and use its actions.

## Use it

1. In GDevelop: Project Manager > Extensions > Import extension, pick `extension/Achievements.json`
   (once it is in the store: search "Achievements").
2. At the start of your first scene, define each achievement:
   `Define achievement "coin_hunter": "Coin Hunter" (goal: 5)`
3. Unlock it in one go (`Unlock achievement "first_step"`), or add progress
   (`Add 1 to the progress of achievement "coin_hunter"`): it unlocks when the progress reaches the goal.

| Kind | Name |
|---|---|
| Actions | Define an achievement · Unlock · Add progress · Set progress · Reset an achievement · Reset all |
| Toast actions | Show toasts (on/off) · Position (6 places) · Duration · Colors · Label (to translate it) · Show the toast of an achievement |
| Conditions | Is unlocked · Was just unlocked · Any achievement was just unlocked |
| Expressions | `Progress(id)` · `Goal(id)` · `ProgressPercent(id)` · `Count()` · `UnlockedCount()` · `IdAt(i)` · `Title(id)` · `Description(id)` · `LastUnlocked()` |

Progress is kept in the browser's local storage under `GDJS_Achievements_<game name>`, so it works in web,
desktop and mobile exports. Achievements are local: they are not linked to Steam or another platform.

## The example

`example/Achievements Example.json` opens in GDevelop: SPACE to jump, C to find a coin, wait 15 seconds,
B moves the toasts, M translates the toast to Malay, R resets everything. Its events show each feature,
including an achievements screen built with a Repeat event and `IdAt(i)`.

## Work on it

The extension is generated: edit `src/core.js` (the runtime) or `tools/build_extension.py` (the actions,
conditions and expressions), then run

```
tools/build.sh                                              # build, check every instruction, export the example
cd tools && node lib/play.js ../build/example tests/example.json ../build/shots/ex   # play test in headless Chrome
```

`tools/build.sh` must print `instruction problems: 0` and `EXPORT OK diagnostics: 0`.
`tools/` needs `npm install` once.

MIT licence.
