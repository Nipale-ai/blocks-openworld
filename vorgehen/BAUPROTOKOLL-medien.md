# NOTES-medien — Radiosender und Screen-Clips für das Open-World-Spiel (Phase 2, Medien)

Erzeugt am 02.09.2026 auf System A (RTX 5090, ComfyUI 0.33.1): Musik mit **ACE-Step 1.5 Turbo**, Startbilder mit
**Z-Image-Turbo**, Clips mit **LTX-2.5 (I2V, zweistufig)**. Geschnitten, gemessen und encodiert auf dem Mac
(ffmpeg 8, Python-venv in `phase2-medien/.venv`). **Das Spiel wurde nicht angefasst** — alles liegt in `phase2-medien/out/`.
Sperre auf System A: `systema-belegen "model-research"` 12:19–12:40 Uhr, danach `systema-frei`, ComfyUI wieder gestoppt
(war beim Start inaktiv), Keep-awake entfernt.

## 1. Dateien in `out/`

| Datei | Was | Länge | Größe | Format | Loop |
|---|---|---|---|---|---|
| `radio_neon_drive.ogg` | Sender 1 · Synthwave, instrumental (ACE-Step Seed 101) | 51,111 s | 819 262 B (800 KB) | OGG Vorbis q4 (~128 kbps), 48 kHz stereo | ganze Datei, nahtlos (23 Takte @ 108 BPM) |
| `radio_sunset_fm.ogg` | Sender 2 · 80s City Pop **mit weiblichem Gesang** (Seed 201) | 55,862 s | 924 455 B (902 KB) | dito | ganze Datei (27 Takte @ 116 BPM) |
| `radio_blue_note.ogg` | Sender 3 · Late-Night-Jazz-Trio, instrumental (Seed 303) | 51,429 s | 721 125 B (704 KB) | dito | ganze Datei (18 Takte @ 84 BPM) |
| `radio_block_radio.ogg` | Sender 4 · Boom-Bap Hip-Hop **mit Rap** (Seed 504) | 54,783 s | 782 140 B (763 KB) | dito | ganze Datei (21 Takte @ 92 BPM) |
| `radio_stations.js` | ES-Modul: Senderliste mit URLs (Variante A) | – | 981 B | JS | – |
| `radio_stations.b64.js` | Senderliste mit Data-URIs (Variante B, Single-File/file://) | – | 4 330 001 B (4,1 MB) | JS, `window.__RADIO_STATIONS` | – |
| `radio_manifest.json` | dieselbe Liste als JSON (Name, Titel, Datei, Sekunden, Bytes) | – | 1 249 B | JSON | – |
| `screen_billboard_car.webm` | Billboard-Clip: schwarzer Sportwagen in Neon-Regen, Kamera driftet langsam hinein und zurück | 12,000 s (288 Frames) | 1 521 693 B (1,45 MB) | VP9 WebM, 1248×704, 24 fps, ohne Ton | ganze Datei, Ping-Pong (nahtlos) |
| `screen_billboard_car.mp4` | dasselbe als H.264 (Safari/allgemein) | 12,000 s | 2 301 086 B (2,2 MB) | H.264 CRF 20, yuv420p, faststart | dito |
| `screen_billboard_car_poster.jpg` | erstes Frame als Poster/Fallback-Textur | – | 81 303 B | JPEG 1248×704 | – |
| `screen_shop_drink.webm` | Ladenfront-Clip: blaue Getränkedose mit Kondenswasser, Spritzer, Neon-Verlauf | 12,000 s (288 Frames) | 1 101 850 B (1,05 MB) | VP9 WebM, 1248×704, 24 fps, ohne Ton | ganze Datei, Ping-Pong (nahtlos) |
| `screen_shop_drink.mp4` | dasselbe als H.264 | 12,000 s | 1 715 610 B (1,6 MB) | H.264 CRF 20 | dito |
| `screen_shop_drink_poster.jpg` | Poster | – | 47 887 B | JPEG | – |
| `extra/radio_underground.ogg` | **optionaler 5. Sender** · Deep House, instrumental (Seed 404) — nicht in der Standardliste | 54,194 s | 852 691 B (832 KB) | OGG Vorbis q4 | ganze Datei (28 Takte @ 124 BPM) |
| `extra/screen_shop_sneaker.webm` / `.mp4` / `_poster.jpg` | **optionaler 3. Clip** · schwebender Sneaker, dreht sich (Ping-Pong = dreht hin und zurück) | 12,000 s | 1 397 484 B / 1 758 581 B / 62 416 B | wie oben | Ping-Pong |

Summe Standardlieferung (4 OGG + 2 WebM + 2 Poster): ≈ 5,9 MB; mit den MP4-Fassungen ≈ 9,9 MB; die Data-URI-Datei
ersetzt die 4 OGGs (4,1 MB statt 3,2 MB). 1248×704 ist 16:9 auf 0,3 % genau (LTX braucht Vielfache von 32).

Alle Senderdateien sind auf **−16 LUFS integriert** normalisiert (linear, kein Limiter — die Naht bleibt exakt),
True Peak −2,1 … −3,9 dBTP (Extra-Sender −0,7). Gemessen an den fertigen OGGs (`check/audio_final.json`, Spektrogramme in `check/final/`):

| Datei | Peak dBFS | RMS dBFS | LUFS | Musik bis | Stille am Ende | Naht-Fehler ggü. Original |
|---|---|---|---|---|---|---|
| radio_neon_drive.ogg | −2,91 | −16,4 | −16,0 | 51,10 s | 0,01 s | −17,5 dB |
| radio_sunset_fm.ogg | −3,58 | −17,9 | −16,1 | 55,85 s | 0,01 s | −19,6 dB |
| radio_blue_note.ogg | −3,87 | −18,0 | −16,0 | 51,40 s | 0,03 s | −26,1 dB (zwei musikalische Pausen 0,6 s bei 2,2 s und 43,3 s — Jazz-Phrasierung, keine Löcher) |
| radio_block_radio.ogg | −2,40 | −17,8 | −16,1 | 54,75 s | 0,03 s | −34,8 dB |
| extra/radio_underground.ogg | −0,89 | −18,4 | −16,0 | 54,15 s | 0,04 s | −26,6 dB |

(„Stille am Ende" = letzte 10–40 ms unter −35 dB RMS im 50-ms-Fenster — das ist die Auslaufflanke des letzten
Fensters, kein Fade: die Datei endet mitten im Takt und läuft beim Wrap in ihren eigenen Anfang weiter.)

## 2. Senderliste — Namen genau so ins HUD

Das HUD zeigt `${st.name} — ${tr.title}` (`Radio.next()` in `src/audio.js`):

| Reihenfolge (Taste R) | `name` (HUD) | `title` | Datei | Charakter |
|---|---|---|---|---|
| 1 | `NEON DRIVE 104.6` | `Night Grid` | radio_neon_drive.ogg | treibend, Arpeggios, 80er-Drums — die Standard-Nachtfahrt |
| 2 | `SUNSET FM 88.1` | `Take the Long Way Home` | radio_sunset_fm.ogg | hell, funky, **gesungener Refrain** („Drive me through the neon / down where the streetlights bend") |
| 3 | `BLUE NOTE 91.3` | `After Hours` | radio_blue_note.ogg | leise, Besen-Drums, Kontrabass — Tempo raus |
| 4 | `BLOCK RADIO 97.9` | `Seven by Seven` | radio_block_radio.ogg | staubige Drums, **Rap** über die Stadt („seven by seven, that's the only grid I know") |
| (optional 5) | `UNDERGROUND 102.2` | `Basement Pressure` | extra/radio_underground.ogg | 124 BPM, Four-on-the-floor — Club |

Vier Sender, vier klar verschiedene Stimmungen; zwei davon mit echten Vocals. Der fünfte liegt bereit, falls
gewünscht (Deep House überschneidet sich im Puls mit Synthwave — deshalb nicht in der Standardliste).

## 3. Verdrahtung Radio — exakt

Der Hook ist `export const RADIO_STATIONS = []` oben in `src/audio.js`; `class Radio` (Zeilen 304–320) macht alles
Weitere: `next()` stoppt die laufende Quelle, wählt den nächsten Sender, nimmt einen zufälligen Track,
`fetch(tr.data)` → `decodeAudioData` (einmal, dann Cache in `this.buffers`), `AudioBufferSourceNode` mit `loop = true`
→ Gain 0,8 → Bus `radio` (0,55). **Es muss nichts an der Klasse geändert werden**: Die Loops sind so geschnitten, dass
`loop = true` über die ganze Datei richtig ist (`loopStart`/`loopEnd` bleiben Default).

**Variante A — Dateien per URL (http-Server, `node test/*.mjs`, Vite o. ä.):**
1. `cp phase2-medien/out/radio_*.ogg assets/radio/` (vier Dateien).
2. In `src/audio.js` direkt nach `export const RADIO_STATIONS = [];`:
   ```js
   const RADIO_BASE = 'assets/radio/';
   RADIO_STATIONS.push(
     { name: 'NEON DRIVE 104.6', tracks: [{ title: 'Night Grid',              data: RADIO_BASE + 'radio_neon_drive.ogg' }] },
     { name: 'SUNSET FM 88.1',   tracks: [{ title: 'Take the Long Way Home',  data: RADIO_BASE + 'radio_sunset_fm.ogg' }] },
     { name: 'BLUE NOTE 91.3',   tracks: [{ title: 'After Hours',             data: RADIO_BASE + 'radio_blue_note.ogg' }] },
     { name: 'BLOCK RADIO 97.9', tracks: [{ title: 'Seven by Seven',          data: RADIO_BASE + 'radio_block_radio.ogg' }] },
   );
   ```
   (Dieselbe Liste steht fertig in `out/radio_stations.js` als `RADIO_STATION_LIST` mit `RADIO_BASE = 'phase2-medien/out/'`;
   `RADIO_BASE` auf den Zielordner setzen.) Pfade sind relativ zu `game.html`.
3. Fertig — R im Auto zeigt `NEON DRIVE 104.6 — Night Grid`. Der Wechsel dauert beim ersten Mal die Decode-Zeit
   (gemessen 80–370 ms je Sender in Chrome, Abschnitt 6), danach sofort aus dem Cache.

**Variante B — Single-File-`game.html` / `file://` (wie die `assets/*.b64.js`-Sidecars):** `fetch()` auf relative
Dateien ist unter `file://` in Chrome verboten, `fetch('data:audio/ogg;base64,…')` nicht.
1. `out/radio_stations.b64.js` (4,1 MB) vor dem Spiel-Bundle laden: in `src/template.html` ein
   `<script src="phase2-medien/out/radio_stations.b64.js"></script>` oder den Inhalt in `build.mjs` wie das Bundle inlinen.
   Die Datei setzt `window.__RADIO_STATIONS = [ { name, tracks: [{ title, data: 'data:audio/ogg;base64,…' }] }, … ]`.
2. In `src/audio.js` nach der Deklaration: `if (window.__RADIO_STATIONS) RADIO_STATIONS.push(...window.__RADIO_STATIONS);`
   Die Data-URI dient in `Radio.buffers` als Map-Schlüssel — vier Schlüssel à 1 MB, unkritisch.

**Pegel:** −16 LUFS × 0,8 (Track-Gain) × 0,55 (Radio-Bus) ≈ −23 LUFS am Master vor dem Kompressor; das ist
„Radio im Auto", nicht Vordergrund. Wenn es lauter sein soll: `this.gain.gain.value = 0.8` in `Radio.next()` auf 1,0
oder den Bus `radio` von 0,55 auf 0,7 — beides in `src/audio.js`, keine Datei muss neu encodiert werden.

**Browser:** OGG Vorbis decodiert in Chrome/Chromium (auch Playwright) und Firefox gapless — die Naht liegt dann
exakt auf dem letzten → ersten Sample. Safari decodiert kein Vorbis (`decodeAudioData` lehnt ab → der bestehende
`catch` zeigt „NO SIGNAL"). Falls Safari gebraucht wird: `make_loop.py` mit `-c:a aac` neu encodieren
(AAC-Priming-Samples machen die Naht dann ~20 ms unsauber — ZU VERIFIZIEREN, nicht getestet).

**Mehr Tracks je Sender:** `tracks` ist ein Array — weitere Seeds kosten 5 s Generierung + ~800 KB je Track
(`gen_radio.py --stations synthwave --seeds 105,106`, dann `make_loop.py`).

## 4. Verdrahtung Screens — exakt (das Spiel hat noch keinen Video-Hook)

Geprüft: `src/assets.js` (`SIGN`-Tabelle Zeilen 253–262) und `src/lighting.js` kennen nur emissive Farbquads
(Art 1 = feste HDR-Farbe, 2 = Neon, 3 = Ladeneinheit), keine `VideoTexture`, kein `<video>`; `NOTES.md` nennt keinen
Screen-Hook. Die Clips sind deshalb so gebaut, dass sie auf **jedes 16:9-Quad** passen. Vorschlag zum Einbau
(`three` ist im Bundle, alles Weitere ist Standard-three.js):

```js
// einmal pro Clip (nicht pro Instanz): ein <video> + eine VideoTexture, geteilt von allen Screens dieses Clips
function makeScreenMaterial(url, poster) {
  const v = document.createElement('video');
  v.src = url; v.muted = true; v.loop = true; v.playsInline = true; v.preload = 'auto'; v.crossOrigin = 'anonymous';
  const tex = new THREE.VideoTexture(v);
  tex.colorSpace = THREE.SRGBColorSpace; tex.minFilter = THREE.LinearFilter; tex.magFilter = THREE.LinearFilter; tex.generateMipmaps = false;
  const mat = new THREE.MeshBasicMaterial({ map: tex, toneMapped: false });   // unlit: leuchtet in der blauen Stunde von selbst
  mat.color.setScalar(1.6);                                                    // > Bloom-Schwelle, damit der Screen glüht wie die Neon-Schilder
  const play = () => v.play().catch(() => {});                                 // erst nach der Start-Klick-Geste (main.js „start screen")
  return { mat, video: v, play };
}
const bill = makeScreenMaterial('assets/screens/screen_billboard_car.webm');
const quad = new THREE.Mesh(new THREE.PlaneGeometry(8, 4.5), bill.mat);       // 16:9, 8 × 4,5 m
```
- **Wo:** z. B. als Dachplakat auf `shop_row` — der Trim-Kasten `box(10, 2, 0.5, 8, 9.5, 6.5)` ist 5:1; ein 8×4,5-m-Quad
  darüber bei lokal (8, 11.3, 6.6), Normale +Z (`facing 'z+'`, wie die Schilder), oder ein eigener Billboard-Mast am
  Plaza-Rand. `screen_shop_drink` als Bildschirm **in** den Ladeneinheiten (Art 3, 8,6 × 2,4 m): Quad 3,2 × 1,8 m bei y 1,6,
  z 7,25 (2 cm vor dem Glas). Das sind Vorschläge — Position bestimmt, wer verdrahtet.
- **Starten:** `bill.play()` im Start-Klick-Handler (dort, wo `audio.resume()` läuft). Muted-Autoplay ist erlaubt,
  aber vor der Geste verweigert Chrome `play()` gelegentlich — deshalb dort aufrufen.
- **`file://`:** `<video src="…webm">` lädt relative Dateien auch unter `file://` (Media-Elemente sind nicht an das
  fetch-Verbot gebunden). Für ein reines Single-File-Build den Clip als `data:video/webm;base64,…` in `v.src` setzen
  (WebM 1,05–1,45 MB → 1,4–1,95 MB Base64).
- **WebM zuerst, MP4 als Fallback:** Playwright-Chromium hat kein H.264 (Lehre aus dem Neon-Warden-Lauf), deshalb
  ist VP9 die Standarddatei; `v.canPlayType('video/webm; codecs="vp9"')` prüfen, sonst `.mp4`.
- **Loop:** `v.loop = true` über die ganze Datei; die Clips sind Ping-Pong (vorwärts + rückwärts, Endframes nicht
  doppelt), der letzte Frame geht in den ersten über wie jeder andere Frame-Schritt (gemessen: Naht-Diff 1,2 / 0,7 bei
  Frame-Diff-Median 1,2 / 0,5 — siehe unten).
- **Kosten:** eine VideoTexture = ein Textur-Upload pro Frame (1248×704 RGBA ≈ 3,5 MB → ~85 MB/s bei 24 fps); zwei Clips
  sind unkritisch, hundert Instanzen desselben Materials kosten nichts extra. `tex.needsUpdate` setzt three selbst.

## 5. Erzeugt, geprüft, verworfen

**Musik (ACE-Step 1.5 Turbo, 64 s, 8 Steps, CFG 1, alle als FLAC in `raw/`):** 5 Genres × 4 Seeds = 20 Tracks, je 4–6 s
Generierung. Messung `check/audio_raw.json`, Spektrogramme `check/radio_*.png` — angesehen für jeden Kandidaten, der in
die engere Wahl kam. Befund, der die Auswahl bestimmt hat: **jeder Track endet vor 64 s in harter Stille** (Musik bis
46–62 s), drei haben zusätzlich Löcher mittendrin. Darum wird nie die Rohdatei geliefert, sondern ein Loop aus ganzen
Takten, der vor dem Musik-Ende endet.

| Kandidat | Musik bis | Befund | Entscheidung |
|---|---|---|---|
| synthwave s101 | 52,9 s | dicht, gleichmäßig | **genommen** (Loop 0,195–51,306 s) |
| synthwave s102 | 46,4 s | fünf Löcher ab 39,8 s | verworfen |
| synthwave s103 | 54,0 s | ok, Naht-Fehler −12,6 dB (schlechtester Wert) | verworfen (s101 sauberer) |
| synthwave s104 | 55,5 s | 0,5 s Stille am Anfang → läge im Loop | verworfen |
| citypop s201 | 61,8 s | **Gesang: Whisper (small.en) liest Strophe + Refrain fast wörtlich** | **genommen** (0,26–56,122 s) |
| citypop s202–s204 | 59–61 s | Whisper erkennt keinen Text — Vocals fehlen oder sind Gemurmel | verworfen |
| jazz s301 | 56,8 s | Loch 54,35–54,9 s, Naht-Fehler −19 dB | verworfen |
| jazz s302 | 57,3 s | sechs Löcher (0,85 s, 22,8 s, 45,4 s …) | verworfen |
| jazz s303 | 55,6 s | sauberes Trio, Naht −26 dB | **genommen** (2,783–54,211 s; erster Takt = Einzähler übersprungen) |
| jazz s304 | 56,3 s | ebenfalls sauber (Naht −29,6 dB), 0,1 % Clipping | Reserve |
| house s401 | 61,3 s | Löcher bei 1,6 s, 40 s, 59 s | verworfen |
| house s402 | 61,6 s | 15 s gefilterter Intro, danach voll | Reserve (Loop ab Takt 8, 46 s) |
| house s403 | 61,0 s | ok, True Peak −0,1 dBTP nach Normalisierung | verworfen (zu heiß) |
| house s404 | 61,0 s | dicht, Naht −26,6 dB | **Extra-Sender** |
| hiphop s501 | 61,2 s | Rap nur teilweise verständlich | verworfen |
| hiphop s502 | 62,4 s | kein Text erkannt | verworfen |
| hiphop s503 | 61,7 s | Rap fast wörtlich, Loop beginnt bei 2,4 s | Reserve |
| hiphop s504 | 59,6 s | **Rap nahezu wörtlich** („Blue hour, low ride, cruising down the boulevard …"), Naht −34,8 dB | **genommen** (0,49–55,273 s) |

Gesangs-Beleg: `check/whisper/*.small.txt` (Rohdateien) und `check/whisper/*.final.txt` (die gelieferten Loops;
whisper.cpp, `ggml-small.en`). Am fertigen `radio_sunset_fm.ogg` liest Whisper Strophe und Refrain direkt; am fertigen
`radio_block_radio.ogg` erst mit 6 dB Vorverstärkung oder Beam-Suche 5 („Blue hour, low ride, cruisin' down the
boulevard … Roll through the city, keep the radio on") — Whisper-Empfindlichkeit bei −16 LUFS, nicht das Audio.
**`ggml-large-v3` halluziniert auf Musik** („Thank you.", „Bye.") und wurde als Prüfwerkzeug verworfen.

**Loop-Schnitt (`make_loop.py`):** Beat-Phase und Taktanfang per Onset-Raster bei bekanntem BPM; Loop = ganze Takte
[a, b), b so spät wie möglich vor dem Musik-Ende (Reserve 1 Beat + 50 ms); Anfang des Loops = 1 Beat Blende von der
natürlichen Fortsetzung nach b in den Kopf ab a, Rest Original → beim Wrap läuft die Musik weiter, kein Fade-out.
Naht geprüft mit `verify_loop.py` (Wrap der decodierten OGG gegen die Original-Fortsetzung, Sample-Alignment ±120):
Fehler −17 … −35 dB relativ = Vorbis-Rauschteppich, kein Sprung (`check/loops/*_naht.png`).

**Stills (Z-Image-Turbo, 1280×704, Seed 7, ~5 s):** Auto-Billboard, Getränkedose, Sneaker — alle drei ohne Text/Logo
(Prompt verbietet es, Bild geprüft), alle drei weiterverwendet.

**Clips (LTX-2.5 I2V, 1280×704, 145 Frames = 6 s, 24 fps, strength1 1,0, 5 Stage-2-Sigmas, ohne Ton, 30–40 s je Clip):**
`check/clip_*_sheet.png` (12 Frames) und `check/clip_*_metrik.png` angesehen: kein Grau-Kollaps (Streuung 42–63),
kein Flackern (Frame-Diff max 1,5 / 0,8 / 3,2 bei Median 1,2 / 0,5 / 2,5), Auto und Dose bleiben scharf, der Sneaker
dreht sich einmal um die Achse.

**Loop-Verfahren fürs Video — drei Varianten gebaut, eine behalten:**
- Crossfade Schwanz→Kopf (0,75 s): Dose ok-ish, **Sneaker mit deutlicher Doppelkontur** über 18 Frames
  (am Wrap-Streifen des ersten Baus angesehen; der Streifen wurde vom Ping-Pong-Bau überschrieben, die
  Crossfade-Fassungen selbst liegen nicht mehr in `out/`) → verworfen.
- Frame-Matching (Schnitt am Frame, der Frame 0 am ähnlichsten ist, 4 Frames Blende): Sneaker kehrt nie zur
  Startpose zurück (beste Differenz 38,9 bei Median 42,8 → harter Schnitt, Flacker-Frames 93–95); Dose 18,0/21,3 → verworfen
  (`check/loops/*_match.*`).
- **Ping-Pong** (vorwärts + rückwärts, 2n−2 = 288 Frames): Naht-Diff 1,2 (Auto), 0,7 (Dose), 1,3 (Sneaker) = ein normaler
  Frame-Schritt, Flackern 0 → **genommen**. Beim Auto und der Dose unsichtbar (Kameradrift bzw. Tropfen); beim Sneaker
  dreht sich der Schuh hin und wieder zurück — deshalb nur als `extra/`.

Prüfwerte der gelieferten Loops (`check/video_out.json`, `check/screen_*_sheet.png`, `_metrik.png`, `_wrap.png`):

| Datei | Frames | Mittelwert | Streuung | Frame-Diff Median/Max | Flacker-Frames | Naht-Diff |
|---|---|---|---|---|---|---|
| screen_billboard_car.webm | 288 | 67,6–73,1 | 60,7–63,3 | 1,21 / 1,62 | keine | 1,2 |
| screen_shop_drink.webm | 288 | 66,3–81,2 | 57,0–58,2 | 0,54 / 1,02 | keine | 0,7 |
| extra/screen_shop_sneaker.webm | 288 | 54,2–68,2 | 42,1–48,8 | 2,48 / 2,94 | keine | 1,3 |

## 6. Browser-Nachweis (System-Chrome via Playwright, `test/verify_browser.mjs`, Ergebnis `check/browser_verify.json`)

Dieselben Schritte wie `Radio.next()` — `fetch` → `decodeAudioData` → `AudioBufferSourceNode` mit `loop = true` — in einem
`OfflineAudioContext` gerendert, einmal bei 48 kHz und einmal bei 44,1 kHz (falls der Spiel-`AudioContext` auf einem
44,1-kHz-Gerät läuft, resampelt Chrome beim Decode). Plus `<video loop>` für die Clips und die Data-URI-Variante unter `file://`.

| Datei | Decode-Länge = ffmpeg | Dauer im Browser | Decode | Wrap-Sprung / typischer Sample-Sprung | Neustart nach Wrap | Kanten (RMS erste/letzte 20 ms) |
|---|---|---|---|---|---|---|
| radio_neon_drive.ogg | ✓ 2 453 333 Samples | 51,111 s | 143 ms | 0,111 / 0,0054 — identisch mit dem Original an Takt b (0,137): Sägezahn-Synth + Kick auf der Eins, kein Artefakt | Fehler 0 | 0,111 / 0,135 (Mitte 0,123) |
| radio_sunset_fm.ogg | ✓ 2 681 379 | 55,862 s | 372 ms | 0,111 / 0,0095 — Original an Takt b 0,188 | 0 | 0,089 / 0,081 |
| radio_blue_note.ogg | ✓ 2 468 571 | 51,429 s | 86 ms | 0,0029 / 0,0014 | 0 | 0,035 / 0,035 |
| radio_block_radio.ogg | ✓ 2 629 565 | 54,783 s | 82 ms | 0,0053 / 0,0063 | 0 | 0,087 / 0,106 |
| extra/radio_underground.ogg | ✓ 2 601 290 | 54,194 s | 184 ms | 0,047 / 0,0030 — Sprünge dieser Größe kommen 110 000× im Track vor (Bass) | 0 | 0,192 / 0,045 |

Bei 44,1 kHz: Längen 2 253 999 / 2 463 516 / 2 267 999 / 2 415 912 Samples (exakt Dauer × 44 100), Wrap-Sprünge gleich,
Neustart-Fehler 0, Decode 280–370 ms. Die Decode-Ränder sind nicht abgeschwächt (Vorbis-Priming wird von Chrome korrekt
verworfen) — der Loop ist im echten Decoder so nahtlos wie in der Messung mit ffmpeg.

Data-URI-Variante (`radio_stations.b64.js`): alle vier Sender über `fetch('data:audio/ogg;base64,…')` decodiert,
gleiche Längen, Decode 119–134 ms. Unter `file://` blockiert Chrome `fetch('radio_neon_drive.ogg')` (CORS, Origin null) —
die Data-URI decodiert dort trotzdem (Sender 1 geprüft), `<video src="screen_billboard_car.webm">` lädt und loopt
(Bildinhalt unter `file://` nicht messbar, Canvas ist „tainted").

Video über http: alle fünf Dateien (2 WebM, 2 MP4, Extra-WebM) 1248×704, Dauer 12,000 s, spielen (Luminanz 54–72 nach 1,5 s),
springen am Ende auf den Anfang (`loop`), kein `ended`; 0–5 verworfene Frames von ~70 = Headless-Timing, nicht Inhalt.
Hinweis: System-Chrome hat H.264; das Playwright-Chromium des Spiels (`test/*.mjs` nutzt `channel: 'chrome'`, also
ebenfalls System-Chrome) — für reines Chromium bleibt WebM die sichere Wahl.

## 7. Wiederholen

Reihenfolge (alle Skripte in `phase2-medien/`, Python aus `.venv` mit numpy/pillow/matplotlib; ffmpeg/ffprobe, whisper-cli):
1. `systema-belegen "model-research" "…" 45` · auf System A `touch ~/.systema-keep-awake; systemctl --user start comfyui.service` · Tunnel `ssh -f -N -L 8188:127.0.0.1:8188 systema`.
2. `python3 gen_radio.py` (alle Sender, 4 Seeds) — Tags/BPM/Tonart/Lyrics stehen in `STATIONS`, Lyrics in `prompts/lyrics_*.txt`.
3. `python3 analyze_audio.py raw/radio_*.flac --png-dir check --json check/audio_raw.json` → Spektrogramme **ansehen**.
4. `python3 make_loop.py raw/<flac> check/loops/<name>.ogg --bpm <bpm> [--skip-bars n]` → `verify_loop.py` mit `--end`/`--gain-db` aus der JSON-Ausgabe.
5. Gesang: `whisper-cli -m ~/.cache/hyperframes/whisper/models/ggml-small.en.bin -f <16-kHz-mono.wav>`.
6. `python3 gen_screens.py stills --seed 7` → Bilder ansehen → `python3 gen_screens.py clips --still raw/<png> --name <name> --seed <n> --seconds 6`.
7. Nach dem letzten GPU-Schritt: `systemctl --user stop comfyui.service; rm ~/.systema-keep-awake` auf System A, `systema-frei "model-research"`.
8. `python3 check_video.py raw/clip_*.mp4 --png-dir check` → Kontaktbögen ansehen → `python3 make_video_loop.py raw/<mp4> out/<name> --mode pingpong`.
9. `python3 build_out.py` (Auswahl in `FINAL`/`EXTRA`) → `out/` inkl. `radio_stations.js`, `radio_stations.b64.js`, `radio_manifest.json`.
10. `node test/verify_browser.mjs` → Decode, Loop-Wrap, Video-Loop und Data-URI in System-Chrome nachweisen (`check/browser_verify.json`).

Lizenz/Herkunft: ACE-Step 1.5 (MIT), LTX-2.5 distilled, Z-Image-Turbo — alle Ausgaben lokal auf eigener Hardware erzeugt,
Lyrics selbst geschrieben (`prompts/lyrics_*.txt`), keine Stock-Inhalte. Technisch-organisatorische Angabe, keine Rechtsberatung.
