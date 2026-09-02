// Gate fuer den Asset-Lauf: prueft, ob GLB-Dateien da und plausibel sind.
// Kein Spiel zu laden — hier zaehlen Dateien, Groessen und Render-Blaetter.
// Aufruf: node pruefe_assets.mjs <phase2-assets-ordner>
import { readdirSync, statSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const ordner = process.argv[2];
if (!ordner || !existsSync(ordner)) { console.log('ROT: Ordner fehlt'); process.exit(1); }

const alle = [];
(function suche(p) {
  for (const e of readdirSync(p, { withFileTypes: true })) {
    const v = join(p, e.name);
    if (e.isDirectory()) suche(v); else alle.push(v);
  }
})(ordner);

const glb = alle.filter(f => /\.(glb|gltf)$/i.test(f));
const bilder = alle.filter(f => /\.(png|jpg|jpeg)$/i.test(f));
const befunde = [];

if (glb.length < 3) befunde.push(`Nur ${glb.length} GLB-Dateien — zu wenig.`);
// Eine GLB unter 20 KB ist fast sicher leer oder abgebrochen
const winzig = glb.filter(f => statSync(f).size < 20000);
if (winzig.length) befunde.push('Verdaechtig kleine GLB: ' +
  winzig.map(f => `${f.split('/').pop()} (${Math.round(statSync(f).size/1024)} KB)`).join(', '));
if (bilder.length < 3) befunde.push(`Nur ${bilder.length} Bilder — die Sichtpruefung fehlt.`);
if (!existsSync(join(ordner, 'NOTES-assets.md'))) befunde.push('NOTES-assets.md fehlt.');

console.log(`   ${glb.length} GLB · ${bilder.length} Bilder · ` +
  `${Math.round(glb.reduce((s,f)=>s+statSync(f).size,0)/1048576)} MB Geometrie`);
for (const f of glb.slice(0, 12))
  console.log(`   ${(statSync(f).size/1048576).toFixed(1).padStart(6)} MB  ${f.split('/').pop()}`);

if (befunde.length) {
  console.log('ROT:'); for (const b of befunde) console.log(' - ' + b);
  process.exit(1);
}
console.log('GRUEN: Assets vorhanden, Render-Blaetter da, Doku da.');
process.exit(0);
