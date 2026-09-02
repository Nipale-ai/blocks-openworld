# BLOCKS — open world, phase 1 graybox (+ round 2: police, camera, dynamism · round 3: the blue-hour look · round 4: the real assets · round 5: radio and screens · round 6: the baked lightmaps applied) handover notes

A folder since round 4: `game.html` (three r180 inlined) plus `assets/` next to it (six compressed GLB families, KTX2 textures,
base64 sidecars for `file://`). Runs from `file://` (double-click) and over http. Built 2026-09-01/02 on the Mac; the Blender
assets came from System A in a separate phase (`phase2-assets/`). Sections 1–8 are the phase-1…3 handover, **section 9 is round 4:
how the assets are packed and loaded, what was retuned for them, what it costs and what still looks weak.**

**Round 2 (2026-09-02) in one paragraph:** the driving camera was rebuilt after a real bug (section 4, "Driving
camera") and now has a headless test that fails if the player's car ever leaves the frame; a full wanted system
with 1–5 stars, marked cruisers, sirens, light bars, officers on foot, roadblocks and evasion replaced the old
"heat" value (section 4, "Police and wanted stars"); and a dynamism layer was added on top (section 4, "Dynamism").
Nothing in the city layout, vehicle physics, weapon wheel or character controller was rewritten.

**Round 4 (2026-09-02, real assets) in one paragraph:** every placeholder factory in `src/assets.js` now returns the Blender GLB
(same names, pivots and child objects — gameplay code is untouched, one main-loop hook picks LODs). `pack-assets.mjs` merges the 22
source GLBs into six families, drops what the game never reads, compresses geometry with Meshopt (positions kept float so wheel pivots
and instanced prototypes stay exact), textures with KTX2/Basis (UASTC normals and hero albedos, ETC1S the rest, full mip chains) and
writes `assets/` (20.2 MB → 5.9 MB) plus base64 sidecars so the same bytes load from `file://`. `src/loader.js` streams them with byte
progress before the city is built; a click during loading starts the game the moment it is ready. Section 9.

**Round 3 (2026-09-02, look only) in one paragraph:** the city moved from flat daylight to the blue hour. A new module
`src/lighting.js` carries every artificial light in two float textures and a world-space cell grid that every
MeshStandardMaterial reads per fragment (section 8) — 596 static lights (street lamps, shopfronts, neon, canopy, wall
packs, porch lights) plus up to ~60 dynamic ones per frame (headlights, tail/brake lights, police flashes and sweeping
beams, muzzle flashes, explosions) — and there is no `THREE.PointLight` left in the scene. On top: hash-lit windows,
neon and shop emissives, glow sprites, headlight pools on the road, a wet-asphalt road material, blob shadows and AO
skirts, a blue-hour sky that also feeds the environment map, and a colour grade in `postfx.js`. Gameplay code is
untouched except for three read-only hooks (section 8.6). The build got *faster* (4.1 ms uncapped at the spawn view
against 5.6 ms in round 2) because the eight three.js point lights of round 2 were more expensive than the grid.

## 1. Running, rebuilding, testing

- Open `game.html` in Chrome. Click → pointer lock → play. `H` toggles the control strip, `Esc` releases the mouse (overlay returns with "Click to resume").
- **Round 4:** `node pack-assets.mjs` rebuilds `assets/` from `phase2-assets/out/*.glb` (needs the gltf-transform 4.5 npx cache and `ktx` 4.4 — section 9.1); then `node build.mjs --minify`. Ship `game.html` + `assets/` together. `node test/quick.mjs [--http]` is the 25-s smoke test, `node test/viewer.mjs <glb> [--node=…] [--dump]` renders any GLB headless with a node/attribute dump, `node test/vehicles-shots.mjs` drives every car type and takes asset close-ups, `node test/probe-perf.mjs` toggles scene parts for frame-time attribution.
- Source lives in `src/` (ES modules). `node build.mjs [--minify]` bundles `src/main.js` with esbuild (`/Users/niklasplenz/stucklenz-website/node_modules/.bin/esbuild`) into `lib/main.bundle.js` and splices it into `src/template.html` → `game.html`. `node_modules/three` is a symlink to the r180 package of the earlier run (`../2026-09-01_20-51-spiel-fable/node_modules/three`).
- Headless tests (Playwright from `~/pyriq/content-engine/ki-kanal/capture/node_modules/playwright`, real Chrome via `channel: 'chrome'`, Metal via `--use-angle=metal`; without it headless Chrome renders with SwiftShader at ~3 fps):
  - **`node test/camera.mjs`** — the driving-camera invariant ("the player's own car is always clearly in frame"). Twelve scripted scenarios: boulevard weave through the median trees, head-on into a facade, reversing into it, hugging a facade, a 3.5 m alley, being rammed from behind and from the side, handbrake spins, mouse orbit with pitch extremes, reverse-view toggling, the gas-station canopy, the stunt ramp, driving in traffic. Every rendered frame projects the car's 8 box corners and 5 occlusion probes; a frame is bad if the car centre leaves ±0.85 NDC, fewer than 4 corners are inside, 3+ probes are occluded by statics, or the camera sits inside the car / a building / the ground / a tree crown. **Fails (exit 1) when any scenario has more than 6 consecutive bad frames (~100 ms).** `--only=<scenario> --dump` prints the offending frames. Keep this test.
  - **`node test/police.mjs`** — wanted-system play-through: fire in public on foot → 1★ → time until a cruiser is within 60 m, line of sight, an officer gets out and fires; kill the officer → 3★+, cover behaviour; a 3★ chase in the muscle car (cruisers within 40 m, rams on the player car, roadblocks); a 5★ chase (unit count, fps, draws); hide in the industrial column → stars drop → "LOST THEM". Exit 1 on any failed check. Traffic and spawns are random, so a single failure is rerun before it counts.
  - `node test/play.mjs [--gpu]` — phase-1 play-through (walk/sprint/jump, enter/drive/exit, weapon wheel, three weapons, get shot at), screenshots + brightness.
  - **`node test/media.mjs [--http]`** — round 5: radio + screens (analysers on the audio graph per station, leave / re-enter, mute, radio under the engine, both clips decoding and advancing, HUD screenshots into `shots/media/`). Exit 1 on any failed check.
  - `node test/drive.mjs` · `node test/feel.mjs` · `node test/audio.mjs` · `node test/overview.mjs` · `node test/npcfire.mjs` — as in phase 1 (vehicle telemetry, uncapped frame time / camera jitter / props, offline audio render, composition shots, hostile sanity).
  - **`node test/look.mjs [--only=name,…]`** — the round-3 look check: spawn view, a look to the left, the free-cam overviews (`ov_*`), a shop street, the gas station, driving + braking, an explosion flash; every shot is measured like the gate (mean luminance, % near-black) and console errors fail it. `shots/before/` holds the round-2 daylight versions of the same viewpoints for the before/after.
  - `node test/beacon.mjs` — close-ups of a cruiser's light bar into `shots/beacon_*.png` (the "darkened" variant is moot now — the scene is dusk); `node test/chasetrace.mjs` — per-cruiser diagnostics during a chase (mode, lane edge, stuck timers, the obstacle in front) for tuning the pursuit driver; `node test/perf5.mjs` — uncapped per-frame timing percentiles during a 5★ chase.
- Debug API in the page: `window.__dbg` (`state()`, `teleport(x,z,yaw)`, `enter(type)`, `exit()`, `select(i)`, `god(on)`, `spawnHostile(d)`, `aimAtNearestNpc()`, `freeCam([x,y,z,tx,ty,tz])`, `traffic()`, `key(code,down)`, `look(dx,dy)`, **`wanted(n)`** sets the star level, **`police()`** dumps the wanted state, cruisers and officers, **`crime(kind)`** reports a crime at the player), `window.__G` (the game context), `window.THREE`.

## 2. Controls (also shown in-game)

On foot: WASD move · Shift sprint · Ctrl walk · Space jump · mouse look · LMB fire · RMB aim (over-the-shoulder) · Tab (hold) weapon wheel with bullet time · 1/2/3 or mouse wheel quick select · R reload · E enter nearest car (AI-driven cars get hijacked: the driver bails and runs; hijacking a cruiser puts an officer on the street and gives you a star).
In a car: W/S throttle/brake (S from standstill = reverse, W while reversing = brake) · A/D steer · Space handbrake · Q horn (**in a cruiser: siren on/off**) · R radio (four stations → off → …, keeps playing when you get out — section 10) · E exit (below ~7 km/h).
General: H help · M mute · Esc release mouse.

## 3. Architecture

| module | responsibility |
|---|---|
| `main.js` | renderer, the blue-hour rig (one faint cool shadow-casting key light, hemisphere, sky + PMREM environment, fog), world assembly, game loop (variable dt clamped to 50 ms, `G.timeScale` for bullet time), interactions (E/H/M/R/V), shadow-camera follow with texel snapping, speed streaks, debug API |
| `lighting.js` | **round 3: every artificial light** — light table + cell grid textures, the `onBeforeCompile` patch for all lit materials, static lamps / signs / windows / emissive overlays, glow sprites, headlight pools, blob shadows, AO skirts (section 8) |
| `assets.js` | **all placeholder geometry** — the phase-2 swap surface (section 5); now also the police livery + light bar and the officer palette |
| `defs.js` | data: vehicle specs (incl. `police`), weapon specs, player/NPC constants, **`WANTED` table (the star ladder)** |
| `world.js` | street grid, blocks, districts, building placement, street furniture, lane graph (traffic), sidewalk graph (pedestrians), static colliders (spatial hash), ground height field, spawns; **`losStatic`, `nearestLaneNode/Edge`, `lanePath` (Dijkstra)** |
| `props.js` | instanced props; rigid-body-lite sim for dynamic ones; explosive barrels; camera crown boxes for trees |
| `player.js` | character controller, collisions, procedural animation on the rig, vehicle enter/exit, health/death/respawn (respawn clears the wanted level) |
| `camera.js` | third-person + **driving camera with candidate positions and sweep** (section 4), recoil, shake, impact kick, FOV punch, roll |
| `vehicles.js` | vehicle physics, collisions, damage & wrecks, traffic AI driver (`Driver`), **pursuit driver (`PoliceDriver`)**, engine audio hookup, crime hooks (rams, wrecks) |
| `police.js` | **wanted system**: crimes → points → stars, witnesses, line of sight, search area and evasion, dispatch of cruisers, roadblocks, officers, light-bar strobe (fixed pool of point lights), siren voices, screen tint |
| `weapons.js` | weapon wheel, firing, projectiles, world raycasts, impacts, explosions; NPC fire with the NPC's own weapon (pistol / MG) |
| `npcs.js` | pedestrians (wander, react, flee), armed hostiles, **police officers** (hunt / search / engage / cover / leave), ragdoll-lite |
| `fx.js` | billboard particles, debris chunks, tracers, decals, skid marks, shockwave rings, explosion lights |
| `audio.js` | Web Audio synthesis: gunshots, impacts, explosions, footsteps, crashes, horns, UI, engine voices, **sirens (`SirenVoice`), wanted stings, police radio chatter**, ambient bed, wind, **radio hook** |
| `postfx.js` | half-float MSAA scene target → threshold → two blur pyramids → ACES + bloom + **colour grade (cold lift, warm gain, S-curve, saturation)** + vignette + police edge tint + speed streaks + sRGB |
| `ui.js` | HUD, weapon wheel SVG, prompts, damage vignette + **directional damage arc**, **wanted stars + evasion bar**, minimap with **cruisers, officers and the search area**, fps/draw readout |
| `input.js` | keys / pointer lock / mouse deltas, per-frame edges, virtual inputs for tests |
| `util.js` | math helpers, `smoothDamp`, deterministic RNG, AABB + spatial grid, `rayAABB`, `MinHeap` |

Conventions everywhere: metres, seconds, kg, N. Y up. **Forward = local +Z, right = local −X** (three.js `Object3D.lookAt` convention, glTF "+Z front"). Yaw = rotation about Y, `forward = (sin yaw, 0, cos yaw)`. A positive steer / positive yaw turns **left**.

## 4. Systems and their tuning

### Character + camera (on foot)
- Capsule-as-circle controller (r 0.36, h 1.8). Speeds: walk 1.9, jog 4.6, sprint 7.4, aiming 2.6 m/s, weapon multipliers 1.0 / 0.9 / 0.72. Accel 26, decel 22, air control 0.35, jump 6.2 m/s, gravity 22. Coyote time 0.12 s. Step limit 0.55 m. Fall damage from −13 m/s.
- Facing follows movement (λ 12/s), snaps to camera while aiming or within 1.6 s of firing (λ 22/s).
- Collision: statics via circle-vs-AABB from the spatial hash, dynamic props (light ones get shoved, heavy ones block), vehicles via OBB (fast cars knock the player down and damage), NPCs soft separation. World boundary walls at ±400 m.
- Animation is procedural on the rig bones (section 5.1), all targets damped (λ 16–18/s).
- Camera on foot (`camera.js`, unchanged from phase 1 apart from the ground clamp): pivot at player + 1.5 m smoothed with a critically damped spring (smoothTime 0.045 s; rotation is *not* smoothed). Boom 4.1 m (aim 1.8 m), shoulder offset 0.42 (aim 0.7), FOV 62 (aim 46). The boom is swept against building AABBs (padded 0.28 m), props ≥ 2.5 m tall and ≥ 0.5 m across, and vehicle OBBs; pull-in is immediate, push-out damped (λ 5). Pitch −60°…+66°. Recoil is an additive pitch/yaw offset; shake is procedural sine noise decaying at λ 6. **New: the camera is clamped ≥ 0.45 m above the ground in both modes** (looking up steeply used to put it under the road).

### Driving camera — what was broken and what it is now
**The bug.** The player reported that the camera "sometimes swings out so far that the car is no longer visible". The suspect was the pivot lift for the boxed-in case (`lift = clamp((2.2 − curDist)·1.1, 0, 2.2)`). The headless test reproduced the symptom immediately and showed the real cause: `camera.js` stored the look-ahead vector in the shared temp `_o` (line 68), overwrote `_o` with the boom target (line 78) and then computed `pivot + lookAhead` with `lookAhead === _o` (line 85), i.e. the camera looked at **2 × pivot** — the pivot mirrored through the world origin. Near the spawn (x≈0, z≈−30) that is close to correct, which is why it survived the phase-1 play-through; a few blocks away the camera points into empty streets and the car is gone. The lift was a secondary problem (for ~0.3 s the camera sat inside the cabin while the lift damped in, then it went top-down).

**The rule now: the player's own car is always clearly in frame.** `updateDrive()` in `camera.js`:
- Pivot = car + 1.15 m (spring smoothTime 0.03). Yaw follows the heading with λ 5.5 + 0.08·speed (the lag is the sense of momentum); mouse orbit decays after 1.6 s idle; orbit pitch is clamped to [−0.5, +0.12] rad so the camera can never be pushed below the pivot. Reverse view flips the heading with hysteresis (on below −2.5 m/s, off above −0.6 m/s) so it cannot flip-flop around the threshold.
- Boom 6.2 m + 0.05·speed **+ an acceleration term** (longitudinal acceleration smoothed at λ 5 → −0.8…+0.7 m: throttle pushes the camera back, braking pulls it in). Pitch −0.2 rad. FOV 64→80 with speed.
- **Candidates instead of a lift.** In the camera frame (back, side, up) there is an ordered list: the ideal boom · slightly raised · swung 3.2 m to the side · higher · 4.6 m to the side · low and 3.6 m to the side · higher still · 2.4 m to the side and 2.2 m up · close above the roof (1.7 m back, 2.7 m up). Each candidate is swept from the pivot (padded AABBs, vehicle OBBs, tree crowns); the first unobstructed one wins. If all are blocked (stopped under a tree crown, wedged between cars) the least-blocked ray is used as far as it is free. The chosen offset is damped (λ 7) so side switches and push-outs glide; if the damped position itself is not free, it snaps to the chosen candidate (pull-in is immediate). The preferred side is remembered so the camera does not oscillate between left and right.
- Look target: the road ahead (1.5 + 0.06·speed metres along the car's heading) while the boom is free; as the camera moves in it blends to the car itself. The look-ahead shrinks with the angle between the camera and the car (`max(0, cos Δyaw)`), so during spins, reversing and orbiting the car stays centred.
- Sweep changes: thin street furniture (< 0.5 m across: lamps, signals, bollards, hydrants) no longer pulls the camera in for a frame as it passes; tree crowns are camera colliders (`props.js` sets `aabb.cam`: ±2.3 m / 1.8–6.6 m for round trees, ±1.7 m / 3.8–9.9 m for tall ones); the gas station is no longer one 24×18×6 box but four columns, a canopy slab (y 4.9–6.4) and the shop box, so you can drive under it.
- Dynamics: lateral-g roll (±0.05 rad, λ 6), impact kick (a world-space offset in the impact direction, λ 9) with a FOV punch (≤ 6°, λ 7), procedural shake as before.
- Measured by `test/camera.mjs` (minified build): 12 scenarios, 4 589 frames, worst streak 1 bad frame, min corners in frame 4 (wall-reverse close view), max centre offset 0.26 NDC (orbit), 0 console errors.

### Vehicles (`vehicles.js`, specs in `defs.js`) — unchanged physics
Planar bicycle model in the body frame with four spring/damper wheels, load-sensitive saturating tyres, friction circle, handbrake, engine + 5-speed automatic, weight transfer, 120 Hz sub-stepping, collisions against statics / vehicles (SAT) / props, damage & wrecks — exactly as in phase 1 (see the table below). Round-2 changes on top: **vehicle-vs-vehicle crash damage is scaled to 60 %** (rams are frequent now; walls still hurt fully), hard impacts throw paint-coloured debris chunks (> 7 m/s) and kick the camera, the last player hit on a car is remembered for eight seconds (`lastHitBy`) so wrecks can be attributed for the wanted level, cruisers have 130 hp.

| | sedan (FWD) | muscle (RWD) | van (RWD) | **police (RWD)** |
|---|---|---|---|---|
| mass | 1350 kg | 1620 kg | 2500 kg | 1500 kg |
| torque / redline | 185 Nm / 6500 | 560 Nm / 6200 | 300 Nm / 4200 (diesel) | 340 Nm / 6600 |
| μ lateral (rear mult.) / longitudinal | 1.05 (1.05) / 1.25 | 1.02 (0.93) / 1.35 | 0.88 (1.0) / 1.15 | 1.12 (1.0) / 1.35 |
| springs / damping / rollbar | 46 k / 4.2 k / 8 k | 38 k / 3.2 k / 5 k | 62 k / 5.2 k / 16 k | 50 k / 4.6 k / 9 k |
| CG height / top speed | 0.55 / 50 | 0.50 / 68 | 0.95 / 36 | 0.52 / 58 |
| character | neutral, chirps in 1st | power-oversteer, lively | slow, tall, rolls | sedan shell, quick, grippy |

### Traffic AI (`Driver` in `vehicles.js`)
14 cars follow the lane graph (right-hand traffic, random turns with 55 % straight preference), pure-pursuit steering, speed limit 10–14 m/s, slow for turns, brake for cars ahead in a corridor, stop for pedestrians and the player on foot (honk after 1.4 s), yield at junction entries, reverse out when stuck > 6 s, flee when threatened, 40 % bail-outs. `E` next to an AI car = hijack. **New: when a cruiser with its siren on is within 45 m behind or beside, traffic pulls 3 m to the right kerb and stops for 3.5 s** (the chase carves a lane through traffic). The driver was refactored into reusable pieces (`lookPoint`, `steerTo`, `carsAhead`, `applyControls`, `progress`) that the pursuit driver shares.

### Police and wanted stars (`police.js`, `PoliceDriver` in `vehicles.js`, officers in `npcs.js`, table `WANTED` in `defs.js`)
The word "heat" is gone from the code and the HUD. Crimes add **wanted points**; stars are thresholds on the points; stars only fall by evading.

**Crimes → points** (cooldowns stop machine-gun fire from counting every round): gunfire 0.3 (witnessed, first shot is a star straight away) · shooting a pedestrian 0.8 · hitting one with the car 0.9 · killing one 2.2 (at least 2★) · ramming a car 0.5 · wrecking a car 1.6 · carjacking 0.7 (witnessed) · explosion 1.5 (witnessed, at least 2★) · shooting / ramming / running over an officer 1.2 / 1.0 / 1.0 · killing an officer 3.2 (at least 3★) · wrecking a cruiser 2.8 (at least 3★). "Witnessed" = a pedestrian within 35 m, a cruiser within 90 m, or the police already have eyes on you — so target practice on the empty stunt lot is free, shooting on the plaza is not. Thresholds: 1★ ≥ 1, 2★ ≥ 3, 3★ ≥ 6, 4★ ≥ 10, 5★ ≥ 16 points. Every crime also *reports* your position.

**The ladder** — every level is recognisably harder than the last:

| ★ | cruisers | pursuit speed | on the street | officers | roadblocks | evade time / search radius |
|---|---|---|---|---|---|---|
| 1 | 1 | 18 m/s | follows 9 m behind, calls it in (radio chatter), no ramming | 1 per car, pistol, rare bursts (2.6–4 s) | – | 10 s / 45 m |
| 2 | 3 | 22 m/s | **boxing**: slots behind, both sides and in front; PIT nudges at the rear axle below 7 m | 1 per car, pistol (1.3–2.4 s), take cover | – | 16 s / 60 m |
| 3 | 4 | 27 m/s | **ramming** the rear quarter whenever lined up within 15 m | 2 per car, pistol (0.9–1.7 s), cover | every 20 s, 2 officers | 24 s / 75 m |
| 4 | 6 | 30 m/s | heavier, faster response, spawns 90 m out | 2 per car, **machine guns** (0.7–1.3 s) | every 14 s, 3 officers | 34 s / 95 m |
| 5 | 8 | 33 m/s | relentless: spawns 80 m out, up to 12 officers, cruisers replaced as soon as one is lost | 2 per car, MG (0.5–1 s) | every 10 s, 4 officers | 45 s / 120 m |

**Cruisers** (`VEHICLE_DEFS.police`, sedan shape with a white body, black hood/doors/boot and a roof light bar) are dispatched while the active count is below the ladder (plus one backup unit if nobody has made contact after 20 s): a lane 60–150 m from the anchor — where you will be in three seconds until the first contact, your *last sighting* afterwards, so a hiding place is not spoiled by fresh spawns — preferably out of the camera frustum or occluded, running the same way as you when you are moving, with a short Dijkstra route (one-way lanes can force long loops) through the lane graph to your last known position — so you hear the siren before you see the car. **Path mode** follows that path with the traffic steering at pursuit speed (turns at ≤ 9.5 m/s, shorter look-ahead in turns so corners are not cut onto the sidewalk), overtakes slow traffic on the left, and switches to **direct mode** with a line of sight under 80 m or for the last stretch when the lanes end. Direct mode leaves the lanes: it drives at a *slot* around you (see the ladder; a cruiser that is already ahead of you and pointing your way does not U-turn but holds the road ahead — offset to box you in from 2★), closes at full speed until 14 m from its slot and then matches your speed, predicts your position 0.5 s ahead, rams at 3★+, refuses to brake for your car but does for other cars, feels the way with three feelers (buildings and props ≥ 0.5 m tall), reverses out when stuck and follows the reverse with a short escape turn (a three-point turn); a cruiser that keeps getting stuck gives up, stands down and is replaced. When you are lost they drive to the last known position, then cruise node to node inside the search area. When you are on foot they pull up within 42 m (or stop where they are with a line of sight up to 75 m if they cannot get closer), the officers get out and the car holds for a moment. **Roadblocks** (3★+, while you drive faster than 32 km/h): two cruisers across the street ~120 m ahead of your heading on a lane aligned with it, offset so they do not sit on the parked cars, officers in cover behind them; the block cars join the pursuit once you are past (or after 45 s). Wrecked cruisers stay as wrecks; hijacking a cruiser (`E`) puts its officer on the street and gives you a star.

**Officers** are NPCs on the normal rig with the normal weapon and damage model (`npcs.js`, `cop = true`, navy uniform): `hunt` runs to the last known position (straight when the line is clear, greedy along the sidewalk graph otherwise), `search` looks around and picks nearby points, `engage` strafes and keeps 8–26 m (stands and shoots when you speed past in a car), shoots in bursts at the ladder cadence with a line-of-sight check from the gun (your own car does not block it, so the car gets shot up — NPC bullets do 16 % vehicle damage), `cover` after a burst (40 %, 70 % when hurt): a point behind the nearest stationary car (their own cruiser preferred) or a heavy prop on the far side from you, crouched, popping up to fire; `leave` when the level clears. They are hit, knocked down, run over and killed exactly like any pedestrian; killing one is a 3★ crime. Dead officers are removed once out of view for 20 s.

**Line of sight and evasion.** Every frame the player is *seen* if a cruiser within 90 m or an officer within 60 m has a static-world line of sight (buildings, tall props and tree crowns block; cars and people do not). Seen → last known position updates, evasion resets. Not seen → after 1.5 s the **evasion timer** runs at the ladder's rate, at only 28 % while you are inside the search circle *and* a unit is actually searching in it; reaching 100 % drops one star, re-arms, and at zero plays the "LOST THEM" chime and stands everyone down (cruisers drive off with sirens off and despawn out of view). Evasion does not start before the first *contact* (a unit within 60 m or a sighting; 40 s cap), so a level cannot be waited out before anyone arrives; until then dispatch keeps guiding the first units to you. **HUD:** five stars top-left (lit ones glow, pop on a new star), "WANTED" while seen, "EVADING · stay hidden" with the stars blinking and a cyan progress bar while hidden; the minimap shows cruisers as strobing red/blue blocks, officers as blue dots and the search area as a cyan circle. Dying clears the level.

**Sirens and lights.** `SirenVoice` (`audio.js`): three oscillators (saw + sub square + high triangle) through a bandpass and a soft clipper, frequency 640→1260 Hz swept by a wail (0.44 Hz, cosine) or a yelp (3.4 Hz, triangle) computed per frame so the mode switches instantly (yelp when a cruiser is in direct mode within 30 m), doppler from the relative velocity, spatialised with refDistance 20 m / max 520 m — audible from two blocks away. Stings: a two-note stab when a star is added, a falling tone when one drops, a three-note chime when clear; a radio-chatter squelch burst when the first unit calls it in and when a roadblock goes up. **Light bar:** two beacon meshes per cruiser (`beacon_L` red, `beacon_R` blue, 0.46×0.14×0.28 m at (±0.3, 1.62, −0.15)) swap between a dark material and an emissive one 4.5× over the bloom threshold in a 2.4 Hz double-flash pattern (phase offset per car); a **fixed pool of four point lights** (intensity 70, distance 18, decay 2) rides on the nearest strobing cruisers so the street around them really flashes — a fixed pool because three.js recompiles every material when the light count changes. Within 32 m of a strobing cruiser the frame edges take a red/blue tint (`postfx.js`, `tint` + `tintCol`). Q in a stolen cruiser toggles its siren.

### Dynamism (what was added for "more alive, more kinetic")
- Camera: boom stretches with throttle and shortens under braking; lateral-g roll; directional impact kick + FOV punch on crashes and when running someone over; look-ahead that follows the heading.
- Speed streaks: above ~80 km/h a mild radial blur (five taps, edges only, ≤ 0.55) fades in (`postfx.js`, `streak`).
- Hits: paint-coloured debris on hard impacts; a red arc on the screen edge points at whoever shot you (or the explosion / car that hit you) for a second (`ui.damageFrom`).
- Traffic pulls over and stops for sirens; pedestrians scatter when a cruiser tears past within 8 m; officers' gunfire makes bystanders flee like the player's does.
- Chases: boxing, PIT nudges, rams, roadblocks, cruisers crashing into traffic and each other (wrecks stay), officers on foot in cover — the streets get messy on their own.
- Stars, stings, chatter and the edge tint make the escalation readable without a single new menu.

### Dynamic props + explosions, weapons, NPCs, audio, rendering, world
Unchanged from phase 1 except where noted above. Summary kept for the handover:
- ~230 dynamic props with a rigid-body-lite sim; barrels explode (chain reactions), crates break; static props are colliders.
- Weapons: pistol (semi, 12, 34 dmg), machine gun (auto 800 rpm, 60, 15 dmg), rocket launcher (blast r 7.5, 260 dmg); wheel on Tab with bullet time; hit feedback per material; explosions shared by rockets, barrels and wrecks. NPC officers fire the pistol (5° spread) or the MG (4.2°, 6-round bursts at 0.09 s).
- NPCs: 64 pedestrians + 2 guards per hostile spot; wander, idle, separate, dodge cars, get run over, react to gunfire / aiming / impacts / sirens; guards engage within 13 m or when shot at (the old "hunt at high heat" rule is gone — hunting is the police's job now).
- Audio: layered synthesised gunshots, explosion (89 % of energy below 150 Hz), impacts per material, footsteps, crash, horns, UI, engine voices with tyre squeal and doppler, wind; **radio** wired in round 5 (`class Radio` in `audio.js`, section 10).
- Rendering: `MeshStandardMaterial` with vertex colours, PMREM sky environment, one 4096² shadow map (±90 m since round 3) with texel snapping, half-float 4×MSAA post chain with ACES, bloom, grade, vignette; instancing for buildings, props, markings, decals, skids, tracers, debris, particles; **round 3: the light grid, the emissive layer and the contact darkening of section 8.**
- World: 7×7 street grid (boulevard at x = 0 with a tree-lined median, main street at z = −10), districts (downtown, plaza, parks, parking, gas station, industrial column, stunt lot, residential rows), deterministic placement (`makeRng(20260901)`), lane graph (right-hand, Bézier turns, no U-turns), sidewalk graph, spatial-hash colliders, ground height field with ramps and speed bumps.

## 5. ASSET HOOKS — the contract the GLBs were built to (and now fulfil)

Everything below lives in `src/assets.js`. **Since round 4 every function here returns the Blender asset** (section 9.4); the tables
remain the contract — pivots, child names, bone names, dimensions — that the loaders verify against. Materials are the GLB PBR sets;
`MAT.*` still holds the lens / brake / beacon / wreck materials the game swaps in.

### 5.1 `makePlayerMesh()` / `makeNpcMesh(rng, armed, cop)` → `makeCharacterRig(palette, scale)`
Returns `{ root: Group, mesh: SkinnedMesh, bones: {name: Bone}, socket: Object3D, height }`. Root origin between the feet on the ground, facing +Z, 1.80 m tall (NPCs scaled 0.93–1.06, officers 0.98–1.06). The animator sets `bone.rotation` by name every frame (rest pose = identity rotations), so a GLTF must ship the same bone names with the same rest orientation (all bones world-aligned, +Y up the limb, arms hanging). **Officers** are the same rig with a navy palette (`cop = true`: shirt #1d2c52, pants #161a24, hair slab #0d1426 as a cap) — a phase-2 officer model needs the same rig plus, ideally, a cap and a belt; the crouch in cover is a pose (thighs −1.35, shins +1.5, mesh lowered 0.42 m), not a separate animation. Rest joint positions (x right→left is −→+, y, z):

| bone | parent | rest position (m) | part box w×h×d (centre) |
|---|---|---|---|
| Hips | — | (0, 0.95, 0) | 0.34×0.18×0.22 @ y 0.90 |
| Spine | Hips | (0, 1.10, 0) | 0.32×0.22×0.20 @ 1.16 |
| Chest | Spine | (0, 1.30, 0) | 0.40×0.26×0.24 @ 1.39 |
| Head | Chest | (0, 1.52, 0) | 0.20×0.24×0.22 @ 1.66 (+hair slab, nose) |
| UpperArm_L / _R | Chest | (±0.22, 1.45, 0) | 0.11×0.28×0.11 @ (±0.24, 1.31) |
| Forearm_L / _R | UpperArm | (±0.24, 1.17, 0) | 0.09×0.25×0.09 @ (±0.24, 1.045) |
| Hand_L / _R | Forearm | (±0.24, 0.92, 0) | 0.08×0.14×0.06 @ (±0.24, 0.85) |
| Thigh_L / _R | Hips | (±0.11, 0.95, 0) | 0.15×0.45×0.16 @ (±0.11, 0.725) |
| Shin_L / _R | Thigh | (±0.11, 0.50, 0) | 0.12×0.42×0.13 @ (±0.11, 0.29) |
| Foot_L / _R | Shin | (±0.11, 0.08, 0) | 0.11×0.08×0.27 @ (±0.11, 0.04, +0.05) |

`_L` is the character's left = world +X when facing +Z; `_R` (weapon hand) = −X. **WeaponSocket**: child of `Hand_R`, position (0, −0.08, 0.03), rotation.x = +90° → a weapon's +Z barrel runs down the forearm and points forward when the arm is raised. Camera pivot = feet + 1.5 m; chest for NPC aim = feet + 1.3 m; bullet capsule = spheres at +0.95 (r 0.42) and +1.66 (r 0.20, headshot ×2.5). Bounding sphere is enlarged ×1.6 for culling while animated.

### 5.2 `makeVehicleMesh(type, paintHex)`
Returns a Group. **Origin = centre of the four contact patches, on the ground (y = 0) with the suspension at static rest; forward +Z.** The body builder is chosen by `def.shape || type` (the police def uses the sedan shape). Children by name (all used by gameplay):
- `body` (Mesh, castShadow), `lights` (Mesh, unlit vertex colours: warm headlights, red tail), `brakeLights` (Mesh, toggled visible on braking), `wheel_FL/FR/RL/RR` (Mesh, pivot at hub centre, rotation.y = steer for the fronts, rotation.x = spin, position.y = radius ± suspension travel), empties `seat` (driver hip point), `exit_L` (+X side, 0.9 m off the body), `exit_R`, `exhaust`, `headlight_L/R`.
- **Police only:** `beacon_L` (red) and `beacon_R` (blue): two 0.46×0.14×0.28 m meshes at (+0.3 / −0.3, 1.62, −0.15) on a 1.15×0.1×0.34 bar; `police.js` swaps their `material` between `MAT.beaconRedOff/BlueOff` and `MAT.beaconRedOn/BlueOn` every frame. A phase-2 cruiser must keep these two named meshes (any geometry) so the strobe keeps working; the point lights are positioned 2.3 m above the car origin independently of the mesh.
- `userData.dims = { length, width, height }`.

| | sedan | muscle | van | police |
|---|---|---|---|---|
| L × W × H | 4.60 × 1.85 × 1.45 | 4.90 × 1.95 × 1.32 | 5.60 × 2.10 × 2.40 | 4.70 × 1.88 × 1.45 |
| wheelbase / track | 2.75 / 1.60 | 2.95 / 1.68 | 3.40 / 1.75 | 2.80 / 1.62 |
| wheel radius / width | 0.34 / 0.22 | 0.36 / 0.30 | 0.38 / 0.24 | 0.35 / 0.24 |
| wheel hubs (x, y, z) | (±0.80, 0.34, ±1.375) | (±0.84, 0.36, ±1.475) | (±0.875, 0.38, ±1.70) | (±0.81, 0.35, ±1.40) |
| seat empty | (0.36, 0.75, 0.35) | (0.38, 0.68, 0.15) | (0.42, 1.00, 1.20) | (0.36, 0.75, 0.35) |
| silhouette | three-box, cabin set back, mirrors | long hood + scoop, low fastback cabin, spoiler, twin exhausts, wide rear tyres | snub cab with wrap windows, tall cargo box, roof rails, vertical tail lights | sedan in white with black hood, doors and boot, roof light bar |

The physics body rectangle used for collisions is exactly L × W around the origin (height 0.2…H for raycasts). Wreck state swaps `body.material` for a dark one.

### 5.3 `makeWeaponMesh(type)`
Returns a Group. **Origin = grip point (where the right hand closes), barrel along +Z, up +Y.** Child empty `muzzle` marks the tip (projectiles and flashes spawn there); the rocket launcher also has `loadedRocket` (hidden while reloading). Officers carry the pistol, from 4★ the machine gun (same meshes).

| | pistol | machine gun | rocket launcher |
|---|---|---|---|
| overall length / height | 0.20 / 0.16 | 0.85 / 0.25 | 1.15 / 0.30 (tube r 0.062) |
| muzzle (x, y, z) | (0, 0.022, 0.16) | (0, 0.05, 0.65) | (0, 0.09, 0.80) |
| grip extends | 0.11 m below origin | 0.11 m below, stock −0.32 behind | grips at z 0.02 and 0.35, bell to z −0.40 |

### 5.4 `makeBuilding(kind, rng)` — `BUILDING_KINDS`
Returns a prefab Mesh; the world instances it (`InstancedMesh` per kind, `instanceColor` = wall tint, walls have vertex colour 1,1,1 so the tint multiplies; glass bands are fixed dark vertex colours). **Origin = bottom centre of the footprint on the lot surface, entrance/facade toward +Z.** Rotations are multiples of 90°, so colliders stay axis-aligned (AABB = footprint × height). Floors are 3.0–4.4 m bands with 1.2–2.4 m glass insets (0.2–0.4 m relief) so lightmaps have something to catch.

| kind | footprint w × d (m) | height | district | notes |
|---|---|---|---|---|
| tower_a | 26 × 26 | 84 (+8 mast) | downtown | 4.5 m plinth, 60 m shaft, 19² setback tower |
| tower_b | 22 × 34 | 66 | downtown | slab, rooftop box |
| tower_c | 30 × 30 | 48 | downtown | 22 m glassy podium, 22² tower |
| office_a | 30 × 22 | 36 | midtown | parapet, roof plant |
| office_b | 24 × 24 | 28 | midtown | 30 × 30 × 8 podium with glass band |
| apartment_a | 28 × 16 | 22 | midtown | balconies on the +Z facade every 3.1 m |
| apartment_b | 20 × 20 | 18 | midtown | |
| shop_row | 42 × 14 | 8 | midtown | glass shopfront, four awnings (+Z), roof sign |
| shop_small | 20 × 14 | 7 | residential/midtown | blue awning |
| warehouse | 48 × 28 | 11 (+2.2 sawtooth) | industrial | two roller doors on +Z |
| industrial | 34 × 24 | 14 | industrial | chimney to 26 m, rooftop tank |
| parking | 40 × 30 | 12 | midtown | open decks + columns (collider is the full box) |
| house | 12 × 10 | 7.5 (4.2 wall + 3.2 pitched roof) | residential | door/windows on +Z, chimney |
| gas_station | 24 × 18 | 6 | midtown | canopy on four columns, two pumps, shop box behind — **colliders: columns 0.8² at (±9, −2/+6), canopy slab y 4.9–6.4 over 24 × 12 at z +2, shop box 10 × 4 × 8 at z −12** (drive-under) |
| monument | 6 × 6 | 30 | plaza | stepped base + obelisk |
| fountain | 12 × 12 | 3 | plaza/park | basin r 5.8 (walkable edge is a collider) |
| bridge_ramp | 12 × 26 | 2.4 (wedge rising toward +Z) | stunt/industrial | **no collider**: it is a height-field entry in `world.ramps` |

### 5.5 `makePropPrefab(kind)` — `{ mesh, geometry, material, radius, height, mass, dynamic, sound }`
Instanced per kind. **Origin = base centre on the ground.** `radius` (collision circle) / `height` / `mass` / dynamic:
cone 0.25/0.72/4 ✔ · barrel 0.30/0.90/40 ✔ (explosive) · crate 0.55/0.90/35 ✔ (breaks) · bench 0.90/0.90/60 ✔ · trash 0.30/0.98/25 ✔ · mailbox 0.25/1.30/90 ✔ · newsbox 0.30/1.10/30 ✔ · dumpster 1.00/1.36/320 ✔ · hydrant 0.16/0.85 static · planter 0.70/0.90 static · bollard 0.12/1.00 static · lamp 0.15/8.0 static (arm 2.2 m toward +Z, head at 7.95) · trafficlight 0.15/5.5 static (arm 4.5 m toward +Z) · tree_round 0.35/6.5 static (canopy r 2.3 at y 4.2; **camera crown box ±2.3 m, y 1.8–6.6**) · tree_tall 0.35/9.5 static (**crown box ±1.7 m, y 3.8–9.9**) · bush 0.70/1.3 static · busstop 1.6/2.7 static (3.2 wide, glass back at z −0.6) · wall 2.0/1.2 static (4 m boundary segment) · tank 2.3/5.2 static.
Dynamic props are rendered with their full quaternion; when lying on the side the origin is lifted by the rotated bounding box, so a replacement mesh must keep the same footprint/height or update the numbers. Officers use heavy props (mass ≥ 250, height ≥ 0.85, not lamps/signals/trees/walls) as cover — keep those numbers when swapping meshes.

### 5.6 Sky
`makeSky(sunDir)` — 1800 m back-face sphere, **since round 3 a blue-hour gradient**: deep blue zenith, cobalt mid band, a warm horizon band toward `sunDir` (whose y is now *negative* — the sun is below the horizon and only the sky uses it) fading to violet away from it, faint stars overhead; also fed to `PMREMGenerator` for the environment map, so the wet road and car paint mirror the horizon band. Phase 2: swap for a dusk HDRI (set `scene.environment` and `scene.background`); the shadow-casting key light uses `G.keyDir`, not `sunDir`. **Careful:** anything that produces NaN in this shader (a `pow` of a slightly negative base did, once) blackens the whole scene through the environment map without a console error. There is still no day/night *cycle* — the city is parked at dusk.

## 6. What was measured (round 2, minified build, MacBook GPU via Metal, headless Chrome 1280×720)

- Gate (`pruefe_openworld.mjs`): GREEN — spawn view mean luminance 136.6, 15.5 % near-black (bottom half 17 %), limit 33 %; chase shots 7–11 % near-black, worst frame in the police run 22.9 % (camera close behind the car during a ram).
- Camera test: PASS, 12 scenarios, 4 589 frames, worst streak 1 bad frame (limit 6), 0 console errors.
- Police test (green runs on the final build): 1★ after the first witnessed shot; first cruiser within 60 m after 3–23 s (the plaza is the hardest spot: no lane passes within 28 m and the monument blocks sight; a backup unit is dispatched after 20 s without contact); officer out 1.5–3 s after the car stops and firing within a few seconds; killing him → 4★ (3★ minimum + points), cover behaviour observed; 3★ chase up the boulevard at ~70 km/h: 2–3 cruisers within 40 m at once, 3–7 rams/impacts on the player car in 25 s, police had eyes on the player in 28–60 of 60 samples, roadblocks with officers when the run drives long enough in one direction; 5★: 8–10 cruisers on the street, 7–10 siren voices, 18–42 audio voices, **60 fps (0.5 s windows min 58) at 250–420 draw calls**; evasion: 2★ → 1★ after 20 s hidden, cleared after ~30 s.
- Frame time uncapped (`feel.mjs`): 196 fps (5.6 ms) at the spawn view, 165 fps (5.8 ms) on the downtown overview — about 1.3 ms more than phase 1, the price of the four extra point lights in every lit fragment. **5★ chase uncapped (`test/perf5.mjs`, 10 cruisers, 4 officers, 10 sirens, 381 draws, 505 k tris): mean 9.8 ms, p50 9.8, p95 13.2, p99 14.9, worst frame 55 ms (one spike in 20 s, a spawn/wreck), 9 of 2 436 frames over 16.7 ms.** Vsync-locked 60 fps in every state; the police test's 0.5 s fps windows dip to 52–58 at most during roadblock spawns (entities are now spawned one per frame and geometry is cached, which removed most of the hitching). 282–420 draw calls, 486–505 k triangles.
- Camera step while sprinting 4.1 cm/frame ± 0.9 cm, max vertical step 0.00 cm.
- Phase-1 play-through (`play.mjs`): all states pass, 0 console errors, 0 warnings.
- Audio numbers of phase 1 unchanged (see `test/audio.mjs`); the siren sits at 640–1260 Hz with refDistance 20 m and is audible ~250 m away.

### Round 3 (blue-hour build, minified, same machine / headless Chrome 1280×720 via Metal)
- Gate (`pruefe_openworld.mjs` on the final build): **GREEN — spawn view mean luminance 65.0, 23.1 % near-black (limit 33 %), bottom half 83.5 / 26.3 % (limit 50 %), 0 console errors.** Round 2 daylight was 136.6 / 15.5 %: the frame is half as bright by design and still well inside the gate.
- `test/look.mjs`, final build: spawn view mean luminance 64.8 with 23.2 % near-black (bottom half 83.2 / 26.5 %) (round 2: 136.6 in daylight — the frame is darker by design and still far under the near-black limit); the darkest of the sampled viewpoints is the drive shot behind the muscle car (mean 42.4, 44.3 % near-black, bottom half 57.7 % — the camera looks down at unlit asphalt right behind the car; the road ahead is lit by its own beam, the sides by the lamps), the brightest the gas station (84.8 / 12.2 %). The police test's hiding-place shot (`pol_E1_evading`, parked in an alley between two warehouses) is 66 % near-black — that is an alley at dusk, not a gate viewpoint, and the exit prompt and the car's silhouette still read.
- Uncapped frame time (`feel.mjs`, two builds): **242–245 fps / 4.1 ms** at the spawn view (round 2: 196 fps / 5.6 ms), 220 fps / 4.5–4.6 ms on the downtown overview (round 2: 165 / 5.8). Camera step while sprinting 3.3 cm/frame ± 0.6, max vertical step 0.00 cm.
- **5★ chase uncapped (`perf5.mjs`, 8–9 cruisers, 4 officers, 8–9 sirens, 237–356 draws, ~480–500 k tris), two runs: mean 4.4 / 4.5 ms, p50 4.3 / 4.4, p95 6.1 / 5.9, p99 8.1 / 7.1, worst frame 10.9 / 68.4 ms, 0 / 1 of ~5 100 frames over 16.7 ms** — the one 68 ms frame in the second run is a first-use shader compile or entity spawn, the same kind of single spike round 2 had (55 ms). Round 2: mean 9.8, p95 13.2, p99 14.9, 9 frames over 16.7. Vsync-locked 60 fps in every state of the play-through.
- Play-through (`play.mjs --gpu`): all states pass, 60 fps, 0 console errors, 0 warnings.
- Camera test (`camera.mjs`, final build): PASS — 12 scenarios, 4 523 frames, **0 bad frames** (limit 6 consecutive), min corners in frame 4 (wall-reverse close view), max centre offset 0.26 NDC (orbit), 0 console errors — identical to round 2, the look changed nothing about the camera.
- Police test (`police.mjs`, final build, two runs): run 1 failed the evasion checks — a damaged cruiser searching the industrial column found the hiding place and kept eyes on the player for 40 s, so no star could drop (the documented nondeterminism: the hiding spot is next to a lane); **run 2 PASS with 0 failures**: 1★ after the first witnessed shot, officer out after 30 s and firing, killing him → 4★, 3★ chase with 2 cruisers within 40 m, 7 impacts, roadblocks with officers, 5★ with 9 cruisers at 60 fps (min 60, max 436 draws), 2★ → 1★ after 20 s hidden, cleared after 35 s. Nothing in the lighting layer reads or writes police state; it only reads positions.
- The police test's own shots: the 3★ chase seen from behind the player car is the darkest at 55 % near-black (unlit asphalt right behind the car), the firefight and the 5★ shots sit at 10–32 %.
- Light counts: 596 static lights in the table; 10–25 dynamic entries in normal driving, ~40–60 during a 5★ chase (three per strobing cruiser plus headlights and tail lights of every driven car within 170 m).

## 7. Known gaps and what I would do with more time

- Pursuit driving is good enough to feel like a chase but not flawless: cruisers still occasionally wedge against corner furniture or a pulled-over car for a few seconds before the escape turn or the give-up rule frees them (about 10–15 % of cruiser-seconds in `chasetrace.mjs` runs are spent at 0 km/h). A proper local planner (a small grid A* around the car when off-lane) would fix the rest.
- The player's car takes a beating at 3★+ (rams are 60 % damage, walls 100 %); at 5★ expect to lose a car every minute or two. If that is too punishing, scale `impact(…, dmgScale)` for cruiser rams further down.
- No arrests: officers only shoot. A "busted" state (surrounded on foot at 1–2★ → fade, respawn without weapons) is the natural next step and needs no new tech.
- The evasion circle is static at the last known position; GTA drifts it toward where you were heading. Cheap to add in `updateSight`.
- Only one shadow cascade (see section 8.5 for why a second was not worth it at dusk); no day/night *cycle* (the city is parked at the blue hour, the lights are tuned for that); vehicles cannot roll over; the parking structure is a solid box; radio tracks and screens arrived in round 5 (section 10) — the rest as in phase 1.
- Lights cast no shadows (only the key light does). A person standing under a lamp does not throw a lamp shadow; the blob shadow covers the contact.
- Officers do not use vehicles after deploying and never get back in; cruisers that deployed keep chasing without a visible driver (there is no driver mesh in any car).

## 8. ROUND 3 — the blue-hour look: what changed, what it costs, what was dropped, what phase 2 improves

Round 3 changed nothing about what the game does. It changed what it looks like: the city sits in the blue hour — the sun just
below the horizon in the north-west, the sky still coloured, everything else dark enough that artificial light reads. All of it
is runtime rendering written by hand; nothing was baked and no texture was loaded.

### 8.1 The base rig (`main.js`, `assets.js` → `makeSky`)
- Sky: `makeSky` is a blue-hour gradient (zenith `#122352`, mid `#254684`, warm horizon `#e08a58` toward the sun azimuth fading to
  `#6a5a9a` away from it, a `glow` term just above the horizon, faint stars above 12°). The same sphere is rendered into the PMREM
  environment map, which is why the wet road and the car paint pick up the horizon band. `sunDir = (−0.45, −0.07, 0.89)` — below the
  horizon; only the sky uses it.
- Key light: one `DirectionalLight` `#8fa8dc` × 0.62 from `keyDir = (−0.42, 0.72, 0.55)` (elevation ≈ 46°, the sunset side) is the
  only shadow caster; it is a "sky/moon" fill that gives every box a lit and a dark face and drops the contact shadows. Shadow map
  4096² over ±90 m (was ±110), bias −0.0003, normalBias 0.7. The texel-snapped follow of round 1 now uses `keyDir`.
- Ambient: `HemisphereLight` sky `#40608f` / ground `#1a1826` × 1.05. Fog `#1a2a52`, 80 → 720 m (distant blocks dissolve into the
  sky colour; the emissive shader fogs toward 60 % of that colour so far windows dim instead of turning blue).
- Environment intensity 0.9 (the map is much darker than the daylight one, so the number went up, not down).

### 8.2 The light grid (`lighting.js`) — hundreds of lights without a single three.js light
- **Data.** A light table `DataTexture` 1024 × 4 RGBA32F: row 0 = position + range, row 1 = colour × intensity + `cos(outer)`
  (−1 for a point light), row 2 = spot direction + `cos(inner)`. A grid `DataTexture` 140 × 70 RGBA32F: the world ±420 m in
  12 m cells, 8 light ids per cell (two texels), −1 = empty. Static lights are inserted once, sorted by distance to the cell
  centre so the eighth-closest lamp is the one that drops out; dynamic lights are inserted at the front every frame (the grid
  is a copy of the static one, ~40 k floats, then uploaded — well under 0.1 ms of CPU). Spot lights are only inserted into
  cells inside their cone (mostly vertical spots — the street lamps — use their ground disc instead of the degenerate
  horizontal cone).
- **Shader.** `Lighting.patch(material)` sets `onBeforeCompile` on every `MeshStandardMaterial` (`patchAll` traverses the scene
  and the `MAT` table): the vertex shader writes the world position to a varying, the fragment shader — injected right after
  `lights_fragment_begin`, i.e. after three's own directional/hemisphere lights — fetches its cell, walks up to 8 ids, and
  for each one builds an `IncidentLight` (attenuation `pow2(saturate(1 − (d/range)^4)) / (d² + 0.35)`, spot factor
  `smoothstep(cosOuter, cosInner, ·)`) and calls **three's own `RE_Direct`**, so the lights go through the same Lambert + GGX
  BRDF as a real point light: the wet road gets real specular smears, car paint gets highlights, nothing is faked in the BRDF.
  Materials share one program-cache key (`lg` / `lgR`), so there is exactly one extra shader variant per material type and no
  recompiles ever — the light count in the scene is constant (zero).
- **Static entries (596):** every street lamp head (sodium `(1, 0.70, 0.36)` × 360 cd, range 26 m, a cutoff spot pointing down,
  outer 70° / inner 36°, so the ground floor of a facade catches some light and the floors above do not); per building kind
  `BUILDING_KINDS[kind].lights` placed per instance with the instance rotation — shopfront spill, neon signs (their colour is the
  same palette entry the emissive shader shows), the gas-station canopy (2 × 520 cd white), warehouse and factory wall packs
  (sodium), the parking decks (green-white fluorescent), porch lights on houses.
- **Dynamic entries (per frame, read-only from the other systems):** driven cars (`v.driver && !v.wrecked`): headlight spots
  (player: two, 1 300 cd, outer 29°, tilted 11° down; AI cars: one combined 1 700 cd spot), a red tail point light that jumps
  from 10 to 40 cd with range 6.5 → 10 m while `brakeLights.visible`, a white reverse light; strobing cruisers
  (`police.strobes`, the list `updateLights` already computed): the double-flash as a red / blue point light at the bar (110 cd,
  16 m) **plus two rotating beams** (red and blue, 900 cd, 34 m, outer 29°, 1.2 rev/s, opposite each other) that sweep the
  facades — the beams are what makes a chase light up the street around it; explosions (`fx.flashes`, 4 200 cd × R/6, range 6R,
  quadratic decay over 0.5 s) and muzzle flashes (`fx.muzzleL`, 320 cd × size, decaying at 40/s).
- **Why a grid and not clustered/tiled lighting or deferred shading:** the city is flat, so a world-XZ grid is the cluster
  structure for free, it is rebuilt on the CPU in microseconds, and it works with three's forward materials unchanged (instanced
  buildings, skinned characters, shadow maps, MSAA — none of that survives a G-buffer rewrite in an evening).

### 8.3 Emissive layer, glow, pools (`lighting.js` + `makeBuildingEmissive` in `assets.js`)
- **Windows.** `floors()` in `assets.js` now records every glass band it builds (`kind.bands`); `makeBuildingEmissive(kind)`
  turns the bands into one quad per window (1.1 m wide, band height − 0.35, 2.3 m pitch, all four faces, 3 cm proud of the
  glass and still 20 cm inside the wall plane) with a per-window seed attribute. One `InstancedMesh` per building kind copies the
  building instance matrices; `instanceColor.r` is a per-building seed and `.g` the neon palette index. The `ShaderMaterial`
  hashes `(window seed, building seed)` → 34 % lit, warm / cool white / TV-blue at 1.05–2.75× (over the bloom threshold), the
  rest near-black; a slow `sin(time)` term makes a window switch about once a minute somewhere in view.
- **Signs and shops.** `SIGN[kind]` lists emissive quads per kind: shop units (kind 3, 78 % open, warm or cool white, 1.15× —
  under the bloom threshold on purpose so a shop reads as *lit inside* rather than as a lamp), neon strips (kind 2, palette
  `NEON` × 4.5, magenta / cyan / orange / lime / red / violet), canopy panels, parking-deck tubes, warehouse / factory wall
  packs, a porch light, the red aircraft light on the `tower_a` mast.
- **Prop overlays.** Lamp heads (a warm quad under the fixture + a small one on the side) and traffic lights (red or green
  per instance: the instance colour multiplies vertex colours, so one geometry serves both states) are extra `InstancedMesh`es
  with the prop matrices (static props never move).
- **Car lights.** `MAT.lights` is now 2.6× (headlight lenses ≈ 2.5, tail lenses ≈ 1.4 in HDR), `MAT.brake` 3.6×, the beacons 6.5×;
  parked and wrecked cars swap to `MAT.lightsOff` (dark lenses) — that is the one-line hook in `Vehicle.updateMesh`.
- **Glow sprites.** One additive `InstancedMesh` (1 024 slots) of camera-facing quads, billboarded in the vertex shader (size
  from the instance matrix, pulled 0.6 m toward the camera so the fixture geometry does not cut it), radial falloff, fogged by
  distance: every lamp head (static, 1.9 m), headlights (1.0 m), tail lights (0.45 / 0.75 m when braking), beacons (0.8 m).
- **Headlight pools.** The spot alone is invisible from the chase camera — at 10 m the beam hits the road at NdotL ≈ 0.08. So
  every driven car within 120 m also gets a flat additive quad on the road ahead (15 × (width + 4.5) m, a cone gradient drawn
  into a canvas, 64 slots). The pool is the visible beam; the spot in the grid still lights people and cars standing in it.

### 8.4 Wet asphalt, contact darkening
- The city interior (±255 m) is cut out of the 1000 m terrain plane and drawn as one quad with its own material
  (`world.roadMat`, `#2b2f36`, metalness 0, `userData.road = true`): the patch overrides its roughness per fragment with two
  octaves of value noise (0.16–0.5 — puddles and dry patches) and breaks the albedo up ±22 %. Low roughness + the PMREM sky +
  the GGX term of every grid light = the lamps and the canopy panels smear into the road toward the camera. Sidewalk slabs
  keep roughness 0.92, so pavement reads matte next to the road. No screen-space reflections (8.5).
- Blob shadows: an `InstancedMesh` of radial-gradient quads under every car (length + 0.7 × width + 0.9), pedestrian and the
  player (0.95 m, stretched when lying), shrinking when airborne.
- AO skirts: four gradient quads around every building footprint (2.6 m wide, 70 % → 0 alpha away from the wall).
- Vertex AO: `baseAO()` darkens the lowest 3.2 m of every building prefab to 58 % and the bottom of tall static props to 55 %
  (a quadratic ramp in the vertex colour; the instance tint multiplies on top).

### 8.5 What was measured, what was dropped and why
- Numbers: section 6, "Round 3". The whole layer costs *less* than the eight `PointLight`s of round 2 did: those were
  evaluated for every fragment of every material; the grid evaluates only the lights that reach a cell.
- **Dropped — screen-space reflections.** An SSR pass needs a depth + normal readback from the 4×MSAA half-float target and a
  ray march per pixel; the env-map + GGX smears already give the wet-road read, and I would rather spend the frame budget on
  DPR 1.5 (the renderer runs at up to 1.5× device pixels — a MacBook shows 1 920 × 1 080 fragments through this shader, not the
  1 280 × 720 of the headless numbers).
- **Dropped — screen-space ambient occlusion.** Same readback problem (three's `SSAOPass` / `GTAOPass` re-render the scene for
  normals + depth: ~300 extra draws and a full-screen pass). Contact AO is done with the skirts, blobs and vertex ramps instead;
  it reads well at this geometry level, and baked AO replaces all three in phase 2.
- **Dropped — cascaded shadow maps.** `examples/jsm/csm` would double the shadow passes for a key light that is 0.62 strong
  and cool; at dusk the second cascade buys nothing visible. The single 4096² map was tightened from ±110 m to ±90 m
  (4.4 cm texels) so the near range is crisp.
- **Dropped — shadow-casting local lights.** No shadow maps for the 596 lamps; the blob shadows cover the contact.
- **Kept after measuring:** 8 lights per cell (fewer left holes between pools in the boulevard), RGBA32F textures with
  `texelFetch` (positions must not be quantised), two rotating beams per cruiser (the `strobes` list is already sorted by
  camera distance; beams are skipped beyond 130 m).

### 8.6 Hooks added to gameplay systems (nothing else was touched)
- `vehicles.js`: `this.lightsMesh` + one line in `updateMesh` swapping `MAT.lights` / `MAT.lightsOff`.
- `police.js`: the four `PointLight`s are gone; `updateLights` stores the sorted per-frame strobe list in `this.strobes`.
- `fx.js`: `this.flashes[]` and `this.muzzleL` are plain records instead of `PointLight`s.
- `world.js`: `buildingMeshes` (kind → `{ im, list }`) so the emissive layer can copy instance matrices; the ground split.
- `main.js`: `G.lighting = new Lighting(G)` after all systems exist, `lighting.patchAll()`, `lighting.update(realDt)` once per
  frame before render. `__dbg.state()` reports `lights` (static) and `dynLights`.

### 8.7 What improves once real textures and baked lighting arrive (the GPU phase)
- **Bake the static part of the grid.** Lamps, signs and canopy lights never move — a lightmap on the road, sidewalks and the
  lower facades replaces ~600 per-fragment evaluations with one texture read and adds the lamp *shadows* (lamp posts, trees,
  parked cars) that no runtime light casts now. Keep the grid for the dynamic entries only (headlights, beacons, flashes): the
  data path already separates them (`count` vs `dyn`).
- **Baked AO** replaces the skirts, blobs and vertex ramps in one go; keep the blobs under moving cars and people.
- **Real emissive textures** replace the window quads: a window texture with an emissive mask on the facade material gives
  curtains, half-lit rooms and proper glass instead of flat squares; keep the per-building hash so towers still differ.
- **Roughness/normal maps** on the road replace the noise puddles; wet-asphalt normal detail is what makes the smears break up.
- **Reflection probes or an SSR pass** once the frame runs at native resolution on the target machine — the road material is
  already set up for it (low roughness, dielectric).
- **An HDRI dusk sky** replaces `makeSky` and the PMREM from it; the fog colour must follow it.
- **Volumetric headlights** (a cone mesh with a depth-faded additive shader) replace the flat pools if the phase-2 machine has
  the fill-rate; the spot lights in the grid stay as they are.

## 9. ROUND 4 — the real assets wired in (phase 2 on the game side)

Round 4 changed what the game is made of, not what it does: every placeholder box is gone and the Blender GLBs of
`phase2-assets/out/` (22 files, 20.2 MB, PNG textures) drive the same gameplay code through the same factory functions.
Nothing in `player.js`, `vehicles.js`, `npcs.js`, `weapons.js`, `police.js`, `camera.js`, `world.js` or `defs.js` was touched.
The rendering-side files that changed: `assets.js` (factories), `loader.js` (new), `main.js` (async start, hooks), `props.js`
(instancing layout, shadow policy), `lighting.js` (two lines: additive emissive quads), `template.html` (progress bar).

### 9.1 What ships, how to rebuild
- **Folder, not a file:** `game.html` + `assets/` (must sit next to each other). `assets/` holds six family GLBs
  (`vehicles.glb`, `characters.glb`, `weapons.glb`, `buildings_city.glb`, `buildings_industrial.glb`, `props.glb`), the Basis
  transcoder (`assets/basis/basis_transcoder.{js,wasm}`, from three r180), `manifest.js` (sizes for the progress bar) and, for
  every one of those files, a `.b64.js` sidecar (section 9.2). `assets/PACK-REPORT.json` is the size report of the last pack.
- **Rebuild assets:** `node pack-assets.mjs` (options `--skip-ktx`, `--only=family`, env `PACK_OUT=dir` to pack beside a live
  `assets/`). It imports the gltf-transform 4.5 JS API from the npx cache (`~/.npm/_npx/f28f967467b6a518/node_modules`) and
  shells out to the CLI for the KTX steps, which need KTX-Software ≥ 4.4 (`ktx`) on the PATH. That binary is not on this Mac by
  default: the 4.4.2 `.pkg` from github.com/KhronosGroup/KTX-Software was expanded without installing (`pkgutil --expand-full`),
  `install_name_tool` pointed `ktx`/`toktx` at `@executable_path/libktx.4.dylib`, ad-hoc `codesign`, result in `/tmp/ktxbin`
  (volatile — redo after a reboot; the parallel instance left the same payload in `~/bin/ktx-4.4.2`, which needs
  `DYLD_LIBRARY_PATH` instead). The CLI's `--slots` takes a comma list, not `{a,b}` braces.
- **Rebuild the page:** `node build.mjs --minify` (unchanged; the Basis worker survives minification because its body only
  references globals). Then `node test/quick.mjs` (file://) and `node test/quick.mjs --http`.

### 9.2 Loading (`src/loader.js`) — start fast, stream, then build
- The page is visible immediately (start card + progress bar from the HTML); `main()` creates the renderer, loads all six
  families in parallel, then builds the city (`boot()`), then flips the card to "Click to play". **A click during loading is
  remembered** and starts the game the moment the build is done — this is what keeps the gate and the old tests working (they
  click 1.5–2.5 s after navigation).
- **Two transports, one path afterwards.** Over http(s) the loader uses `fetch()` with a streaming reader, so the bar moves per
  chunk (byte totals come from `manifest.js`). From `file://` — a double-clicked `game.html`, the gate, every test — Chrome
  refuses `fetch()` for sibling files, but `<script src>` works: each packed file also ships as `<file>.b64.js`, a script that
  calls `__assetChunk(name, base64)`; the loader inserts those tags in parallel and turns the payload into an ArrayBuffer with
  `fetch('data:…')` (native decode, no byte loop). After that both paths call `GLTFLoader.parse()` on the same bytes. The KTX2
  transcoder reaches `KTX2Loader` through `LoadingManager.setURLModifier` (data URLs in file:// mode, plain files over http);
  the transcoder workers are Blob workers, which file:// allows.
- Decoders: `EXT_meshopt_compression` via three's `meshopt_decoder.module.js` (WASM embedded in the bundle, no download),
  `KHR_texture_basisu` via `KTX2Loader` (4 workers max; on this Mac Chrome reports ASTC, so the textures land as ASTC 4×4 — BC7 /
  ETC2 on other GPUs, decided at runtime by `detectSupport`).
- Registry: `ASSETS.vehicles[type] = { lod0, lod1, lod2 }`, `ASSETS.characters[variant]`, `ASSETS.weapons[type]`,
  `ASSETS.buildings[kind]`, `ASSETS.props[kind]`, every material in `ASSETS.materials` (handed to the light-grid patch through
  `G.extraMaterials`; paint clones made later go through `ASSETS.onNewMaterial`).
- **Trap fixed in `register()`:** `GLTFLoader` makes node names unique per file (`body` → `body_1` for the second car in the merged
  vehicles file, `Hips_3` for the fourth rig). The contract names are restored from the exporter's `extras.name` (Blender writes
  it into `userData.name`), falling back to stripping a `_<digits>` suffix. Without this every car but the first lost its wheels.
- Measured (MacBook, headless Chrome, file://): 5.9 MB in 0.3 s when the machine is quiet (0.7–1.3 s under the load average of
  25–30 this afternoon had), 0.3 s more to build the city, ~1 s of shader warm-up (a hidden cruiser, officer and the three weapons
  are compiled once at boot so the first chase does not hitch). Over http the same numbers plus network time.

### 9.3 Packing (`pack-assets.mjs`) — sizes before / after
1. **Merge per family + dedup.** 8 vehicle GLBs → one document (the trim and wheel texture sets existed 8×, now once), 8
   character GLBs → one (identical normal maps deduplicated), 3 weapons → one (one gun atlas). Roots renamed
   (`Vehicle_police_lod1`, `CharacterRig_civ3`) so everything is addressable after the merge; one scene per family.
2. **Dropped:** `TANGENT` (three derives tangents per pixel; 16 bytes/vertex saved) and `TEXCOORD_1` (no lightmaps this round —
   the source files keep both).
3. **Geometry:** reorder + quantise (UV 14 bit, colour 8, weights 8, normals octahedral 8 via the Meshopt filter) +
   `EXT_meshopt_compression` (FILTER method). **Positions stay float32 on purpose:** gltf-transform's quantiser folds the
   dequantisation scale/offset into the node transforms, and the game overwrites the wheel nodes' `position.y` / `rotation`
   every frame and instances `Building_*` / `Prop_*` geometry directly — both would have gone wrong. The cost is ~0.7 MB across
   all families; Meshopt still compresses float positions well.
4. **LODs at pack time:** the shipped `*_lod1` cars (10.2–11.2 k tris) are run through the Meshopt simplifier to ~55 %
   (5.8–6.3 k, error ≤ 0.6 %) as LOD1, and again to ~33 % (3.4–3.5 k, error ≤ 2 %) as LOD2 — lenses, brake lights and beacons are
   never simplified. Checked in `test/viewer.mjs` (`shots/`-style sheets in `/tmp` during the round): silhouettes intact.
5. **Textures → KTX2 with full mip chains:** UASTC (level 2, RDO λ 1.0, zstd 18) for every normal map and for the vehicle /
   character / weapon albedos (paint panel lines, the POLICE lettering, faces), ETC1S (quality 180–220, compression 2) for the
   building and prop albedos and every ORM. Anisotropy 4 on all maps.
6. Sidecars + manifest, then the report:

| family | source (22 PNG GLBs) | packed | ratio | sidecar (base64) |
|---|---|---|---|---|
| vehicles (4 + LOD1 + LOD2) | 11 384 KB | 3 320 KB | 29 % | 4 427 KB |
| characters (8 rigs) | 3 199 KB | 374 KB | 12 % | 499 KB |
| weapons (3) | 1 328 KB | 264 KB | 20 % | 352 KB |
| buildings_city (13 kinds) | 2 681 KB | 1 196 KB | 45 % | 1 595 KB |
| buildings_industrial (4) | 1 166 KB | 463 KB | 40 % | 617 KB |
| props (19 kinds) | 973 KB | 405 KB | 42 % | 540 KB |
| **total** | **20 731 KB** | **6 021 KB (29 %)** | | **8 789 KB** incl. transcoder |

The vehicle family is the largest because its albedos are UASTC (the police livery is 2048×1024); ETC1S there would save ~1.5 MB
at visible cost on the lettering. GPU memory matters more than disk: `gltf-transform inspect` puts the source PNGs at ~360 MB
decompressed (every 1024² RGBA8 map is 5.6 MB, the city trim sheet 22 MB each), the KTX2 set lands at roughly a quarter of that
as ASTC 4×4 (8 bpp) and an eighth for the ETC1S maps. `renderer.info.memory.textures` reports 61–63 textures in flight.

### 9.4 The factories (`src/assets.js`) — contract → asset
- **Characters:** `makeCharacterRig(variant, scale)` = `SkeletonUtils.clone` of `CharacterRig_<variant>`; `bones` by name from
  the cloned skeleton, `mesh` = the armature node (so `mesh.position.y` lifts the whole figure), `socket` = the GLB's
  `WeaponSocket` under `Hand_R`. Frustum bound: an explicit `boundingSphere` (r 1.7 m at hip height) instead of per-frame skinned
  bounds. Player → `player`, officers → `officer` (cap and belt are in the mesh), pedestrians → `civ0…civ5` by the NPC rng.
- **Vehicles:** one group with three LOD hierarchies (`lod0`, `lod1`, `lod2`; LOD0 first so `getObjectByName('body' | 'lights'
  | 'brakeLights' | 'wheel_*' | 'beacon_*')` finds the gameplay parts there). Paint: per-colour clone of the body material with
  `color = hex`; police keeps the livery texture. `lights` gets `MAT.lightsOff` (the game swaps to `MAT.lights` when driven),
  `brakeLights` `MAT.brake`, beacons the `MAT.beacon*` pair, wreck = `MAT.wreck` as before. `updateLods(G)` (called once per
  frame from `main.js`) switches levels at 48 / 110 m with hysteresis (42 / 100), never for the player's car, and mirrors the
  LOD0 state onto the shown level: body material (paint or wreck), lens material, brake visibility, wheel pose, beacon materials.
  Only LOD0 casts shadows.
- **Weapons:** `Weapon_<type>.clone()` — `body`, `muzzle`, `loadedRocket` are the GLB's.
- **Buildings / props:** the `Building_<kind>` / `Prop_<kind>` meshes are the InstancedMesh prototypes. The placeholder builders
  still run once per kind — they record the glass bands the emissive window layer positions its quads by (and keep the world's
  rng sequence identical, so the city layout is the phase-1 one). A white `COLOR_0` is added to every prototype and the round-3
  vertex-AO ramp (`baseAO`, lowest 3.2 m of a building to 62 %, static props to 60 %) is written into it; the family material
  runs with `vertexColors` so instance tint × AO × texture multiply as before. Prop collision numbers are the phase-1 table
  (`PROP_DATA`), which the GLBs were built to.
- Materials from the GLBs are `MeshStandardMaterial`s and go through the light-grid patch like everything else (the grid still
  lights them — there are still no three.js point lights). Glass: transparent, opacity ≤ 0.5, no depth write, double-sided.

### 9.5 What was retuned for PBR and why
- **Car paint.** The paint ORM ships metalness ≈ 0.63 / roughness ≈ 0.42; under the blue-hour environment map a metal has no
  diffuse and every car became a dark mirror. The paint clones set the material scalars to metalness 0.45 / roughness 0.85
  (they multiply the maps → ≈ 0.28 / 0.36, the round-3 paint response) with `envMapIntensity` 1.35 so the horizon band still runs
  across the roof. Dark palette entries (`#3b4a3e`, `#1f1f24`) still read dark — that is the palette, not the material.
- **Emissive windows and signs draw additively now** (`lighting.js`: `AdditiveBlending`, no depth write, fog fades the glow
  instead of tinting it). Over the textured facades a lit window glows through the trim sheet's frames and mullions instead of
  covering them with a flat card, and an unlit one adds nothing so the texture's dark glass shows. Shop units dropped from
  1.15× to 0.95×.
- **Shadow budget.** The shadow pass now carries real meshes: 4096² → 3072² over ±80 m (5.2 cm texels), props cast shadows only
  where a shadow reads at dusk (crowns, bins, boxes, benches, planters — not the 434 lamp posts), pedestrians cast none beyond
  45 m and are hidden beyond 130 m, LOD1/LOD2 cars cast none. `test/probe-perf.mjs` attributed ~3–5 ms of the frame to the shadow
  pass before this.
- **Static props in world cells.** `props.js` builds one InstancedMesh per kind *per 120 m cell* for static kinds (dynamic kinds
  stay one mesh each, they move). An InstancedMesh's bound spans all its instances, so before this every lamp, wall segment and
  tree in the city was drawn on both passes whatever the camera looked at (props alone were 335 k triangles per pass); now the
  frustum culls whole cells. Draw calls went up by ~40, triangles per frame roughly halved.
- **Adaptive resolution.** Real meshes and four texture reads per pixel cost more per fragment than flat vertex colours; on a
  retina display at DPR 1.5 (round 3's cap) the frame would not hold 60 fps. The renderer now starts at DPR 1.25 (cap 1.5),
  steps down by 0.25 (min 0.8) after 3 s under 56 fps, and steps back up after 12 s at 60 fps unless that just failed. `G.dpr`
  / `__dbg.state().dpr` show the current value; headless tests run at DPR 1 and never trigger it.
- Not changed: sky, key/hemisphere lights, fog, the light table (596 static lights), bloom / grade / vignette, the wet-road
  material and the headlight pools — the dusk look of round 3 carries over unchanged; the gate view measures 65 / 22 % near-black
  exactly as in round 3 (section 9.6).

### 9.6 Measured (minified build, MacBook GPU via Metal, headless Chrome 1280×720)
All numbers from the final minified build (`game.html` 1 040 KB + `assets/` 5.9 MB), taken this afternoon on a machine whose load
average was **20–30 the whole time** (other sessions were running their own batteries) — the uncapped numbers are therefore
pessimistic; round 3's 4.1 ms was measured on a quiet machine. Vsync-locked 60 fps held in every play-through state.

| what | result |
|---|---|
| Load (`test/quick.mjs`, file://) | assets 5.9 MB in **0.3–0.7 s** (1.3 s under load), city build + shader warm-up ≈ 1 s more; page visible with progress bar from the first frame |
| Load over http (`--http`) | same bytes streamed with byte progress, 1.6 s incl. server, 0 console errors (favicon now `data:`) |
| Gate `pruefe_openworld.mjs` | **GREEN — mean 86.1, 18.7 % near-black (limit 33), bottom half 119.6 / 9.8 % (limit 50), 0 console errors** (round 3: 65.0 / 23.1 %) |
| `test/look.mjs` (same viewpoints as round 3) | spawn 65.3 / 22.5 % (round 3: 64.8 / 23.2), shops 85.8 / 18.6 %, gas 80.5 / 13.3 %, drive 44.7 / 42.8 % (round 3: 42.4 / 44.3), 0 console errors |
| `test/play.mjs --gpu` | all states pass (walk, sprint, jump, enter / drive / brake / handbrake / exit, weapon wheel with bullet time, pistol, MG, rocket, under fire), **60 fps, 0 console errors, 0 warnings** |
| `test/vehicles-shots.mjs` | sedan, muscle, van driven, cruiser spawned and driven with siren, close-ups of player / officer / pedestrian / three weapons / lamp / tree / both police doors → `shots/assets_*.png`, `shots/assets-closeups-runde4.png`; 0 console errors |
| `test/camera.mjs` | **PASS** — 12 scenarios, 4 687 frames, worst streak 1 bad frame (limit 6), 0 console errors |
| `test/police.mjs` (run 2, full) | 1★ after the first witnessed shot, cruiser within 45 s, officer out and firing, officer killed → 4★, 3★ chase with 2 cruisers within 40 m and 5 impacts, roadblocks, 5★ with 8 cruisers, evasion 2★ → 1★ → clear; **1 failed check: the 5★ fps floor (min 0.5-s window 48 fps, threshold 55)**. Run 1 failed the 1★ arrival (the documented nondeterminism) and the same fps window (54). 0 console errors both runs |
| Uncapped frame time (`test/feel.mjs`, two runs) | spawn view **11.0–11.8 ms** (88 fps), downtown overview **8.2–12.8 ms**, 322–355 draws, 760–820 k triangles (round 3: 4.1 ms / 245 fps, 284 draws, 490 k) |
| 5★ chase uncapped (`test/perf5.mjs`, two runs) | run 2: **mean 12.2 ms, p50 12.2, p95 16.7, p99 20.2, max 39 ms; 93 of 1 875 frames (5 %) over 16.7 ms** — 10 cruisers, 4 officers, 10 sirens, 285 draws, 696 k tris. Run 1 (load 29): mean 15.1, p95 21.7, p99 34 (round 3: mean 4.4, p95 6.1, p99 8.1) |
| Where the frame goes (`test/probe-perf.mjs`) | at load 20 every toggle sits inside ±1.5 ms of noise; the reproducible ones: all vehicles hidden −2 to −3 ms, props hidden −1 to −2.5 ms, shadow map off −1 to −4 ms, NPCs hidden −1 to −2 ms; normal / ORM maps, bloom and the 2048² shadow map made no measurable difference |
| Triangles per frame | 550–840 k in play (was 1.25–1.35 M before the LOD2 / prop-cell / shadow-policy pass), 590–700 k in a chase |
| Sizes | source 20 731 KB → packed 6 021 KB (29 %); base64 sidecars 8 789 KB; `game.html` 1 040 KB minified |

**Honest reading of the frame-rate rule.** At 1280×720 the phase-2 city renders in 8–13 ms uncapped under this machine's load, i.e.
60 fps with headroom in normal play; a 5★ chase averages 12 ms with 5 % of frames over the 16.7 ms budget and 0.5-s windows down
to 48 fps — the police test's 55-fps floor is not met in either run. Round 3 was three times cheaper per frame; the difference is
real geometry and four texture reads per pixel, and this round's LOD / culling / shadow-budget pass roughly halved the triangle
load without reaching round 3's number. On a retina display the adaptive resolution (section 9.5) is what keeps 60 fps; at DPR 1.0
in 720p the numbers above apply. The next steps that would buy the rest are listed in 9.8 (instanced skinning, a lighter
shadow-caster set, dropping normal maps on far materials).

### 9.7 The "mirrored POLICE" defect — checked, not present in the shipped GLB
The brief reported the door lettering reading backwards on both sides. `test/viewer.mjs` (real Chrome + three.js `GLTFLoader`, the
same path the game uses) rendered `vehicle_police.glb` and `vehicle_police_lod1.glb` from both sides and zoomed on both doors
(`shots/police_lettering_check.png`, `shots/police_lettering_sides.png`): POLICE reads forwards on the left door (P at the front)
and on the right door (P at the rear), i.e. left-to-right for a viewer on either side, in LOD0 and LOD1 — and in the running game
(`shots/assets_police_left_door.png` / `_right_door.png`). The albedo has the left-door region baked mirrored and the left door's
UVs mirrored to match, which is why a look at the texture alone suggests a defect. No UV or decal change was made; the check is
kept as a test so the next texture revision is caught.

### 9.8 What still looks weak (and what to do about it)
- **The character model** (as flagged in the brief): tube arms with a visible shoulder seam, stub hands, a single mesh per
  variant. It reads at gameplay distance; the close-ups (`shots/assets_weapon_mg.png`, `shots/assets_officer_closeup.png`) show it. Not rebuilt in this
  round — next: a modelled shoulder, hands with fingers, one texture with a tint mask instead of eight atlases.
- **Lit windows are still quads, not textures**: the emissive layer's hash-lit quads sit on the trim sheet's window bays; an
  emissive mask in the facade material would give curtains and half-lit rooms and drop ~15 draw calls.
- **Shop units** are still flat cards over the shopfront glass; additive blending softened them but they do not show interiors.
- **No baked lighting / AO** — the source UV2s exist but were dropped; the round-3 skirts, blobs and vertex ramps still do the
  contact darkening. Lightmaps would also add the lamp-post and parked-car shadows the runtime cannot cast.
- **LOD pop at 48 m** is visible on a car that crosses the threshold while you watch it (no cross-fade); LOD2 at 110 m is fine.
- **Trees** are the icosphere-crown models (solid blobs); leaf cards with alpha would sit better in the lamp light.
- **Glass** is a flat tinted pane; no interior beyond the shrunken shell, so a car close up looks empty from the side.
- **Wide dusk shots look close to round 3** (`shots/vorher-nachher-runde4.png`): the assets were built to the placeholder
  dimensions and the blue hour hides surface detail at 50 m; the gain is in everything within ~25 m — cars, people, weapons, lamps,
  shopfronts (`shots/assets-closeups-runde4.png`). More contrast in the facade textures and lit-window textures would carry it further.
- **Draw calls** are 300–530 per frame (LOD hierarchies add none; prop cells added ~40). Skinned pedestrians are 1 draw each on
  both passes — instanced skinning (a per-instance bone texture) would fold 60+ draws into one and is the next performance step.
- **The frame on a retina display** relies on the adaptive resolution to stay at 60 fps (section 9.5); a full-resolution retina
  frame is not 60 fps with this many PBR pixels.
- **Duplicate instance note:** the duel harness started this round twice (11:51 and 11:54). The second instance (session
  `…-18`) stood down after a message exchange; its findings (ASTC transcode target, ORM R = 255 everywhere so no AO map, the
  mirrored-texture explanation for the lettering) are folded in above, its per-file compression outputs were removed.

## 10. ROUND 5 — the radio and the screens wired in (audio and video only)

Round 5 added sound and moving pictures from `phase2-medien/out/` and nothing else: no gameplay, lighting or asset file
was touched. Files changed: `audio.js` (the `Radio` class and `meter()`), `screens.js` (new), `loader.js` (four helpers
exported, no behaviour change), `main.js` (construct `Screens`, start playback on the click, one `update` line, two debug
calls), `ui.js` + `template.html` (the station line under the speedo, "R radio" in the control strip), `pack-media.mjs`
(new), `test/media.mjs` (new). `phase3-lightmaps/` and `phase2-medien/` were not written to.

### 10.1 What ships, how to rebuild
- `node pack-media.mjs` copies the four station loops and the two clips into `assets/radio/` and `assets/screens/` and
  writes `assets/radio/stations.js` (the list) plus one `.b64.js` sidecar per media file (`__assetChunk('radio/<file>', b64)`,
  the round-4 scheme) and `assets/MEDIA-REPORT.json`. Source of truth for names, titles and files is
  `phase2-medien/out/radio_manifest.json`; the optional fifth station and third clip in `out/extra/` are not shipped.
  Then `node build.mjs --minify` (1051 KB) and `node test/media.mjs` / `--http`.
- Sizes: radio 3.2 MB OGG + 4.2 MB sidecars; screens 2.6 MB WebM + 4.0 MB MP4 + 0.13 MB posters + 3.6 MB sidecars
  (`assets/` 34 MB in total, of which the game loads at most 6 MB GLBs + ~2.7 MB screens at start and ~1 MB per station on
  first use). The MP4s have no sidecar: they are the http fallback for browsers without VP9 only.
- **Two transports, as for the GLBs:** over http the radio `fetch()`es the OGG and the `<video>` streams the WebM; from
  `file://` the bytes come through the sidecar script and `fetch('data:…')` (audio) or a `blob:` URL (video, poster). The
  blob detour is not optional: a `<video src="file://…">` plays, but `texImage2D` on it throws a SecurityError (cross-origin
  taint — every file:// URL is its own origin in Chrome); a blob URL made by the page is same-origin. Same for the poster
  JPEG (`data:` URL in file:// mode).

### 10.2 The radio (`class Radio` in `audio.js`)
| R | station (HUD) | title | file | character |
|---|---|---|---|---|
| 1 | NEON DRIVE 104.6 | Night Grid | radio_neon_drive.ogg | synthwave, instrumental, 108 BPM |
| 2 | SUNSET FM 88.1 | Take the Long Way Home | radio_sunset_fm.ogg | 80s city pop, female vocal |
| 3 | BLUE NOTE 91.3 | After Hours | radio_blue_note.ogg | late-night jazz trio |
| 4 | BLOCK RADIO 97.9 | Seven by Seven | radio_block_radio.ogg | boom-bap hip-hop, rap |
| 5 | RADIO OFF | | | then back to 1 |

- **Keys.** R in a car cycles the positions above (a short burst of static between them). R on foot stays reload. M is
  the master mute as before — the radio runs through the master, so it mutes with everything else and the bus keeps
  running underneath (verified: master RMS 0, radio bus unchanged).
- **Belongs to the player, not the car.** Get out and the radio keeps playing from the car: muffled (lowpass 900 Hz) and
  spatialised at the car (panner ref 4 m, max 140 m), so walking away fades it (measured: RMS 0.013 next to the car, 0.0025
  at 42 m). Get into any car and it is dry again, same station, same position. A wrecked car takes its radio with it
  (`off()`); the next R starts at station 1.
- **Every station broadcasts continuously.** The first tune-in starts at a random offset; switching away and back resumes
  where the station would be now (an epoch per track, `s.start(t, offset)`), so the four stations feel like four channels
  rather than four files. `loop = true` over the whole buffer — the loops are cut on bar boundaries by phase2-medien, no
  `loopStart/End` needed.
- **Graph.** `AudioBufferSourceNode → trackGain (0.55) → [inside gain → bus radio]` and `[outside gain (0.9) → lowpass →
  panner → bus radio]`; the two gains crossfade (τ 0.12 s) on enter / exit. The bus `radio` is still 0.55 (unchanged from
  phase 1). Louder / quieter: `RADIO_TRACK_GAIN` at the top of the class, nothing needs re-encoding.
- **Level, measured on the buses** (`__dbg.audio().levels`, RMS, analysers created on demand, muscle car): idle engine
  0.074 / radio 0.040 (radio −5.4 dB), full throttle 0.242 / 0.045 (−14.6 dB), coasting 0.078 / 0.038 (−6.2 dB); a cruiser
  with siren at 5 m: sfx 0.136 / radio 0.038 (−11 dB). Under the engine and the sirens, audible at idle — by design.
- **Loading.** The list (`stations.js`, 0.7 KB) is loaded on the start click (`preload()`); the bytes of a station on its
  first R (sidecar 1 MB or fetch 0.8 MB, `decodeAudioData` ≈ 50–100 ms, cached — ≈ 20 MB float32 per station, 80 MB for all
  four). A late decode cannot overtake a newer R (generation counter). Failures (404, Safari without Vorbis) show
  `<station> · NO SIGNAL` in the HUD and the reason in `__dbg.audio().radio.error`.
- **HUD.** Two lines under the speedo (`#radio`): `♪ STATION` and the title (`tuning…` while decoding, `RADIO OFF · R` when
  off, dimmed). The centre message on R is unchanged. `Radio.hud()` returns the two strings, `label()` joins them.
- **The hook is still open.** `RADIO_STATIONS.push({ name, tracks: [{ title, data: url | 'data:audio/ogg;base64,…' }] })`
  works as before; a track has either `data` (anything `fetch()` reads) or `file` (a name under `assets/radio/`). More
  tracks per station = more entries in `tracks` (random pick per tune-in); more stations = more entries in
  `radio_manifest.json` + `node pack-media.mjs`.

### 10.3 The screens (`screens.js`)
- **Where.** Every `shop_row` carries a rooftop billboard (8 × 4.5 m screen, local (−8, 11.5, 5.92) facing +Z, on a 0.3 m
  board with two posts down to the roof deck at y 8.0 — the neon sign board of the asset occupies x 3…13, the billboard
  stands left of it) showing `screen_billboard_car` (black sports car in neon rain, camera drifts in and back). Shop windows
  get `screen_shop_drink` (blue can, condensation): a 3.2 × 1.8 m screen with a thin bezel hanging in the window at local
  z 7.33 (glass at 7.0, the emissive unit quad at 7.22 — the screen is in front of both and opaque, so the additive glow
  does not wash it out), 1.6 m up; two of the four units per `shop_row` (alternating by instance) and one window in every
  second `shop_small`. City of round 4: 4 billboards + 8 + 22 = 30 window screens. Table `PLACE` at the top of the file.
- **How.** One `<video>` (muted, loop, playsinline) + one `VideoTexture` per clip, shared by all its screens; one
  `InstancedMesh` per clip with the building matrices × the local offset, one more per frame type. Cost: two texture
  uploads per new video frame (three r180 uses `requestVideoFrameCallback`, so 24 per second per clip, not 60) and four
  draw calls. Material: `MeshBasicMaterial` (unlit, `toneMapped: false`) at 1.35× so the bright parts cross the bloom
  threshold like the neon; black until the poster is in, poster until `loadeddata`, then the video (the poster is frame 0,
  the swap is invisible). Frames: one dark `MeshStandardMaterial` registered through `noteMaterial()` so the light grid
  patches it like every other material (constructed after `ASSETS.onNewMaterial` is set — order matters in `boot()`).
- **Codec.** WebM/VP9 when `canPlayType('video/webm; codecs="vp9"')` says so (Chrome, Firefox, Playwright-Chromium),
  else `.mp4` (http only — see 10.1). Playback starts in `begin()` (start click); `update()` retries `play()` every 2 s
  while a clip is paused (Chrome sometimes refuses before a gesture). Both clips are 12 s ping-pong loops, `loop = true`.
- **Not done, on purpose:** the screens do not spill light (no light-grid entry — "no lighting changes"). If the lightmap
  round wants them to, one `addStatic` per screen instance with the clip's mean colour is all it takes (positions are in
  `PLACE`, matrices in `Screens` constructor). No screen-space reflection of the screens either (8.5).

### 10.4 Verified (final minified build, MacBook GPU via Metal, headless Chrome 1280×720, `--mute-audio`)
- `node test/media.mjs` (file://) and `--http`: all checks pass in both modes — AudioContext running; four stations in
  order with RMS on the radio bus 0.017–0.039 each (0 before the first R); HUD line per station (screenshots
  `shots/media/hud_1…4.png`); fifth R off (bus RMS 0), sixth wraps; radio under the engine at full throttle; exit → still
  playing, muffled, fades to 0.0025 at 42 m; re-enter → dry, same station, position advanced by the elapsed time; M → master
  0 with the bus alive, M again → back; both clips readyState 4, not paused, `currentTime` advancing, 1248 × 704,
  VideoTexture bound, 0 dropped frames (file), 0–11 (http); 60 fps; 0 console errors. `shots/media/billboard.png` (rooftop
  billboard over a shop row from the street) and `shopscreen.png` (a window screen) were looked at.
- `node test/quick.mjs` file + http: 60 fps, 0 errors, load 0.7 s / 1.2 s; the reference views unchanged within noise
  (spawn mean 86.3 / 19.1 % dark). `node test/look.mjs`: 0 errors, 60 fps, spawn 65.2 / 22.5 % (round 4: 65.3 / 22.5 %).
  The duell gate (`pruefe_openworld.mjs`): GREEN, mean 65.2 / 22.7 % near-black (limit 33 %), 0 console errors.
  `node test/play.mjs --gpu` on the final build: 60 fps, 378 draws, 0 errors, 0 warnings (walk, car, wheel, three weapons, 3★).
- Headless audio is real: with `--mute-audio` Chrome still renders the graph (the analysers read the buses), so the
  numbers above are the audio graph, not "no exception".
- Known limits: Safari decodes neither Vorbis nor VP9 (radio → NO SIGNAL, screens → MP4 over http, dark from file://);
  `decodeAudioData` keeps 20 MB per station; the radio has one owner (the player) — AI cars have no radios.


## 11. ROUND 6 — the baked lightmaps applied (2026-09-02, 14:12–14:45)

The phase-3 bakes (`phase3-lightmaps/out/`, recipe in `phase3-lightmaps/NOTES-lightmaps.md` §3) are wired into the game. Buildings and the
city floor now take their sky light and every **static** artificial light — direct **with shadows** plus all bounce — from the KTX2 atlases;
the key light (dynamic shadows), the dynamic grid lights (headlights, tail lights, beacons, flashes, muzzle), the emissive layer, glow
sprites, headlight pools, blob shadows, fog and the post chain are untouched. Cars, people, props and weapons keep the round-3 real-time
path (hemisphere + env + grid). Gameplay code was not touched. System A / the GPU were not used — everything below ran on the Mac.

### 11.1 What changed, file by file
- **`pack-assets.mjs`** — the two building families are read from `phase3-lightmaps/out/assets-uv2/` (the phase-2 GLBs with the repacked
  TEXCOORD_1) and **keep `TEXCOORD_1`**: only `TANGENT` is dropped for them, and `prune()` runs with `keepAttributes: true` for them
  (with `false`, gltf-transform prunes every TEXCOORD no texture references — it would have thrown the channel away again after the
  explicit drop was removed). The packer verifies per primitive that TEXCOORD_1 survived and throws otherwise (report field `texcoord1`).
  The eight KTX2 maps are copied next to the GLBs, get `.b64.js` sidecars and manifest entries, and `lm-layout.json` is slimmed
  (index / kind / x / z / rot / rect per building, districts, `lm_scale`, `districtOfTemplate`) into `assets/lm-layout.js` — a plain
  script like `manifest.js`, so it loads from `file://` too. `~/bin/ktx-4.4.2` is on the packer's PATH as a fallback for `/tmp/ktxbin`.
  Cost: buildings_city 1 196 → 1 245 KB, buildings_industrial 463 → 468 KB (the quantised 14-bit UV1); the maps 25.8 MB on disk,
  their sidecars 34 MB. Other families are byte-identical to round 5 (`--only=buildings_city,buildings_industrial` was used).
- **`src/loader.js`** — loads `assets/lm-layout.js`; if it exists and all eight maps are in the manifest, the maps are fetched like the
  GLBs (streaming over http, sidecars from `file://`) and parsed with the same `KTX2Loader` (`parse()` on the bytes; UASTC → ASTC 4×4 on
  this Mac, ETC1S AO → the same). `_lm` textures are forced to `SRGBColorSpace` (the file's DFD says so already — the decode is part of the
  encoding), `_ao` to `NoColorSpace`, anisotropy 4, `flipY` false. `ASSETS.lightmaps = { districts: {downtown|midtown|industrial:
  {lm, ao, scale}}, ground: {lm, ao, scale}, byIndex: Map(world.buildings index → {district, kind, x, z, rot, rect}), districtOfTemplate }`,
  or `null` when nothing is shipped — then the whole game runs exactly as in round 5. Progress bar and file count include the maps.
- **`src/world.js`** — `instanceBuildings()` groups by **(kind, district)** instead of by kind: the 15 placed kinds → 17 `InstancedMesh`es (only `shop_small` and `fountain` span two districts)
  (`Buildings_<kind>_<district>`), each with a geometry that shares the prototype's vertex buffers and owns one `lmRect`
  `InstancedBufferAttribute` (vec4 `[u0, v0, su, sv]` in glTF UV space, from the layout by index — verified against kind, x, z, rot;
  a mismatch falls back to the template's district and warns; 141 / 141 matched). The family material is cloned once per (family,
  district) (`lmMaterial()`, 5 clones), `vertexColors` off, `userData.lightmap = { mode: 'instance', lm, ao, scale, district }`. Tints are
  drawn in the old list order before grouping, so the RNG sequence — and every tint the bake was lit with — is unchanged.
  `buildingMeshes` stays keyed by kind: `{ list, meshes, matrixAt(i, m) }`, and every building record carries `im` + `slot`
  (`lighting.js` and `screens.js` read `b.im.getMatrixAt(b.slot, …)` now). Road, slabs, lane marks and crosswalks get
  `userData.lightmap = { mode: 'world', … }` from `groundLM()` — the terrain outside ±255 m is not in the map and stays real-time.
- **`src/lighting.js`** — `patch(mat, { road, lm })`: for a lightmapped material the vertex shader writes `vLmUv` (instance: `uv1 *
  lmRect.zw + lmRect.xy`; world: `((x + 255) / 510, (255 − z) / 510)` from the world position the patch already computes), the fragment
  shader replaces `<lights_fragment_maps>` by `irradiance += texture2D(uLM, vLmUv).rgb * uLMScale` and `radiance += getIBLRadiance(…) *
  texture2D(uAO, vLmUv).r` (env diffuse gone, env specular occluded by the baked AO), the hemisphere term is neutralised, and the grid
  loop stops at the first static id (`lgIdF < lgStatic` → `break`; a cell lists its dynamic ids first, so the dynamic lights keep working
  on lightmapped surfaces; `lgStatic` is a new shared uniform = `staticCount` = 596). `LM_MODE_INSTANCE` is a material define, `uv1` is
  declared only when three has not (`#ifndef USE_UV1`). Program cache keys: `lgLinstance`, `lgRLworld` (road), `lgLworld`. The AO skirts
  are not built when the bake is present (the ground map carries the plinth contact); blob shadows stay.
- **`src/assets.js`** — `makeBuilding(kind, rng, { baked })`: with `baked` the vertex-colour AO ramp is not applied and no COLOR attribute
  is added (the bake has the contact darkening); `screens.js` — one line (matrix lookup).
- **The one thing the recipe got wrong, and why it matters:** `NOTES-lightmaps.md` §3.5 removes the hemisphere with a regex on
  `shader.fragmentShader` inside `onBeforeCompile`. At that point the shader is still the unexpanded template — the hemisphere line lives
  inside the chunk `<lights_fragment_begin>` — so the regex never matches and the hemisphere (1.05 × #40608f / #1a1826, i.e. the whole
  blue-hour ambient) stays on top of the bake. `preview/viewer.mjs` has the same no-op, so its `out/verify/*_lm.png` shots are
  hemisphere-double-lit. The game inlines `THREE.ShaderChunk.lights_fragment_begin` with that line neutralised instead (`LOOP_FRAG_LM`),
  and warns at module load if the line is not found. First build with the no-op: spawn mean 73.7 / 18.4 % dark; fixed: 73.5 / 18.7 % —
  the difference is small because the hemisphere is weak next to the lamps, but it was the wrong kind of small.

### 11.2 Verified (minified build, MacBook GPU via Metal, headless Chrome 1280×720)
`node test/look.mjs --out=shots/lm` — same viewpoints as `shots/ov_*.png`; the side-by-side strips are `shots/lm/compare_<view>.png`
(round 5 left, round 6 right) and `shots/lm/crop_{shops,gas,street}.png` at full resolution. 60 fps, 0 console errors, 0 warnings
after the hemisphere fix (`lights 596 dyn 15`).

| view | round 5 mean / % near-black | round 6 mean / % near-black | what changed in the picture |
|---|---|---|---|
| 01_spawn | 66.2 / 22.3 | 73.5 / 18.7 | tower facades sky-lit with a gradient instead of flat; lamp pools soft with post shadows |
| ov_shops | 86.2 / 18.7 | 77.5 / 25.7 | neon halo on the wall above the sign, orange spill of the next shop on the wall and pavement; the unshadowed magenta pool on the road is gone (see 11.3) |
| ov_street | 36.9 / 52.2 | 43.9 / 40.7 | lamp pools along both kerbs with the pavement lit, tree and post shadows in them |
| ov_gas | 80.6 / 12.9 | 71.1 / 24.1 | canopy underside lit (the V-flip tell-tale), pump island bright, cars in it; the canopy's white pools on the road gone (specular, 11.3) |
| ov_plaza | 67.5 / 24.1 | 85.6 / 20.1 | plaza bright like the Cycles target (`phase3-lightmaps/out/verify/compare_ov_plaza.png`), monument shadow |
| ov_downtown | 75.5 / 36.7 | 83.2 / 25.6 | towers blue-lit from the sky with bounce off the plaza — matches the full-GI Cycles panel |
| ov_industrial | 69.7 / 42.0 | 71.3 / 33.7 | sodium wall packs light the warehouse walls with falloff |
| ov_residential | 71.2 / 21.8 | 72.1 / 20.6 | shop-sign spill on the walls, softer corners |
| ov_park | 61.5 / 46.8 | 64.0 / 38.5 | the apartment block reads as a volume (lit corners, floor bands) instead of a black slab |
| ov_birdseye | 42.9 / 55.2 | 42.9 / 54.8 | unchanged at this distance |
| 05_drive | 51.9 / 36.1 | 49.4 / 39.4 | headlight pools, tail-light glow and blob shadow still on the lightmapped road (dynamic lights work) |

Nothing is blown out and nothing is black; no district is scrambled (every wall's light sits where its lamp is — the rects and the
packed uv1 agree). The brightness lands in the same range as round 5 (the bake replaces, it does not add). Gate
`pruefe_openworld.mjs`: **GREEN**, mean 71.7 / 18.6 % near-black (limit 33 %), 0 console errors. `node test/quick.mjs --http`: load
1.1 s, 60 fps, 0 errors — the fetch path serves the KTX2 files too. Runtime check (`node test/lmcheck.mjs`):
`lgStatic` = 596 = `staticCount`, 17 district meshes over 15 kinds, uv1 + lmRect on all of them, 0 zero-width rects, 5 lightmapped
building materials + 4 ground materials, no skirts, ground map 4096² `COMPRESSED_SRGB8_ALPHA8_ASTC_4x4` with 13 mips, AO linear ASTC,
KTX2 transcode 125–410 ms per map in the workers, 0 page errors.
Cost: draws 329–412 in the look views (round 5: 300–495 — the 2 extra district meshes are within noise, the skirts' draw is gone);
frame 16.7 ms at 60 fps throughout; textures 74 (was 61–63); assets 31.1 MB in 0.8–1.1 s from `file://` (was 5.9 MB in 0.3 s) —
the KTX2 transcode of the 4096² maps is what costs, 100–400 ms each in the workers; ≈ 75 MB more VRAM with mips.

### 11.3 Left undone / consequences to know about
- **No specular from the static lights on the wet road any more.** The bake is diffuse irradiance; the static grid entries are skipped on
  lightmapped materials as the recipe demands. The lamp / neon / canopy *smears* on the wet asphalt of round 3 (GGX from the grid lights)
  are therefore gone — the road reads matter at night; only the env-specular of the sky remains. The fix is small (a second, specular-only
  pass over the static ids for the road material: `RE_Direct` with `material.diffuseColor = 0`, ~10 lines in `LOOP_FRAG_LM`) but it is an
  improvement beyond this round's brief, so it was not started.
- **Props, cars, people, weapons** are not lightmapped (hemisphere + env + unshadowed grid, as before) — a car parked next to a lit shop
  wall is lit slightly differently from the wall. Light probes for the dynamic objects are the phase-3 wish list.
- **The terrain outside ±255 m** (`Ground`) is real-time; at the city edge the field meets the lightmapped road with a visible but
  distant seam.
- **`preview/viewer.mjs` keeps the hemisphere** (11.1) — its verify shots are slightly over-lit; not fixed (outside the game).
- **Load size:** `assets/` is 31 MB (+ 43 MB of sidecars); `file://` start went from 0.3 s to ~1 s. ETC1S for the `_lm` files would
  quarter that at visible cost (§2 of the lightmap notes). Not changed.
- **A world change needs a re-bake** (`NOTES-lightmaps.md` §6: `dump_world.mjs` → System A → `encode_ktx.sh` → `node pack-assets.mjs`).
  `dump_world.mjs` still runs: with the stub registry `ASSETS.lightmaps` is null and `world.js` takes the old per-kind path.
- Round 5's `shots/ov_*.png` are kept as the "before"; the new set lives in `shots/lm/`.
