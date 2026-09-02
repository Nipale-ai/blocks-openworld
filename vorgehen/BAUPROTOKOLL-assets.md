# Phase 2 — real assets for BLOCKS (work log + handover)

Started 2026-09-02 10:05 CEST. Everything here is produced by scripts in this directory, run
headless on System A (`ssh systema`, RTX 5090, Blender 5.2.1 at `/usr/local/bin/blender`).
Nothing outside `phase2-assets/` was written.

## Deliverables at a glance

All GLBs are in `out/` (textures embedded), the render sheets I checked in `out/renders/*_sheet.png`, numeric reports
in `out/renders/*.json`, textures also loose in `out/tex/`, `.blend` scenes in `out/`. Scripts in this directory.
Final status table at the end of this file. Every asset passes `verify.py`'s contract check.

| file | what |
|---|---|
| `out/vehicle_sedan.glb`, `vehicle_muscle.glb`, `vehicle_van.glb`, `vehicle_police.glb` (+ `_lod1`) | player / traffic / police cars |
| `out/weapon_pistol.glb`, `weapon_mg.glb`, `weapon_rocket.glb` | weapons |
| `out/character_player.glb`, `character_officer.glb`, `character_civ0..5.glb` | skinned biped variants |
| `out/buildings_city.glb` (13 kinds), `out/buildings_industrial.glb` (4 kinds) | instanced building prototypes |
| `out/props.glb` (19 kinds) | street furniture prototypes |

## Findings from the game source that shape the assets (read-only, nothing modified)

- `vehicles.js:17-24` fetches `body`, `brakeLights`, `lights`, `wheel_FL/FR/RL/RR`, `beacon_L/R` by name.
  `vehicles.js:183` swaps `lights.material` between `MAT.lights` and `MAT.lightsOff` every frame — **both are
  vertex-colour materials**, so the `lights` mesh must ship a `COLOR_0` attribute (warm white lenses, red tails).
  `vehicles.js:160` swaps `body.material` for `MAT.wreck` — so `body` must be exactly one Mesh with one material
  (GLTFLoader splits multi-material meshes into a Group, which would break `body.material`). Paint therefore lives
  on `body` alone; black plastics, chrome, interior live on a separate `trim` mesh; glass on `glass`.
- `player.js:134` / `npcs.js:285` move `rig.mesh.position.y` to lift/lower the character. A three.js SkinnedMesh in
  `attached` bind mode ignores its own transform, so the object returned as `mesh` must be the **armature node**
  (parent of the bones), not the SkinnedMesh. See loader instructions below.
- `world.js:344` / `props.js:15` build one `InstancedMesh(proto.geometry, proto.material)` per building/prop kind:
  each building and prop GLB is **one mesh with one material**. `instanceColor` tints the material, so the wall
  areas of the base-colour texture are kept near white and the glass areas dark (same trick as the placeholder).
- `makeBuildingEmissive` places the lit-window quads from the placeholder's recorded glass bands (`floorH`,
  `glassH`, `inset` per kind). The new buildings keep the same floor pitch and band positions so the existing
  window layer still lines up (window frame pitch 2.3 m, panes ≥ 1.2 m so the 1.1 m quads sit inside the frames).
- `lighting.js:168` patches every `MeshStandardMaterial` it can reach at start (`patchAll`) and everything in
  `G.extraMaterials`. Materials loaded from GLBs after that must be handed to `patch()` — noted per asset below.

## Conventions

- Blender scene: Z up, car/character forward = −Y. glTF export with `+Y up` turns Blender (x, y, z) into
  glTF (x, z, −y), so a contract point (x, y, z) is placed at Blender (x, −z, y). `common.B()` does that.
- Units metres. Origins exactly as in the contract (vehicle: centre of the contact patches on the ground;
  character: between the feet; weapon: grip; building/prop: bottom centre).
- One GLB per asset, textures packed (PNG), no Draco. Exception on purpose: buildings and props are one GLB per
  family (`buildings_city`, `buildings_industrial`, `props`) so the kinds share one texture set in memory and one
  material — 17 separate building GLBs would have carried 17 copies of the 2048² sheet into VRAM.

