// Loads GDevelop's engine library (libGD) in Node, with every built-in JS extension,
// the same way the GDevelop editor does at start-up.
const path = require('path'), fs = require('fs'), os = require('os');
const GDJS_ROOT = '/Applications/GDevelop 5.app/Contents/Resources/GDJS';
async function loadGD() {
  const initGD = require('../vendor/libGD.js');
  const gd = await initGD({ locateFile: f => path.join(__dirname, '../vendor', f), print: () => {}, printErr: () => {} });
  global.gd = gd;
  const platform = gd.JsPlatform.get();
  const extDir = path.join(GDJS_ROOT, 'Runtime/Extensions');
  for (const d of fs.readdirSync(extDir)) {
    const f = path.join(extDir, d, 'JsExtension.js');
    if (!fs.existsSync(f)) continue;
    try {
      const ext = require(f).createExtension(s => s, gd);
      // Include files are relative to the GDJS Runtime folder, like in the editor.
      platform.addNewExtension(ext);
    } catch (e) { console.error('extension failed', d, e.message); }
  }
  return gd;
}
function makeFileSystem(gd) {
  const isURL = p => /^https?:\/\//.test(p);
  const fsx = {
    mkDir: p => { fs.mkdirSync(p, { recursive: true }); return true; },
    dirExists: p => fs.existsSync(p),
    clearDir: p => { if (fs.existsSync(p)) for (const f of fs.readdirSync(p)) fs.rmSync(path.join(p, f), { recursive: true, force: true }); },
    getTempDir: () => path.join(os.tmpdir(), 'GDTMP-ach'),
    fileNameFrom: p => path.basename(p),
    dirNameFrom: p => path.dirname(p),
    makeAbsolute: (f, base) => isURL(f) ? f : path.resolve(path.resolve(base), path.normalize(f)),
    makeRelative: (f, base) => isURL(f) ? f : path.relative(base, path.normalize(f)),
    isAbsolute: p => p.length === 0 || p[0] === '/' || isURL(p),
    copyFile: (s, d) => { try { if (s !== d) { fs.mkdirSync(path.dirname(d), { recursive: true }); fs.copyFileSync(s, d); } return true; } catch (e) { console.error('copyFile', s, d, e.message); return false; } },
    writeToFile: (f, c) => { fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, c); return true; },
    readFile: f => { try { return fs.readFileSync(f, 'utf8'); } catch (e) { return ''; } },
    readDir: (p, ext) => { const out = new gd.VectorString(); ext = ext.toUpperCase(); if (fs.existsSync(p)) for (const f of fs.readdirSync(p)) if (!ext || f.toUpperCase().endsWith(ext)) out.push_back(p + '/' + f); return out; },
    fileExists: p => { try { return fs.statSync(p).isFile(); } catch (e) { return false; } },
  };
  return Object.assign(new gd.AbstractFileSystemJS(), fsx);
}
function makeCodeWriter(dir) {
  fs.mkdirSync(dir, { recursive: true });
  const file = n => path.join(dir, n.replace(/[^A-Za-z0-9_.-]/g, '_') + '.js');
  return {
    getIncludeFileFor: n => file(n),
    writeFunctionCode: async (n, code) => fs.writeFileSync(file(n), code),
    writeBehaviorCode: async (n, code) => fs.writeFileSync(file(n), code),
    writeObjectCode: async (n, code) => fs.writeFileSync(file(n), code),
  };
}
module.exports = { loadGD, makeFileSystem, makeCodeWriter, GDJS_ROOT };
