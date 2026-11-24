#!/usr/bin/env node
/* gdmp-master one-command installer for a VERSIONED OPS KNOWLEDGE PACKAGE.
 * GDMP has no AI Skill runtime: this copies knowledge files only.
 * Usage: gdmp-master | --check-only | --uninstall
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const pkgRoot = path.resolve(__dirname, '..');
const src = pkgRoot;
function targets() {
  const env = process.env.OPENCODE_SKILLS_DIR || process.env.OINK_SKILLS_DIR;
  return env ? [env] : [path.join(os.homedir(), '.config', 'opencode', 'skills'), path.join(process.cwd(), '.opencode', 'skills')];
}
function check() {
  if (!fs.existsSync(path.join(src, 'SKILL.md'))) throw new Error('SKILL.md missing in package');
  const txt = fs.readFileSync(path.join(src, 'SKILL.md'), 'utf8');
  if (!/^---\n[\s\S]*?\n---\n/.test(txt) || !/name:\s*gdmp-master/.test(txt)) throw new Error('frontmatter invalid');
  return true;
}
function copyDir(a, b) {
  fs.mkdirSync(b, { recursive: true });
  for (const e of fs.readdirSync(a, { withFileTypes: true })) {
    const s = path.join(a, e.name), d = path.join(b, e.name);
    if (e.isDirectory()) copyDir(s, d);
    else if (!e.name.startsWith('.install')) fs.copyFileSync(s, d);
  }
}
function main() {
  check();
  if (process.argv.includes('--check-only')) { console.log('gdmp-master: package OK (knowledge package; AI execution NOT enabled)'); return; }
  const dests = targets();
  if (process.argv.includes('--uninstall')) {
    for (const d of dests) { const t = path.join(d, 'gdmp-master'); if (fs.existsSync(t)) { fs.rmSync(t, { recursive: true, force: true }); console.log('removed', t); } }
    return;
  }
  const dir = dests.find(d => fs.existsSync(d)) || dests[0];
  const target = path.join(dir, 'gdmp-master');
  copyDir(src, target);
  console.log('installed gdmp-master KNOWLEDGE PACKAGE ->', target);
  console.log('NOTE: GDMP has no AI Skill runtime; files installed != AI execution enabled.');
}
try { main(); } catch (e) { console.error('gdmp-master install failed:', e.message); process.exit(1); }