## 1. Vehicles — `out/vehicle_{sedan,muscle,van,police}.glb` (+ `_lod1` variants)

Generator: `build_vehicles.py` (`blender -b -P build_vehicles.py -- sedan muscle van police lod1`). Verified with
`verify.py` (contract check PASS for all eight files, sheets in `out/renders/vehicle_*_sheet.png`).

**How they are built.** The shell is a loft of 14–19 cross-section stations (floor, rocker, door, shoulder/belt line,
tumblehome, roof — 22 points per ring) with edge creases on the belt and rocker lines, Catmull-Clark level 2 (level 1 for
LOD1), wheel arches cut by boolean cylinders, glass split off by material, the cabin interior is a shrunken flipped copy
of the shell (so you never see through the car), lights are grid patches snapped onto the shell surface. Trim (bumpers,
grille + chrome frame, plates, mirrors, handles, wheel-well liners, underbody, dash, console, seats, steering wheel,
exhaust; van: roof rails, rear step; muscle: scoop, spoiler, twin pipes; police: light bar, push bar, antenna) is one
mesh on a 16-swatch atlas. Wheels: lathe tyre with tread normal map, dished 5-spoke alloy, barrel and hub.

**Files and budgets** (budget stated: ≤ 25 k tris LOD0 for a player-driven car, ≤ 13.5 k LOD1 for traffic):

| file | tris total | body | trim | glass | wheels (4) | lights + brake | size (game, x·y·z) | GLB |
|---|---|---|---|---|---|---|---|---|
| vehicle_sedan.glb | 23 828 | 11 712 | 7 692 | 1 024 | 3 184 | 216 | 2.21 × 1.46 × 4.74 (body 1.83 × 1.26 × 4.62) | 1.6 MB |
| vehicle_muscle.glb | 20 928 | 9 944 | 6 792 | 768 | 3 184 | 240 | 2.31 × 1.32 × 5.04 | 1.5 MB |
| vehicle_van.glb | 20 888 | 8 944 | 8 096 | 512 | 3 184 | 152 | 2.46 × 2.47 × 5.76 | 1.5 MB |
| vehicle_police.glb | 24 432 | 11 708 | 8 084 | 1 024 | 3 184 | 216 (+216 beacons) | 2.24 × 1.69 × 4.93 | 1.8 MB |
| *_lod1.glb | 10.4–11.6 k | 2.5–3.2 k | 4.0–4.6 k | 128–256 | 3 184 | same | same | 1.2–1.4 MB |

The width beyond the contract W is the mirrors (±0.18 m), the length beyond L is the bumpers/push bar (≤ 0.12 m) — the
physics box stays L × W as in `defs.js`; the visual body shell itself is within 2 cm of L × W × (H − wheel clearance).

**Texture sets** (all embedded PNG): `paint_<kind>`: `body_<kind>_albedo` 1024² (2048×1024 police), `_orm`, `_normal`
(panel gaps, hood/boot shut lines, blacked-out B-pillar, dark underside; police livery + POLICE lettering baked in);
`trim`: `trim_albedo/orm/normal` 1024² swatch atlas (black plastic, chrome, interior, grille mesh, housing, rubber,
steel, seat quilting, dash, wheel well, plate, …); `wheel`: `wheel_albedo/orm/normal_{1,2}` 512² (tread band repeats
9× around the tyre, alloy band, hub); `glass` (no texture: base 0.04/0.07/0.09, roughness 0.04, alpha 0.42, BLEND);
`lights` / `brake`: emissive fallbacks — the game swaps these materials anyway.

**Contract values verified (verify.py, tolerance 1 cm):** every `wheel_*` at (±track/2, r, ±wb/2) with the pivot at the
hub centre and the tyre size 2r × 2r × ww; `seat`, `exit_L/R` (±(W/2 + 0.9), 0, 0.3), `exhaust` (−0.5, 0.3, −L/2 − 0.1),
`headlight_L/R` (±(W/2 − 0.35), 0.8, L/2); police `beacon_L` (0.3, 1.62, −0.15) / `beacon_R` (−0.3, 1.62, −0.15),
0.46 × 0.14 × 0.28; lowest point y = 0 for all; `lights` carries COLOR_0 (warm lenses front, red rear), `brakeLights`
COLOR_0 red. The root node carries `extras.dims = {length, width, height}`.

