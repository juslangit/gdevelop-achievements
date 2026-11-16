// Usage: node lib/build_html5.js <project.json> <outDir>
// Loads the project with GDevelop's own library, loads its extensions, prints
// any diagnostics (unknown objects, missing behaviors, undeclared variables)
// and exports a playable HTML5 build to outDir.
const path = require('path'), fs = require('fs');
const { loadGD, makeFileSystem, makeCodeWriter, GDJS_ROOT } = require('./gdenv');
(async () => {
  const [projFile, outDir] = process.argv.slice(2);
  const gd = await loadGD();
  const { loadProjectEventsFunctionsExtensions } = require('./loader');
  const project = gd.ProjectHelper.createNewGDJSProject();
  const json = JSON.parse(fs.readFileSync(projFile, 'utf8'));
  const el = gd.Serializer.fromJSObject(json);
  project.unserializeFrom(el);
  project.setProjectFile(path.resolve(projFile));
  // Behaviors need shared data in each scene (the editor adds it when you add a behavior).
  for (let i = 0; i < project.getLayoutsCount(); i++) project.getLayoutAt(i).updateBehaviorsSharedData(project);
  await loadProjectEventsFunctionsExtensions(project, makeCodeWriter(path.join(require('os').tmpdir(), 'GDTMP-ach-code')), { _: s => s });
  // 1. Every instruction must exist and have the right number of parameters.
  const platform = gd.JsPlatform.get();
  let bad = 0;
  // 2. Every number and text expression must be valid in its scene
  //    (known objects, behaviors, functions and declared variables).
  let scoped = null;
  const checkExpr = (value, type, where) => {
    if (value === '') return;
    let root = null;
    if ((type === 'scenevar' || type === 'globalvar') && currentLayout) {
      const rootName = value.split(/[.\[]/)[0];
      const ok = type === 'scenevar' ? currentLayout.getVariables().has(rootName) : project.getVariables().has(rootName);
      if (!ok) { bad++; console.log('VAR', type, rootName, 'is not declared there, in', where); }
      return;
    }
    if ((type === 'variable' || type === 'variableOrProperty' || type === 'variableOrPropertyOrParameter') && scoped) {
      const rootName = value.split(/[.\[]/)[0].trim();
      if (!scoped.getVariablesContainersList().has(rootName)) { bad++; console.log('VAR', rootName, 'is not declared in any scope, in', where); }
      return;
    }
    if (gd.ParameterMetadata.isExpression('number', type)) root = 'number';
    else if (gd.ParameterMetadata.isExpression('string', type)) root = 'string';
    if (!root || !scoped) return;
    const parser = new gd.ExpressionParser2();
    const node = parser.parseExpression(value).get();
    const validator = new gd.ExpressionValidator(platform, scoped, root, '', '');
    node.visit(validator);
    const errs = validator.getAllErrors();
    for (let i = 0; i < errs.size(); i++) { bad++; console.log('EXPR', JSON.stringify(value), '->', errs.at(i).getMessage(), 'in', where); }
    validator.delete(); parser.delete();
  };
  const checkList = (list, isCond, where) => (list || []).forEach(ins => {
    const t = ins.type.value;
    const m = isCond ? gd.MetadataProvider.getConditionMetadata(platform, t) : gd.MetadataProvider.getActionMetadata(platform, t);
    if (gd.MetadataProvider.isBadInstructionMetadata(m)) { bad++; console.log('UNKNOWN', isCond ? 'condition' : 'action', t, 'in', where); }
    else if (m.getParametersCount() !== ins.parameters.length) { bad++; console.log('PARAMS', t, 'expects', m.getParametersCount(), 'got', ins.parameters.length, JSON.stringify(ins.parameters), 'in', where); }
    else ins.parameters.forEach((v, i) => checkExpr(v, m.getParameter(i).getType(), where + ' / ' + t));
    if (ins.subInstructions) checkList(ins.subInstructions, isCond, where);
  });
  // Local variables: like the editor, an event's own variables are in scope for its
  // conditions, actions, loop settings and sub-events.
  const keepAlive = [];
  const withLocals = (e, fn) => {
    if (!e.variables || !e.variables.length || !scoped) return fn();
    const evt = new gd.StandardEvent();
    evt.unserializeFrom(project, gd.Serializer.fromJSObject({ type: 'BuiltinCommonInstructions::Standard', conditions: [], actions: [], variables: e.variables }));
    keepAlive.push(evt);
    const outer = scoped;
    scoped = gd.ProjectScopedContainers.makeNewProjectScopedContainersWithLocalVariables(outer, evt);
    try { fn(); } finally { scoped = outer; }
  };
  const walk = (events, where) => (events || []).forEach(e => withLocals(e, () => {
    if (e.type === 'BuiltinCommonInstructions::ForEachChildVariable') {
      for (const n of [e.iterableVariableName, e.valueIteratorVariableName, e.keyIteratorVariableName].filter(Boolean))
        checkExpr(n, 'variable', where + ' / for each child');
    }
    checkList(e.conditions, true, where); checkList(e.whileConditions, true, where); checkList(e.actions, false, where);
    if (e.repeatExpression) checkExpr(e.repeatExpression, 'expression', where + ' / repeat');
    walk(e.events, where);
  }));
  let currentLayout = null;
  const useScene = name => { currentLayout = project.hasLayoutNamed(name) ? project.getLayout(name) : null; scoped = project.hasLayoutNamed(name) ? gd.ProjectScopedContainers.makeNewProjectScopedContainersForProjectAndLayout(project, project.getLayout(name)) : null; };
  json.layouts.forEach(l => { useScene(l.name); walk(l.events, 'scene ' + l.name); });
  (json.externalEvents || []).forEach(l => { useScene(l.associatedLayout); walk(l.events, 'external ' + l.name); });
  scoped = null;
  // Extensions from GDevelop's store are checked by GDevelop, not here. (Their 3D mappers need the 3D
  // extension, which this older copy of libGD can't load.)
  const STORE = [];
  (json.eventsFunctionsExtensions || []).filter(x => !STORE.includes(x.name)).forEach(x => {
    x.eventsFunctions.forEach(f => walk(f.events, x.name + '.' + f.name));
    (x.eventsBasedBehaviors || []).forEach(b => b.eventsFunctions.forEach(f => walk(f.events, x.name + '.' + b.name + '.' + f.name)));
    (x.eventsBasedObjects || []).forEach(b => b.eventsFunctions.forEach(f => walk(f.events, x.name + '.' + b.name + '.' + f.name)));
  });
  console.log('instruction problems:', bad);
  if (process.argv.includes('--normalize')) {
    const out = new gd.SerializerElement();
    project.serializeTo(out);
    fs.writeFileSync(projFile, JSON.stringify(JSON.parse(gd.Serializer.toJSON(out)), null, 2));
    console.log('normalized', projFile);
  }
  const exporter = new gd.Exporter(makeFileSystem(gd), GDJS_ROOT);
  const opts = new gd.ExportOptions(project, path.resolve(outDir));
  const ok = exporter.exportWholePixiProject(opts);
  if (!ok) console.error('EXPORT FAILED', exporter.getLastError());
  const rep = project.getWholeProjectDiagnosticReport();
  let issues = 0;
  for (let i = 0; i < rep.count(); i++) {
    const r = rep.get(i);
    for (let j = 0; j < r.count(); j++) { const d = r.get(j); issues++; console.log('DIAG', r.getSceneName ? r.getSceneName() : '', d.getMessage(), '| object:', d.getObjectName(), '| expected:', d.getExpectedValue(), '| actual:', d.getActualValue()); }
  }
  console.log(ok ? 'EXPORT OK' : 'EXPORT FAILED', 'diagnostics:', issues);
  process.exit(ok && issues === 0 && bad === 0 ? 0 : 1);
})().catch(e => { console.error(e); process.exit(2); });
