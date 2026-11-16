// Usage: node lib/play.js <buildDir> <script.json> <outPrefix>
// Serves an exported build, opens it in headless Chrome, runs a list of steps and prints console errors.
// The first step may set the device: {"device": [width, height], "touch": true}  (default 1280 x 720, no touch).
// Steps (each is an object, keys run in this order):
//   wait: ms                  down / up / press: key            hold: [key, ms]
//   touchDown: [id, x, y]     touchMove: [id, x, y]             touchUp: id
//                             x, y in game pixels on the screen; or [id, "ObjectName", dx, dy] = that object's centre
//   tap: [x, y] or ["ObjectName"]   a quick touch (id 9)
//   click: [x, y]             a mouse click in game pixels
//   until: "js condition"     eval: "js expression" (printed)    shot: "name"
const http = require('http'), fs = require('fs'), path = require('path');
const { chromium } = require('playwright-core');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.ogg': 'audio/ogg', '.wav': 'audio/wav', '.ttf': 'font/ttf', '.css': 'text/css' };
(async () => {
  const [dir, scriptFile, outPrefix] = process.argv.slice(2);
  const steps = scriptFile ? JSON.parse(fs.readFileSync(scriptFile, 'utf8')) : [{ wait: 3000 }, { shot: 'start' }];
  const dev = steps[0].device ? steps.shift() : { device: [1280, 720], touch: false };
  const server = http.createServer((req, res) => {
    const u = decodeURIComponent(req.url.split('?')[0]);
    const p = path.join(dir, u === '/' ? 'index.html' : u);
    fs.readFile(p, (e, data) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' }); res.end(data); });
  }).listen(0);
  const port = server.address().port;
  const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--autoplay-policy=no-user-gesture-required', '--use-gl=angle', '--use-angle=swiftshader'] });
  const context = await browser.newContext({ viewport: { width: dev.device[0], height: dev.device[1] }, hasTouch: !!dev.touch, isMobile: !!dev.touch, deviceScaleFactor: 1,
    // Like a phone preset in Chrome's device toolbar: GDevelop's "Device has a touchscreen" reads the user agent.
    ...(dev.touch ? { userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1' } : {}) });
  const page = await context.newPage();
  const errors = [];
  page.on('console', m => { if ((m.type() === 'error' || m.type() === 'warning') && !/GL Driver|Failed to load resource|creating the session|texture for resource ""/.test(m.text())) errors.push(m.type() + ': ' + m.text()); });
  page.on('response', r => { if (r.status() >= 400 && !/favicon.ico|analytics/.test(r.url())) errors.push('http ' + r.status() + ' ' + r.url()); });
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  await page.addInitScript(() => {
    const t = setInterval(() => {
      if (window.gdjs && gdjs.RuntimeGame && !gdjs.RuntimeGame.prototype.__wrapped) {
        const orig = gdjs.RuntimeGame.prototype.startGameLoop;
        gdjs.RuntimeGame.prototype.startGameLoop = function () { window.__game = this; return orig.apply(this, arguments); };
        gdjs.RuntimeGame.prototype.__wrapped = true; clearInterval(t);
      }
    }, 1);
    window.td = {
      scene: () => window.__game.getSceneStack().getCurrentScene(),
      sv: n => window.td.scene().getVariables().get(n).toJSObject(),
      count: n => window.td.scene().getObjects(n).length,
      res: () => [window.__game.getGameResolutionWidth(), window.__game.getGameResolutionHeight()],
      borders: (l = '') => { const L = window.td.scene().getLayer(l); return [L.getCameraX() - L.getCameraWidth() / 2, L.getCameraY() - L.getCameraHeight() / 2, L.getCameraX() + L.getCameraWidth() / 2, L.getCameraY() + L.getCameraHeight() / 2].map(Math.round); },
      layerVisible: l => window.td.scene().getLayer(l).isVisible(),
      cadet: () => { const c = window.td.scene().getObjects('Cadet')[0]; const v = c.getVariables(); return { x: Math.round(c.getX()), y: Math.round(c.getY()), anim: c.getAnimationName(), dashing: v.get('dashing').getAsBoolean(), aim: Math.round(v.get('aim').getAsNumber()), speed: Math.round(c.getBehavior('TopDownMovement').getSpeed()) }; },
      pos: n => window.td.scene().getObjects(n).map(o => [Math.round(o.getX()), Math.round(o.getY()), Math.round(o.getWidth()), Math.round(o.getHeight())]),
      // Centre of the first object called n, in game pixels on the screen.
      screen: n => { const [nm, k] = n.split('#'); const o = window.td.scene().getObjects(nm)[+(k || 0)]; const L = window.td.scene().getLayer(o.getLayer()); const p = L.convertInverseCoords(o.getCenterXInScene(), o.getCenterYInScene()); return [p[0], p[1]]; },
      gv: n => window.__game.getVariables().get(n).toJSObject(),
      name: () => window.td.scene().getName(),
      texts: n => window.td.scene().getObjects(n).map(o => o.getText()),
    };
  });
  // The exported build shows the "Made with GDevelop" watermark; GDevelop's own preview doesn't, so hide it
  // in screenshots to match what students see in Part 6.
  if (!dev.watermark) await page.addInitScript(() => { const st = document.createElement('style'); st.textContent = '#watermark-background, #watermark-link { display: none !important; }'; document.addEventListener('DOMContentLoaded', () => document.head.appendChild(st)); });
  await page.goto(/^https?:/.test(dir) ? dir : `http://localhost:${port}/index.html`);  // a URL plays the published build
  const touches = new Map();
  const toPage = async (x, y) => page.evaluate(([x, y]) => {
    const c = document.querySelector('canvas').getBoundingClientRect();
    return [c.left + x * c.width / window.__game.getGameResolutionWidth(), c.top + y * c.height / window.__game.getGameResolutionHeight()];
  }, [x, y]);
  const where = async a => {
    if (typeof a[1] === 'string') { const p = await page.evaluate(n => td.screen(n), a[1]); return toPage(p[0] + (a[2] || 0), p[1] + (a[3] || 0)); }
    return toPage(a[1], a[2]);
  };
  // Touches are real TouchEvents dispatched on the canvas, one changed finger per event, like a phone sends them.
  // (CDP's Input.dispatchTouchEvent mixes up which finger was lifted when several are down.)
  const fire = async (type, id) => page.evaluate(([type, id, list]) => {
    const c = document.querySelector('canvas');
    const mk = ([i, [x, y]]) => new Touch({ identifier: i, target: c, clientX: x, clientY: y, pageX: x, pageY: y, radiusX: 5, radiusY: 5, force: 1 });
    const all = list.map(mk), changed = all.filter(t => t.identifier === id);
    const ev = new TouchEvent(type, { bubbles: true, cancelable: true, touches: type === 'touchend' ? all.filter(t => t.identifier !== id) : all,
      targetTouches: type === 'touchend' ? all.filter(t => t.identifier !== id) : all, changedTouches: changed });
    c.dispatchEvent(ev);
  }, [type, id, [...touches.entries()]]);
  const lift = async id => { await fire('touchend', id); touches.delete(id); };
  for (const s of steps) {
    if (s.wait) await page.waitForTimeout(s.wait);
    if (s.touchDown) { touches.set(s.touchDown[0], await where(s.touchDown)); await fire('touchstart', s.touchDown[0]); }
    if (s.touchMove) { touches.set(s.touchMove[0], await where(s.touchMove)); await fire('touchmove', s.touchMove[0]); }
    if (s.touchUp !== undefined) await lift(s.touchUp);
    if (s.tap) { touches.set(9, await where([9, ...s.tap])); await fire('touchstart', 9); await page.waitForTimeout(60); await lift(9); }
    if (s.click) { const p = await toPage(s.click[0], s.click[1]); await page.mouse.click(p[0], p[1]); }
    if (s.down) await page.keyboard.down(s.down);
    if (s.hold) { await page.keyboard.down(s.hold[0]); await page.waitForTimeout(s.hold[1]); await page.keyboard.up(s.hold[0]); }
    if (s.up) await page.keyboard.up(s.up);
    if (s.press) await page.keyboard.press(s.press);
    if (s.until) { try { await page.waitForFunction(s.until, null, { timeout: s.timeout || 5000, polling: 16 }); } catch (e) { console.log('UNTIL timed out', s.until); } }
    if (s.eval) console.log('EVAL', s.eval, '=>', JSON.stringify(await page.evaluate(s.eval)));
    if (s.shot) await page.screenshot({ path: `${outPrefix}-${s.shot}.png` });
  }
  console.log('ERRORS', errors.length); errors.slice(0, 30).forEach(e => console.log('  ' + e));
  await browser.close(); server.close();
})();