**Loading in `assets.js` (`makeVehicleMesh(type, paintHex)`):**
```js
// once, at start: const GLB = {}; for (const t of ['sedan','muscle','van','police']) GLB[t] = (await loader.loadAsync(`assets/vehicle_${t}.glb`)).scene;
const src = GLB[type]; const g = src.clone();               // Object3D.clone shares geometry + materials
g.name = 'Vehicle_' + type;
const body = g.getObjectByName('body');
body.material = paintMaterial(type, paintHex);               // cache one clone of body.material per paint colour and set .color = paintHex
                                                             // (police: keep the default colour, the livery is in the texture)
g.getObjectByName('lights');  g.getObjectByName('brakeLights').visible = false;   // both keep the game's material swaps
for (const n of ['body','trim','glass']) { const o = g.getObjectByName(n); o.castShadow = n !== 'glass'; o.receiveShadow = true; }
for (const w of ['wheel_FL','wheel_FR','wheel_RL','wheel_RR']) g.getObjectByName(w).castShadow = true;
g.userData.dims = { length: d.length, width: d.width, height: d.height };        // or read g.children[0].userData.dims
return g;   // seat / exit_L / exit_R / exhaust / headlight_L / headlight_R / beacon_L / beacon_R are already there by name
```
Material notes: the loaded materials are `MeshStandardMaterial`s — register them once in `G.extraMaterials` (or call
`lighting.patch(mat)`) so the light grid patches them; `glass` comes in with `transparent = true`, `depthWrite = false`,
`opacity 0.42` — leave it after the opaque children (three.js sorts it). The wreck swap (`body.material = MAT.wreck`)
and the lights swap keep working because `body`/`lights`/`brakeLights` are single-material meshes. The GLB node name
of the mesh objects is exactly the child name; `getObjectByName` finds them one level under the root node. Use
`vehicle_<type>_lod1.glb` for traffic if the frame time needs it (identical names/pivots, half the triangles).

**What I would improve with more time:** door shut lines as geometry grooves baked to the normal map from a high-poly
(now painted in UV space), separate emissive masks for indicators, wider rear tyres on the muscle car (the contract
gives one width), an interior with a proper dashboard texture, clearcoat on the paint once the lighting patch is
confirmed to compile with `MeshPhysicalMaterial`.

## 2. Weapons — `out/weapon_{pistol,mg,rocket}.glb`

Generator: `build_weapons.py`. Origin = grip point, barrel +Z, up +Y; `muzzle` empties at (0, 0.022, 0.16) / (0, 0.05,
0.65) / (0, 0.09, 0.80) verified; `loadedRocket` is a separate named mesh (272 tris) under the launcher root.

| file | tris | extents (x·y·z, m) | notes |
|---|---|---|---|
| weapon_pistol.glb | ~1.3 k | 0.04 × 0.17 × 0.22 | polymer frame, steel slide with front/rear serrations, cover plate, extractor, ejection port, sights, rail, raked stippled grip with finger ridges, trigger guard loop, mag base |
| weapon_mg.glb | ~3.2 k | 0.07 × 0.30 × 0.97 | receiver + lower, top rail, slotted handguard with side rails, barrel + slotted brake, hooded front sight, rear sight, reflex optic, curved 2-piece magazine, ejection port cover, forward assist, bolt handle, buffer tube with rings, collapsible stock, pad, sling mounts |
| weapon_rocket.glb | ~3.1 k | 0.18 × 0.31 × 1.35 | tube r 0.062 with rivet rings, orange bands, muzzle rim, rear bell, heat shield, shoulder rest, carry handle, front + rear grips, trigger housing, flip-up optic with hood, front iron sight, sling loops; `loadedRocket` (body, ring, red ogive) |

Texture set `gun_albedo/orm/normal` 1024² swatch atlas (polymer, stipple, gun steel, gunmetal, serrations, rail
notches, vent slots, olive, ribs, orange, rubber, lens, brass, warhead, wear) — one material per weapon, single mesh
`body`. Budgets stated: pistol ≤ 4 k, MG ≤ 7 k, launcher ≤ 6 k (all met).

