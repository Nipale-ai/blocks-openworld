// Gate fuer den Open-World-Lauf. Strenger als pruefe_spiel.mjs:
// prueft zusaetzlich HELLIGKEIT (die Falle, in die GLM-5.3 am 01.09. lief)
// und ob die bestellten Kernmechaniken ueberhaupt im Build stecken.
// Aufruf: node pruefe_openworld.mjs <pfad-zu-game.html>
// Exit 0 = GRUEN, Exit 1 = ROT.
import { chromium } from '/Users/niklasplenz/pyriq/content-engine/ki-kanal/capture/node_modules/playwright/index.mjs';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';

const datei = process.argv[2];
if (!datei) { console.log('ROT: kein Pfad uebergeben'); process.exit(1); }

const befunde = [], hinweise = [];
const browser = await chromium.launch({ channel: 'chrome',
  args: ['--autoplay-policy=no-user-gesture-required', '--mute-audio'] });
const seite = await browser.newPage({ viewport: { width: 1280, height: 720 } });
const fehler = [];
seite.on('console', m => { if (m.type() === 'error') fehler.push(m.text()); });
seite.on('pageerror', e => fehler.push(String(e)));

try {
  await seite.goto('file://' + datei, { timeout: 60000 });
} catch (e) { befunde.push('Seite laedt nicht: ' + e.message); }

// grosse Builds brauchen Zeit (GLB-Parse); bis zu 90 s auf ein Canvas warten
let canvas = null;
for (let i = 0; i < 90; i++) {
  canvas = await seite.$('canvas');
  if (canvas) break;
  await seite.waitForTimeout(1000);
}
if (!canvas) befunde.push('Kein <canvas> nach 90 s — Szene startet nicht.');

// Startbildschirm wegklicken, damit gemessen wird was der Spieler sieht
await seite.mouse.click(640, 500).catch(() => {});
await seite.waitForTimeout(1500);
await seite.mouse.click(640, 360).catch(() => {});
await seite.waitForTimeout(6000);

const text = (await seite.textContent('body').catch(() => '')) || '';
if (text.trim().length < 5) befunde.push('Body praktisch leer — kein UI gerendert.');

// --- HELLIGKEIT: die eigentliche Neuerung ---
// Nur der Screenshot misst gueltig. Canvas-Pixel per drawImage liefern ohne
// preserveDrawingBuffer lauter Nullen — das ist keine Messung, sondern ein Irrtum.
const bild = '/tmp/gate-openworld.png';
await seite.screenshot({ path: bild }).catch(() => {});
try {
  // Messung ueber Python/PIL — zuverlaessiger als eine JS-PNG-Bibliothek,
  // und PIL liegt hier ohnehin.
  const roh = execFileSync('python3', ['-c', `
from PIL import Image
import sys, json
im = Image.open("${bild}").convert('L'); w,h = im.size
def mess(y0,y1):
    px = list(im.crop((0,int(h*y0),w,int(h*y1))).getdata()); n=len(px)
    return {"mittel": round(sum(px)/n,1),
            "dunkel": round(100*sum(1 for v in px if v<25)/n,1)}
print(json.dumps({"ganz": mess(0.10,0.92), "unten": mess(0.55,0.90)}))
`], { encoding: 'utf8' });
  const m = JSON.parse(roh);
  hinweise.push(`Helligkeit gesamt: Mittel ${m.ganz.mittel}, ${m.ganz.dunkel}% fast schwarz`);
  hinweise.push(`Helligkeit unten:  Mittel ${m.unten.mittel}, ${m.unten.dunkel}% fast schwarz`);
  if (m.ganz.dunkel > 33)
    befunde.push(`Zu dunkel: ${m.ganz.dunkel}% des Bildes sind fast schwarz (Grenze 33%).`);
  if (m.unten.dunkel > 50)
    befunde.push(`Boden nicht sichtbar: ${m.unten.dunkel}% der unteren Bildhaelfte fast schwarz (Grenze 50%).`);
} catch (e) { befunde.push('Helligkeit nicht messbar: ' + e.message); }

// --- Kernmechaniken: steckt das Bestellte ueberhaupt drin? ---
const quelle = readFileSync(datei, 'utf8');
const nurCode = quelle.length > 4_000_000 ? quelle.slice(0, 2_000_000) + quelle.slice(-2_000_000) : quelle;
const erwartet = [
  [/weapon|waffe/i,                 'Waffen'],
  [/rocket|launcher|rakete/i,       'Raketenwerfer'],
  [/pistol|handgun/i,               'Pistole'],
  [/machine\s?gun|\bmg\b|rifle/i,   'Maschinengewehr'],
  [/vehicle|\bcar\b|drive|driving/i,'Fahrzeuge'],
  [/npc|pedestrian|crowd/i,         'NPCs'],
];
const fehlend = erwartet.filter(([re]) => !re.test(nurCode)).map(([, name]) => name);
if (fehlend.length) befunde.push('Im Build nicht auffindbar: ' + fehlend.join(', '));

const echteFehler = fehler.filter(f => !/net::ERR_INTERNET_DISCONNECTED/i.test(f));
for (const f of echteFehler.slice(0, 8)) befunde.push('Konsolen-Fehler: ' + f.slice(0, 200));

await browser.close();

for (const h of hinweise) console.log('   ' + h);
if (befunde.length) {
  console.log('ROT (' + befunde.length + ' Befunde):');
  for (const b of befunde) console.log(' - ' + b);
  process.exit(1);
}
console.log('GRUEN: laedt, Canvas da, hell genug, Kernmechaniken im Build, keine Konsolen-Fehler.');
process.exit(0);
