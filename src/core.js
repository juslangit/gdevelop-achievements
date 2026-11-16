// Achievements extension: the runtime core.
// build_extension.py pastes this file into the extension's "onFirstSceneLoaded" function.
// It runs once per game and keeps one Achievements object on the game, shared by every scene.
const game = runtimeScene.getGame();
if (!game.__achievements) {
  const LAYER = '__AchievementsToast';
  const props = game.getGameData().properties || {};
  // Each game keeps its own save, even when several games share one website.
  const KEY = 'GDJS_Achievements_' + (props.name || 'game');

  const toColor = (s, fallback) => {
    s = String(s || '').trim();
    if (/^#?[0-9a-f]{6}$/i.test(s)) return parseInt(s.replace('#', ''), 16);
    const p = s.split(';').map(Number);
    if (p.length === 3 && p.every((n) => n >= 0 && n <= 255)) return (p[0] << 16) | (p[1] << 8) | p[2];
    return fallback;
  };
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const easeOut = (t) => 1 - Math.pow(1 - clamp(t, 0, 1), 3);

  // PIXI v7 and v8 draw shapes differently; support both.
  const roundRect = (g, x, y, w, h, r, color, alpha) => {
    if (typeof g.roundRect === 'function' && typeof g.fill === 'function' && !g.beginFill) g.roundRect(x, y, w, h, r).fill({ color, alpha });
    else { g.beginFill(color, alpha); g.drawRoundedRect(x, y, w, h, r); g.endFill(); }
  };
  const circle = (g, x, y, r, color) => {
    if (typeof g.circle === 'function' && typeof g.fill === 'function' && !g.beginFill) g.circle(x, y, r).fill({ color });
    else { g.beginFill(color, 1); g.drawCircle(x, y, r); g.endFill(); }
  };
  const star = (g, x, y, R, color) => {
    const pts = [];
    for (let i = 0; i < 10; i++) {
      const a = -Math.PI / 2 + (i * Math.PI) / 5, r = i % 2 ? R * 0.45 : R;
      pts.push(x + Math.cos(a) * r, y + Math.sin(a) * r);
    }
    if (typeof g.poly === 'function' && typeof g.fill === 'function' && !g.beginFill) g.poly(pts).fill({ color });
    else { g.beginFill(color, 1); g.drawPolygon(pts); g.endFill(); }
  };
  const makeText = (style) => {
    try { return new PIXI.Text({ text: '', style }); } catch (e) { return new PIXI.Text('', style); }
  };
  // Cut a text with "…" until it fits in maxWidth.
  const fit = (t, str, maxWidth) => {
    t.text = str;
    let s = str;
    while (t.width > maxWidth && s.length > 1) {
      s = s.slice(0, -1);
      t.text = s.trimEnd() + '…';
    }
  };

  const A = {
    defs: {}, // id -> { title, desc, goal }
    order: [], // ids, in the order they were defined
    data: null, // id -> { p: progress, u: unlocked, t: unlock time }, saved in localStorage
    pending: [], // unlocked during this frame
    just: [], // unlocked during the previous frame: what "just unlocked" sees
    last: '',
    queue: [], // toasts waiting to be shown
    toast: null, // { id, start }
    view: null,
    warned: {},
    style: {
      enabled: true, position: 'Top', duration: 3,
      bg: 0x1e2233, fg: 0xffffff, accent: 0xffc83d, label: 'Achievement unlocked',
    },

    load() {
      if (this.data) return;
      this.data = {};
      try {
        const o = JSON.parse(localStorage.getItem(KEY) || '{}');
        if (o && typeof o === 'object' && !Array.isArray(o)) this.data = o;
      } catch (e) {}
    },
    save() {
      try { localStorage.setItem(KEY, JSON.stringify(this.data)); } catch (e) {}
    },
    entry(id) {
      this.load();
      const e = this.data[id];
      if (!e || typeof e !== 'object') this.data[id] = { p: 0, u: false, t: 0 };
      return this.data[id];
    },
    def(id) {
      if (!this.defs[id]) {
        if (!this.warned[id]) { this.warned[id] = true; console.warn('Achievements: "' + id + '" is used but was never defined. Use the action "Define an achievement" first.'); }
        return { title: id, desc: '', goal: 1 };
      }
      return this.defs[id];
    },

    define(id, title, desc, goal) {
      id = String(id);
      if (!id) return;
      if (!this.defs[id]) this.order.push(id);
      this.defs[id] = { title: String(title || id), desc: String(desc || ''), goal: Math.max(1, Number(goal) || 1) };
      // A goal made smaller in an update unlocks it for players who already reached it.
      const e = this.entry(id);
      if (!e.u && e.p >= this.defs[id].goal) this.unlock(id);
    },
    unlock(id) {
      id = String(id);
      if (!id) return;
      const e = this.entry(id);
      if (e.u) return;
      e.u = true;
      e.t = Date.now();
      e.p = Math.max(Number(e.p) || 0, this.def(id).goal);
      this.save();
      this.pending.push(id);
      this.last = id;
      if (this.style.enabled) this.queue.push(id);
    },
    setProgress(id, value) {
      id = String(id);
      if (!id) return;
      const e = this.entry(id);
      if (e.u) return;
      e.p = Math.max(0, Number(value) || 0);
      if (e.p >= this.def(id).goal) this.unlock(id);
      else this.save();
    },
    addProgress(id, amount) {
      id = String(id);
      if (!id) return;
      this.setProgress(id, (Number(this.entry(id).p) || 0) + (Number(amount) || 0));
    },
    reset(id) {
      id = String(id);
      this.load();
      delete this.data[id];
      this.save();
      this.queue = this.queue.filter((q) => q !== id);
      if (this.toast && this.toast.id === id) this.toast = null;
    },
    resetAll() {
      this.data = {};
      this.save();
      this.queue = [];
      this.pending = [];
      this.just = [];
      this.last = '';
      this.toast = null;
    },

    isUnlocked(id) { this.load(); const e = this.data[String(id)]; return !!(e && e.u); },
    progress(id) { this.load(); const e = this.data[String(id)]; return e ? Math.min(Number(e.p) || 0, this.def(String(id)).goal) : 0; },
    goal(id) { return this.def(String(id)).goal; },
    percent(id) { return Math.round((this.progress(id) / this.goal(id)) * 100); },
    unlockedCount() { return this.order.filter((id) => this.isUnlocked(id)).length; },

    // Called before the events of every scene: last frame's unlocks become "just unlocked" for one frame.
    preEvents() {
      this.just = this.pending;
      this.pending = [];
    },

    // ---------------------------------------------------------------- the toast
    layer(scene) {
      if (!scene.hasLayer(LAYER)) {
        scene.addLayer({
          name: LAYER, visibility: true, cameras: [], effects: [], isLightingLayer: false,
          followBaseLayerCamera: false, renderingType: '2d', cameraType: '',
          defaultCameraBehavior: 'top-left-anchored-if-never-moved',
          ambientLightColorR: 200, ambientLightColorG: 200, ambientLightColorB: 200,
        });
      }
      // Keep it above every other layer, including ones created later by events.
      const names = [];
      scene.getAllLayerNames(names);
      if (names[names.length - 1] !== LAYER) scene.setLayerIndex(LAYER, names.length - 1);
      return scene.getLayer(LAYER);
    },
    destroyView() {
      if (!this.view) return;
      const c = this.view.c;
      if (c.parent) c.parent.removeChild(c);
      c.destroy({ children: true });
      this.view = null;
    },
    buildView(scene) {
      this.destroyView();
      const layer = this.layer(scene);
      const c = new PIXI.Container();
      const bg = new PIXI.Graphics(), icon = new PIXI.Graphics();
      const font = 'Arial, Helvetica, sans-serif';
      const label = makeText({ fontFamily: font, fontWeight: 'bold', fontSize: 12 });
      const title = makeText({ fontFamily: font, fontWeight: 'bold', fontSize: 18 });
      const desc = makeText({ fontFamily: font, fontSize: 13 });
      c.addChild(bg, icon, label, title, desc);
      layer.getRendererObject().addChild(c);
      this.view = { scene, c, bg, icon, label, title, desc, key: '' };
    },
    layout(v, id, W, H) {
      const st = this.style, d = this.def(id);
      const s = clamp(H / 720, 0.7, 2.5);
      const w = Math.min(460 * s, W - 24 * s), h = 92 * s, pad = 14 * s, r = 26 * s;
      v.w = w; v.h = h; v.s = s;
      v.bg.clear(); v.icon.clear();
      roundRect(v.bg, 0, 0, w, h, 12 * s, st.accent, 1);
      roundRect(v.bg, 2 * s, 2 * s, w - 4 * s, h - 4 * s, 10 * s, st.bg, 1);
      circle(v.icon, pad + r, h / 2, r, st.accent);
      star(v.icon, pad + r, h / 2 + 1 * s, r * 0.62, st.bg);
      const x = pad + 2 * r + 12 * s, maxW = w - x - pad;
      for (const [t, size, color, alpha] of [[v.label, 14, st.accent, 1], [v.title, 22, st.fg, 1], [v.desc, 15, st.fg, 0.75]]) {
        t.style.fontSize = Math.round(size * s);
        t.style.fill = color;
        t.alpha = alpha;
        t.x = x;
      }
      fit(v.label, st.label, maxW);
      fit(v.title, d.title, maxW);
      fit(v.desc, d.desc, maxW);
      v.label.y = 13 * s; v.title.y = 32 * s; v.desc.y = 61 * s;
    },
    // Called after the events of every scene: shows the toasts one after another.
    postEvents(scene) {
      if (game.isInGameEdition && game.isInGameEdition()) return;
      const now = performance.now();
      if (!this.toast && this.queue.length) this.toast = { id: this.queue.shift(), start: now };
      if (!this.toast) { this.destroyView(); return; }
      if (!this.view || this.view.scene !== scene) this.buildView(scene);
      else this.layer(scene);
      const v = this.view, W = game.getGameResolutionWidth(), H = game.getGameResolutionHeight();
      const key = [this.toast.id, W, H, JSON.stringify(this.style)].join('|');
      if (v.key !== key) { this.layout(v, this.toast.id, W, H); v.key = key; }
      const IN = 350, OUT = 350, HOLD = Math.max(0, this.style.duration) * 1000, t = now - this.toast.start;
      if (t > IN + HOLD + OUT) { this.toast = null; this.destroyView(); return; }
      const k = t < IN ? easeOut(t / IN) : t < IN + HOLD ? 1 : 1 - easeOut((t - IN - HOLD) / OUT);
      const pos = this.style.position, m = 16 * v.s, bottom = /^Bottom/.test(pos);
      v.c.x = /left$/.test(pos) ? m : /right$/.test(pos) ? W - v.w - m : (W - v.w) / 2;
      const on = bottom ? H - v.h - m : m, off = bottom ? H + 4 : -v.h - 4;
      v.c.y = off + (on - off) * k;
    },
    setColors(bg, fg, accent) {
      this.style.bg = toColor(bg, this.style.bg);
      this.style.fg = toColor(fg, this.style.fg);
      this.style.accent = toColor(accent, this.style.accent);
    },
  };
  game.__achievements = A;
}