**Loading (`makeWeaponMesh(type)`):** `const g = GLB.weapon[type].clone(); g.name = 'Weapon_' + type; return g;` — the
group has `body` (castShadow true), `muzzle` and, for the launcher, `loadedRocket`. Nothing else to do; the socket
transform (rotation.x = +90° under `Hand_R`) is unchanged.

## 3. Character rig — `out/character_{player,officer,civ0..civ5}.glb`

Generator: `build_character.py`. One skinned mesh (`CharacterMesh`, 2 308 tris + cap/belt geometry for the officer)
under an armature node `CharacterRig` with the 16 contract bones. **Verified straight from the GLB JSON** (`verify.py`
parses the binary): every joint has rotation (0,0,0,1) = identity and its world position equals the contract table to
the millimetre (Hips 0/0.95/0 … Foot_R −0.11/0.08/0); `WeaponSocket` is a child of `Hand_R` at world (−0.24, 0.84,
0.03) with rotation.x = +90°; lowest point y = 0 (soles), top 1.815 m (hair), 1.85 m with the officer's cap.
Bones are Blender bones pointing +Z with roll 0 — the exporter's Y-up conversion turns that into identity glTF joints,
which is what the animator expects (`bone.rotation` set absolutely by name every frame).

Mesh: lofted tubes (torso 11 rings, head 9 rings + pole, arms 3-joint tubes, legs 3-joint tubes, hands with thumbs,
shoes as z-lofts, ears, nose, hair cap; officer: peaked cap with peak, duty belt with buckle, holster on the right hip,
two pouches, chest radio). Skin weights are assigned per ring: 1.0 inside a segment, 0.85/0.15 approaching a joint,
0.5/0.5 on the joint ring — the crouch pose (thighs −1.35, shins +1.5) and the walk cycle bend cleanly.

Texture set per variant: `char_<name>_albedo/orm/normal` 1024² atlas painted from the palette (face with eyes, brows,
mouth; hairline; shirt with neckline/placket/hem, short or long sleeves; trousers with seams; shoes; officer: navy shirt
with tie, badge, pocket flaps, epaulettes, shoulder patches, trouser stripe, black cap with badge). Cloth folds in the
normal map. Roughness skin 0.55, cloth 0.85, leather 0.45, metal 0.3. Variants and palettes are the placeholder's
(`makePlayerMesh`, `NPC_SHIRTS`/`NPC_PANTS`, officer navy) — add more by adding a palette to `PALETTES` and re-running.

**Loading (`makeCharacterRig(palette, scale)` replacement):** load each variant once, then per spawn:
```js
import { clone as skeletonClone } from 'three/examples/jsm/utils/SkeletonUtils.js';
const src = GLB.character[variant];                 // gltf.scene of character_<variant>.glb
const inst = skeletonClone(src);                    // clones bones + SkinnedMesh with a fresh Skeleton
const mesh = inst.getObjectByName('CharacterRig');  // the ARMATURE node: bones AND the SkinnedMesh are its children,
                                                    // so mesh.position.y (crouch / jump offset in player.js:134) moves the whole character
const skinned = inst.getObjectByName('CharacterMesh'); skinned.castShadow = true; skinned.frustumCulled = false; // or enlarge its bounding sphere ×1.6 as before
const bones = {}; skinned.skeleton.bones.forEach(b => { bones[b.name] = b; });
const socket = inst.getObjectByName('WeaponSocket');  // already a child of Hand_R with position (0,-0.08,0.03), rotation.x = +90°
const root = new THREE.Group(); root.name = 'CharacterRoot'; root.add(inst); root.scale.setScalar(scale);
return { root, mesh, bones, socket, height: 1.8 * scale };
```
The animator's `bone.rotation` writes work unchanged (rest = identity). The skinned material is a MeshStandardMaterial
with the atlas — hand it to `lighting.patch()` once per variant. Civilians: pick `civ0..civ5` by `rng`; officers use
`officer`, scaled 0.98–1.06 as now. Officers' cap and belt are part of the mesh (no extra objects).

