#!/usr/bin/env node
// pack-mech.mjs — ships the modelled mech into the game's assets/: mech.glb (Draco, straight from Blender) + the Draco
// decoder (three's wasm build) next to the Basis transcoder, base64 sidecars for file:// (gate + tests), manifest sizes.
// Usage: node pack-mech.mjs        (run after ./run-brain.sh bau_mech.py; reads brain-out/mech.glb)
import { readFileSync, writeFileSync, mkdirSync, copyFileSync, existsSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const HERE = dirname(fileURLToPath(import.meta.url)); const GAME = join(HERE, '..'); const OUT = join(GAME, 'assets');
// Superstandard: bevorzugt die abgeleitete Spiel-Version (≤80k, aus mech-hero), sonst die direkte mech.glb.
const src = existsSync(join(HERE, 'brain-out/mech-game.glb')) ? join(HERE, 'brain-out/mech-game.glb')
  : existsSync(join(HERE, 'mech-game.glb')) ? join(HERE, 'mech-game.glb')
  : existsSync(join(HERE, 'brain-out/mech.glb')) ? join(HERE, 'brain-out/mech.glb') : join(HERE, 'mech.glb');
copyFileSync(src, join(HERE, 'mech.glb')); copyFileSync(src, join(OUT, 'mech.glb'));
mkdirSync(join(OUT, 'draco'), { recursive: true });
const DRACO_SRC = join(GAME, 'node_modules/three/examples/jsm/libs/draco/gltf');
const DRACO = ['draco_wasm_wrapper.js', 'draco_decoder.wasm', 'draco_decoder.js'];
for (const f of DRACO) copyFileSync(join(DRACO_SRC, f), join(OUT, 'draco', f));
const files = ['mech.glb', ...DRACO.map(f => 'draco/' + f)]; const sizes = {}; let sidecar = 0;
for (const rel of files) { const buf = readFileSync(join(OUT, rel)); sizes[rel] = buf.length; const js = `__assetChunk(${JSON.stringify(rel)},"${buf.toString('base64')}");`; writeFileSync(join(OUT, rel + '.b64.js'), js); sidecar += js.length; }
const mf = join(OUT, 'manifest.js'); const m = existsSync(mf) ? JSON.parse(readFileSync(mf, 'utf8').replace(/^window\.__ASSET_MANIFEST=/, '').replace(/;\s*$/, '')) : { files: {} };
Object.assign(m.files, sizes); m.built = new Date().toISOString(); writeFileSync(mf, `window.__ASSET_MANIFEST=${JSON.stringify(m)};`);
console.log(`packed ${files.map(f => `${f} ${(sizes[f] / 1024).toFixed(0)} KB`).join(', ')}; sidecars ${(sidecar / 1024).toFixed(0)} KB; manifest ${Object.keys(m.files).length} files`);