**What I would improve with more time (characters):** proper finger geometry instead of a mitten + thumb, a second
LOD, blend-shape face variation, elbows/knees with an extra loop for the crouch, hair variants as separate caps,
and a vertex-colour tint mask so one texture could serve every palette instead of one atlas per variant.

## 4. Buildings — `out/buildings_city.glb` (13 kinds) and `out/buildings_industrial.glb` (4 kinds)

Generator: `build_buildings.py`. Every kind is one mesh `Building_<kind>` under the family root, one material per
family (`buildings_city`: 2048² trim sheet; `buildings_industrial`: 1024² trim sheet) — so all kinds of a family share
ONE texture set in memory, and `InstancedMesh(proto.geometry, proto.material)` works as before with `instanceColor`
tinting the light wall rows (glass, frames, ledges are dark and barely tinted, like the placeholder's vertex colours).

Footprints and heights are exactly the table (verified numerically in the generator log: e.g. tower_a x ±13, z ±13,
y 0…84 + mast to 94; tower_b 22 × 34 × 66 + rooftop box to 72; …); extras beyond the box are the same as the
placeholder's (awnings, balconies, roof boxes, parapets, canopy). Origin bottom centre, facade/entrance toward +Z.
The floors keep the placeholder's `floorH / glassH / inset` per kind, so `makeBuildingEmissive`'s lit-window quads
(2.3 m pitch, 1.1 m wide, 3 cm in front of the recessed band) land inside the window frames of the texture: the window
band of every facade is split into [plain margin | exactly `floor((w − 2.4) / 2.3)` window bays | plain margin], the
same count and centring the emissive layer uses.

Triangles (instanced hundreds of times, budget ≤ 1 200 per kind): tower_a 1 156 · tower_b 962 · tower_c 720 ·
office_a 584 · office_b 418 · apartment_a 582 · apartment_b 340 · shop_row 174 · shop_small 78 · parking 686 ·
gas_station 158 · monument 70 · fountain 266 · warehouse 102 · industrial 402 · house 94 · bridge_ramp 26.
UV2 (`TEXCOORD_1`) is a smart projection with 2 % margins on every kind, free for lightmaps.

Trim sheet rows (city): concrete / plaster / brick wall bands (ComfyUI Z-Image-Turbo photographic sources made
tileable, `comfy_textures.py`), window bands on concrete / plaster / brick (frame, mullion, transom, sill, dirt streak;
glass roughness 0.08), curtain wall (mullions every 1.15 m, spandrel), shopfront (kick plate, frames, doors with push
bars, transom), stone plinth, ledge, roof gravel, dark metal, and a swatch strip (awning stripes orange/red/blue, white,
water, sign black, wood, dark glass). Industrial sheet: corrugated siding (metalness 0.6), roller door ribs, brick +
brick windows, roof tiles, plaster + plaster windows, asphalt (bridge ramp), stone/ledge/gravel/metal, swatches
(yellow paint, wood, dark, glass, dirt, light frames, dark roof, water).

**Loading (`makeBuilding(kind, rng)` replacement):**
```js
const fam = ['warehouse','industrial','house','bridge_ramp'].includes(kind) ? GLB.buildingsIndustrial : GLB.buildingsCity;
const proto = fam.getObjectByName('Building_' + kind);      // Mesh with .geometry (UVMap + UV2) and the family material
proto.castShadow = true; proto.receiveShadow = true; proto.userData.kind = BUILDING_KINDS[kind];
return proto;                                                 // world.js:344 does new InstancedMesh(proto.geometry, proto.material, n)
```
Keep `BUILDING_KINDS[kind].bands` as recorded by the placeholder builders (or record the same numbers) so the emissive
layer keeps working; the family material must be given to `lighting.patch()` (it is a MeshStandardMaterial). Because
all kinds of a family share the material, `instanceColor` per InstancedMesh still works (the tint is per instance,
not per material). The gas station's colliders (columns ±9 / −2,+6, canopy slab, shop box at z −12) match the geometry.

**What I would improve with more time (buildings):** bake ambient occlusion into UV2 from the ledge geometry, real
mullion geometry on the curtain-wall podiums, a few facade variants per kind (the instancing hash could pick them),
a rooftop kit (HVAC, water tanks, antennas) shared across kinds, an emissive mask for the shopfronts, and a separate
ground-floor row with entrances per bay so the lobby door is not repeated every second bay.

## 5. Props — `out/props.glb` (19 kinds, one material)

Generator: `build_props.py`. One mesh `Prop_<kind>` per kind under the root `Props`, one swatch-atlas material
`props` (`props_albedo/orm/normal` 1024²: painted steel, wood grain, concrete, leaves, bark, rubber, signal lenses,
plates…). Origin = base centre on the ground; the contract's radius / height numbers are kept (cone 0.72, barrel 0.90,
crate 0.90, bench 0.885, hydrant 0.89, trash 0.98, mailbox 1.3, planter 0.9, bollard 1.0, newsbox 1.1, dumpster 1.4,
lamp 8.07 with the arm 2.2 m toward +Z and the head at 7.95, trafficlight 5.4 with the arm 4.5 m toward +Z and the
housing at z 4.2, tree_round canopy r 2.3 @ y 4.2, tree_tall crown to 9.5, bush 1.3, busstop 3.2 wide / 2.7 tall with
the glass back at z −0.6, wall 4 × 1.2, tank r 2.2 / 5.2) so `makePropPrefab`'s collision numbers stay valid.
Triangles: barrel 308 · bench 396 · bollard 188 · bush 60 · busstop 208 · cone 250 · crate 264 · dumpster 236 ·
hydrant 400 · lamp 296 · mailbox 156 · newsbox 80 · planter 116 · tank 448 · trafficlight 316 · trash 356 ·
tree_round 260 · tree_tall 160 · wall 88 (4 586 total, budget ≤ 500 per kind). UV2 on every prop.

**Loading (`makePropPrefab(kind)` replacement):** `const mesh = GLB.props.getObjectByName('Prop_' + kind);` and return
`{ kind, mesh, geometry: mesh.geometry, material: mesh.material, radius, height, mass, dynamic, sound }` with the
numbers from the existing table; the material (shared by all kinds) goes to `lighting.patch()` once. The lamp head
emissive quad and the traffic-light lenses of `lighting.js` (`propOverlay`) sit at the same positions as before.

**What I would improve with more time (props):** leaf-card canopies with alpha (the crown is solid icospheres with a
leaf normal map now), a dented/rusty variant of barrel and dumpster, decals on newsbox and bus stop.

## 6. Verification, scripts, render sheets

- `verify.py` re-imports every GLB into an empty Blender scene, prints each node's game-frame position, triangle
  count, bounding box, materials/images, parses the GLB JSON for joint rotations, compares with `contract.json`
  (positions ±1 cm, sizes, lowest point, budgets) and renders a 4-view sheet on a 1 m checker ground. All sheets are in
  `out/renders/*_sheet.png`, the numeric reports in `out/renders/*.json`. Every asset passes its contract check.
- `run.sh <script> [args]` syncs the scripts to System A, runs Blender headless there and syncs `out/` back.
- Scripts: `common.py` (helpers, export), `build_vehicles.py`, `build_weapons.py`, `build_character.py`,
  `build_buildings.py`, `build_props.py`, `comfy_textures.py` (ComfyUI Z-Image-Turbo base textures), `verify.py`,
  `contract.json`. `.blend` files of every asset are in `out/` for manual inspection.

## Status

| # | asset | files | state |
|---|---|---|---|
| 1 | vehicles | vehicle_{sedan,muscle,van,police}.glb + _lod1 | done, contract PASS, sheets checked |
| 2 | weapons | weapon_{pistol,mg,rocket}.glb | done, contract PASS, sheets checked |
| 3 | characters | character_{player,officer,civ0..civ5}.glb | done, contract PASS (joints from GLB JSON), sheets checked |
| 4 | buildings | buildings_city.glb (13), buildings_industrial.glb (4) | done, footprints/heights verified, 17 sheets |
| 5 | props | props.glb (19) | done, sheets checked |
