# Phase 3 — baked lightmaps for BLOCKS (handover)

Built 2026-09-02 on System A (RTX 5090, Blender 5.2.1 LTS, Cycles/OptiX) from the city the game builds itself. Nothing outside
`phase3-lightmaps/` was written. Status table and the numbers are at the end; **section 3 is the wiring recipe.**

## 0. Files in `out/`

| file | covers | resolution | mips | codec | size |
|---|---|---|---|---|---|
| `out/downtown_ao.ktx2` | same buildings, ambient occlusion (6 m) | 4096 × 1280 | 13 | ETC1S (BasisLZ) | 0.4 MB |
| `out/downtown_lm.ktx2` | downtown + plaza blocks: 3 × tower_c, monument, fountain — baked irradiance (sky + static lights, direct + indirect) · lm_scale 4.0 | 4096 × 1280 | 13 | UASTC + zstd | 2.9 MB |
| `out/ground_ao.ktx2` | same floor, AO (building plinths, kerbs, under trees) | 4096 × 4096 | 13 | ETC1S (BasisLZ) | 1.2 MB |
| `out/ground_lm.ktx2` | the whole city floor ±255 m in world XZ: roads, sidewalks, lots, plaza, park lawns, medians — irradiance incl. lamp pools and post/tree shadows · lm_scale 8.0 | 4096 × 4096 | 13 | UASTC + zstd | 7.1 MB |
| `out/industrial_ao.ktx2` | same buildings, AO | 2048 × 1536 | 12 | ETC1S (BasisLZ) | 0.4 MB |
| `out/industrial_lm.ktx2` | industrial + stunt + park blocks: 36 buildings (warehouses, factories, shop_smalls, ramps, fountain) — irradiance · lm_scale 8.0 | 2048 × 1536 | 12 | UASTC + zstd | 1.7 MB |
| `out/midtown_ao.ktx2` | same buildings, AO | 4096 × 3584 | 13 | ETC1S (BasisLZ) | 1.7 MB |
| `out/midtown_lm.ktx2` | midtown + residential + parking + gas blocks: 100 buildings (offices, apartments, shop rows, houses, parking deck, gas station) — irradiance · lm_scale 4.0 | 4096 × 3584 | 13 | UASTC + zstd | 10.0 MB |
| `out/assets-uv2/buildings_city.glb` | phase-2 GLB with repacked TEXCOORD_1 — pack from this | | | | 2.6 MB |
| `out/assets-uv2/buildings_industrial.glb` | phase-2 GLB with repacked TEXCOORD_1 — pack from this | | | | 1.1 MB |
| `out/lm-layout.json` | per-instance atlas rects (glTF UV space), districts, lm_scale, ground mapping | | | | 0.1 MB |

## 1. What was baked, and why this way

- **Layout = the game's own layout.** `dump_world.mjs` runs `../src/world.js` in Node (asset registry stubbed with boxes) and writes
  `work/world-dump.json`: 141 buildings (kind, x, z, rot, tint, block/template), 716 static props, the 36 blocks, medians, and the
  596 static lights of `lighting.js` (same rng, same order — the count matches the game's light table). `build_city.py` rebuilds
  that in Blender from the phase-2 `.blend` assets (same meshes, same UVMap + UV2, same textures). Blender (x, y, z) = game (x, −z, y).
- **Lighting = the game's rig, in radiometric units.** Calibrated first (`calib_units.py`): Cycles' bake value for a white Lambert
  surface is E/π, a point light of P W has I = P/4π. So every static light is a Blender light with P = 4π·I_game, the game's
  falloff `pow2(sat(1−(d/R)^4))/(d²+0.35)` is reproduced exactly with a Light-Path *Ray Length* node tree, street lamps are spots with
  `spot_size = 2·1.22`, `blend = (cos 0.62 − cos 1.22)/(1 − cos 1.22)` (matches the game's smoothstep within 2 % out to 8 m; the dim tail
  beyond 12 m is a little brighter in Cycles). The world is the `makeSky()` gradient rendered to an equirect (× environmentIntensity
  0.9) **plus** the hemisphere light expressed as radiance (1.05/π · mix(ground, sky, ½+½·n.y)). Windows, signs, neon, canopy panels
  and lamp heads are emissive quads at the game's HDR colours (signs/lamp heads camera-only — their spill is already in the light
  table; lit windows spill 35 % of their radiance, the same hash → same windows lit as in the game's shader). The key light
  (`#8fa8dc` × 0.62, keyDir) is **not** baked — it keeps its real-time shadows for cars and people — except for its bounce (below).
- **Lightmap content** (per texel, three.js irradiance units = what `RE_Direct` adds as `irradiance`, so ×BRDF_Lambert(albedo) in the
  shader): `LM = π · (DiffuseDirect[key hidden] + DiffuseIndirect[key on])` = sky direct + sky bounce + static lamps/signs direct
  **with shadows** + their bounce + the key light's bounce. **AO** = Cycles ambient occlusion, 6 m radius, separate map.
- **Where it lands:** buildings → the second UV channel (TEXCOORD_1) of the prototypes, one **rect per instance** in a per-district
  atlas (an instance can only get one affine rect, so the prototype's UV2 islands were repacked tightly — same cuts, same channel —
  and the two building GLBs re-exported with that TEXCOORD_1 into `out/assets-uv2/`; the original smart projection filled only
  8–13 % of the square on the towers). Ground (road, sidewalks, lots, medians) → **one world-XZ map**, no UV needed:
  `uv = ((x + 255)/510, (255 − z)/510)`. Static props are occluders/bouncers in the bake but are not lightmapped (they keep the
  real-time path; a lamp post or a tree trunk gains nothing visible from a lightmap). Dynamic props, cars and people are not in the bake.

## 2. Sections, samples, times

Every section: take the System A lock (`systema-belegen "model-research" … 20–25`), run `bake_district.py` for one district
(buildings atlas + that district's ground cells), release (`systema-frei`). The bakes themselves are short on the 5090 — most of a
section is denoising, encoding and the verification renders; the lock was never held longer than a few minutes at a time.

| section | receivers | atlas | direct | indirect | AO | ground cells (direct / indirect / AO) |
|---|---|---|---|---|---|---|
| 1 downtown (downtown + plaza) | 5 buildings (3 tower_c, monument, fountain) | 4096 × 1280 | 2.7 s | 5.3 s | 1.4 s | 9.5 % of the map: 13.4 / 6.4 / 2.7 s |
| 2 midtown (midtown + residential + parking + gas) | 100 buildings | 4096 × 3584 | 11.1 s | 21.0 s | 3.6 s | 53.8 %: 51.5 / 28.1 / 5.4 s |
| 3 industrial (industrial + stunt + park) | 36 buildings | 2048 × 1536 | 4.9 s | 7.0 s | 1.3 s | 100.0 % total: 36.2 / 13.6 / 3.8 s |

- **Samples:** 1024 spp with adaptive sampling (threshold 0.015, min 64) for the two diffuse passes, 256 spp for AO, 6 bounces
  (4 diffuse, 2 glossy), light tree on, `sample_clamp_indirect` 10, caustics off, `filter_glossy` 1. Cycles' bake spends samples
  only on covered texels, so a 4096² map costs what its coverage costs. Sample study on the downtown atlas (4096x1280, direct + indirect, raw before denoising, RMS difference to the 2048-spp bake over covered texels, mean irradiance 0.479): 256 spp fixed: 5.5 s, RMS 0.0952 (19.9 %); 1024 spp adaptive: 7.9 s, RMS 0.0821 (17.2 %); 2048 spp adaptive: 11.8 s, RMS 0.0000 (0.0 %). After OIDN: 256 vs 2048 RMS 0.0603 (12.6 %), 1024 vs 2048 RMS 0.0530 (11.1 %). Settled on 1024 adaptive + OIDN for every map.
- **Denoise:** OpenImageDenoise through Blender's compositor (HDR, accurate prefilter) on the *summed* map, after the gutters were
  filled by dilation (so the denoiser never sees black island borders and the mip chain never bleeds black into an island).
  0.4–0.9 s per map.
- **Texel density:** buildings 5.0 texels/m (20 cm) in downtown and industrial, 4.05 texels/m (25 cm) in midtown — the 100
  midtown buildings did not fit a 4096-wide atlas at 5.0 even after repacking; the ground runs at 8 texels/m (12.5 cm) because
  that is where the sharp features are (lamp pools, post and tree shadows, kerb lines). A wall is therefore at most 2× coarser than
  the pavement next to it; nothing is blurrier than the vertex-colour ramps and gradient skirts it replaces.
- **Encoding:** irradiance / `lm_scale` through the sRGB OETF into 8 bit with ½-LSB dither, then KTX2. `lm_scale` = 4 for
  downtown and midtown (99.9th percentile 2.6 / 16 — only the shopfront spill right next to a sign light clips), 8 for industrial
  (the sodium wall packs sit 1.5 m off the warehouse walls and push the wall behind them to 40–115; at 4 that hot spot went flat)
  and 8 for the ground (lamp pool centres reach 10; with 4 the pools clipped). Everything outside the islands is filled by
  dilation for a 24-texel band and flat beyond it (mips stay clean, the flat area costs nothing).
  Codec, measured on the midtown atlas (4096 × 3584) against the 8-bit source: UASTC quality 2 + RDO λ 0.8 + zstd 18 → 43.8 dB
  PSNR; RDO λ 3 → 39.7 dB for ~10 % less disk; ETC1S quality 255 → 35.8 dB, max error 141/255, a quarter of the size but with
  visible block banding in the smooth pools and facades. Lightmaps therefore ship as UASTC (transcodes to ASTC 4×4 / BC7, 8 bpp
  in VRAM, sRGB decode in hardware); AO maps as ETC1S quality 200 (a single channel, 4 bpp in VRAM). If disk size matters more
  than the gradients, `encode_ktx.sh` takes one line to switch the `_lm` files to ETC1S.

## 3. HOW THE GAME LOADS AND APPLIES THEM — the recipe

(see the reference implementation `preview/viewer.mjs`, which renders the game's viewpoints with exactly this path)

### 3.1 Files and what they mean
- `out/<district>_lm.ktx2` — building lightmap atlas of that district (sRGB-encoded, UASTC). Decoded texel × `lm_scale[district]`
  (in `out/lm-layout.json`, 4.0) = diffuse irradiance in three.js units.
- `out/<district>_ao.ktx2` — building AO of that district (linear R8, ETC1S), same UVs.
- `out/ground_lm.ktx2` / `out/ground_ao.ktx2` — the whole city floor in world XZ (4096², 8 texels/m), `lm_scale.ground = 8.0`.
- `out/lm-layout.json` — per building instance (`index` = position in `world.buildings`, plus `kind, x, z, rot` to match robustly):
  `rect = [u0, v0, su, sv]` inside the district atlas, and `district` grouping (`districtOfTemplate`: downtown+plaza → downtown;
  midtown+residential+parking+gas → midtown; industrial+stunt+park → industrial).
- `out/assets-uv2/buildings_city.glb`, `buildings_industrial.glb` — the phase-2 building GLBs with the **repacked TEXCOORD_1**.
  Everything else in them is byte-for-byte the same content (same meshes, materials, textures, names). **Pack from these.**

### 3.2 Packing — keep TEXCOORD_1
In `pack-assets.mjs` the buildings families must keep `TEXCOORD_1` (today it is dropped for every family together with
`TANGENT`): for `buildings_city` and `buildings_industrial` only drop `TANGENT`, and read the source files from
`phase3-lightmaps/out/assets-uv2/` instead of `phase2-assets/out/`. Meshopt/quantisation are fine (`quantizeTexcoord: 14` is
1/16384 UV — 0.25 texel at 4096). Props keep being packed as they are (no lightmap on props). Ship the six `.ktx2` files next to
the other assets (plus `.b64.js` sidecars if the file:// path is kept; `KTX2Loader` loads them with the same transcoder).

### 3.3 Buildings: `InstancedMesh` per (kind, district) + one instance attribute
`world.js:instanceBuildings()` today builds one `InstancedMesh` per kind. Group by `(kind, district)` instead (17 kinds × ≤ 3
districts ≈ 25 meshes instead of 17 — a handful more draw calls), clone the family material per district
(`proto.material.clone()`, one clone per family × district = up to 6 materials) and give every instance its rect:

```js
// per (kind, district) InstancedMesh im, list = its building records
const rects = new Float32Array(list.length * 4);
list.forEach((b, i) => { const r = LM.rectOf(b); rects.set(r ? r.rect : [0, 0, 1, 1], i * 4); }); // r from lm-layout.json by (kind, x, z, rot) or index
im.geometry = proto.geometry.clone();                       // the geometry is shared between districts: clone before adding the attribute
im.geometry.setAttribute('lmRect', new THREE.InstancedBufferAttribute(rects, 4));
```
The geometry already carries `uv1` (= TEXCOORD_1) once it is packed. **The vertex-colour AO ramp (`baseAO` in assets.js) and the AO
skirts (`lighting.js:buildContact`) should be switched off for buildings** — both are now in the bake (double darkening otherwise).
Keep the emissive window / sign layer exactly as it is (additive, on top).

### 3.4 Ground
`Road`, `Slabs` (sidewalks, lots, medians), `LaneMarks`, `Crosswalks` use the ground maps with a world-space lookup — no UVs,
no instancing changes: `uv = ((x + 255) / 510, (255 − z) / 510)` from the world position (the patch already has `vLGPos`).
The `Ground` terrain outside ±255 m stays unlit-by-lightmap (it is outside the map); guard with the `lgParams` bounds or an
`if` on the uv range.

### 3.5 The material patch (no double lighting)
Extend the existing `Lighting.patch()` in `lighting.js` — it already rewrites the shader of every `MeshStandardMaterial`.
For a *lightmapped* material (buildings, ground) three changes, in this order (verbatim from `preview/viewer.mjs`, which
renders the game's viewpoints with exactly this):

```js
shader.uniforms.uLM = { value: lmTexture }; shader.uniforms.uAO = { value: aoTexture }; shader.uniforms.uLMScale = { value: lmScale };
// vertex: the lightmap uv (instance rect, or world XZ for the ground)
shader.vertexShader = shader.vertexShader
  .replace('#include <common>', '#include <common>\nvarying vec2 vLmUv;\n#if LM_MODE_INSTANCE\nattribute vec4 lmRect; attribute vec2 uv1;\n#endif')
  .replace('#include <worldpos_vertex>', `#include <worldpos_vertex>
  #if LM_MODE_INSTANCE
    vLmUv = uv1 * lmRect.zw + lmRect.xy;
  #else
    { vec4 wp = vec4(transformed, 1.0);
    #ifdef USE_INSTANCING
      wp = instanceMatrix * wp;
    #endif
      wp = modelMatrix * wp; vLmUv = vec2((wp.x + 255.0) / 510.0, (255.0 - wp.z) / 510.0); }
  #endif`);
// fragment: (1) baked irradiance instead of hemisphere + env diffuse, (2) env specular × baked AO
shader.fragmentShader = shader.fragmentShader
  .replace('#include <common>', '#include <common>\nuniform sampler2D uLM; uniform sampler2D uAO; uniform float uLMScale; varying vec2 vLmUv;')
  .replace('#include <lights_fragment_maps>', `
    vec3 lmIrradiance = texture2D(uLM, vLmUv).rgb * uLMScale; float lmAO = texture2D(uAO, vLmUv).r;
    irradiance += lmIrradiance;                                                    // sky + static lamps/signs (direct with shadows + all bounce)
    #if defined( USE_ENVMAP ) && defined( STANDARD )
      radiance += getIBLRadiance( geometryViewDir, geometryNormal, material.roughness ) * lmAO;   // env SPECULAR stays (wet road), occluded by AO
    #endif`)                                                                        // env DIFFUSE (getIBLIrradiance) is gone: it is inside the bake
  .replace(/irradiance \+= getHemisphereLightIrradiance\( hemisphereLights\[ i \], geometryNormal \);/, 'irradiance += vec3(0.0);'); // hemisphere: inside the bake too
```
> **Correction from the wiring (round 6, 2026-09-02):** the hemisphere replace above is a **no-op** — in `onBeforeCompile` the shader is
> still the unexpanded template and that line lives inside the chunk `<lights_fragment_begin>`. The game inlines
> `THREE.ShaderChunk.lights_fragment_begin` with the line neutralised instead (`src/lighting.js`, `LOOP_FRAG_LM`). `preview/viewer.mjs`
> has the same no-op, so the `out/verify/*_lm.png` viewer shots are lit by the bake **plus** the hemisphere (slightly too bright).
Then, in the light-grid loop of the same patch, **skip the static entries for lightmapped materials** — they are the lamps,
signs, canopy and porch lights that the bake already contains, now with shadows:
```glsl
if ( lgIdF < lgParams.w ) continue;       // lgParams.w = lighting.staticCount for lightmapped materials, 0.0 for everything else
```
(`lgParams` is a `Vector4` whose `.w` is unused today; set it per material through a second uniform or a define — the dynamic
lights (headlights, tail lights, beacons, flashes, muzzle) are the ids ≥ `staticCount` and keep working on the lightmapped surfaces.)
`lmScale` = `lm_scale[district]` (4.0) for building atlases, `lm_scale.ground` (8.0) for the ground. Textures: `KTX2Loader`
gives the `_lm` files `colorSpace = SRGBColorSpace` from the file's DFD (keep it — that decode is part of the encoding),
`_ao` linear; set `anisotropy = 4`, leave `flipY = false` (default for compressed textures — the world-XZ formula above is for that).

What stays real-time and untouched: the key `DirectionalLight` with its shadow map (cars, people, props still throw shadows
onto the lightmapped ground), the hemisphere/env/grid lighting on **everything that is not lightmapped** (cars, characters,
props, weapons, dynamic props), blob shadows under cars and people, all dynamic grid lights, the emissive layer, glow sprites,
headlight pools, fog and the post chain. Nothing in the bake depends on the camera.

### 3.6 Sanity checks after wiring
- `node test/look.mjs`: `ov_street` and `ov_shops` must show the lamp pools with the post shadows and the neon glow on the wall
  (compare with `phase3-lightmaps/out/verify/compare_*.png`); the gate view brightness should land in the same range as round 4
  (the bake replaces, it does not add, ambient light).
- A tower must not be lit through a neighbour's wall: the direct lamp term for buildings comes from the bake only.
- If a district looks *scrambled* (bright squares in the wrong places), the packed GLB still carries the old TEXCOORD_1 or
  `lmRect` was not set → 3.2 / 3.3.

## 4. Verification (what was looked at)

`out/verify/compare_<view>.png` — for every viewpoint of `test/look.mjs`: the round-4 game screenshot | the Cycles render of the
rebuilt city with the full dusk rig (the target: same rig, real GI) | Cycles lit **only** by the baked lightmap + the real-time
key light (what the bake actually contains) | the three.js viewer with the shipped KTX2 files applied exactly as in section 3.
The Cycles renders carry no fog and no bloom (Blender 5.2's scene output cannot write the mist pass alongside the image and the
File Output node produced nothing headless — not worth more time; fog only matters in the two distant views), so the far end of
`ov_birdseye` / `ov_downtown` is crisper and the field greener than in the game. The viewer applies three's ACES with the game's
exposure but not the postfx grade, and it draws no emissive window/sign layer, no glow sprites and no cars — it is there to prove
the *lightmap path*, not to replace the game's screenshot.
- Same place from every angle (the layout is the game's own dump; the cameras are the game's free-cam arrays).
- The lightmap-only render is near-identical to the full-GI render: neon glow on the shop walls, the orange shop spill on the
  awnings and pavement, the canopy light on the pumps and the shop box, lamp pools with post shadows, tree shadows on the median,
  the dark seam where the plinth meets the pavement. That is the proof the bake carries the lighting, not the renderer.
- No black district: every atlas has its coverage checked (5 % of covered texels are zero in every district — the bottom faces
  of the buildings, which nobody sees). The ground map covers the full ±255 m square.
- No light through walls in the baked term: the lamps are shadow-casting in Cycles. (The real-time grid never had shadows —
  that is precisely what the recipe in 3.5 removes for lightmapped surfaces.)
- Seams: island margins 4 px, instance gutters 12 px, gutters filled by dilation before denoising and mipmapping; the ground cells
  tile exactly (margin 0) and were checked for holes (none after the fill pass). Nothing blotchy after OIDN.
- The three.js viewer found two bugs that the Cycles-side checks could not: the exposure was applied twice (three's ACES already
  divides by 0.6), and the per-instance rects have to be expressed in glTF UV space (the exporter flips V) — both fixed, both
  documented in the recipe; the canopy underside of the gas station is the tell-tale (dark if the V flip is wrong).

## 5. What I would improve with more time
- **Props as receivers** (tree crowns and trunks, lamp posts, bus stops, tanks): they are occluders and bouncers in the bake but
  keep the real-time path. A per-cell prop atlas (props.js already groups static props per 120 m cell) would give them the same
  treatment; the win is small at dusk.
- **Light probes for the dynamic objects.** Cars and people still get hemisphere + env + unshadowed grid lights; a baked
  irradiance-probe grid (Cycles can bake spherical harmonics from an empty-sphere trick, or a `LightProbe` grid sampled from the
  ground lightmap) would give the "road bounce under the car" the brief mentions for moving objects too.
- **Midtown at 5 texels/m** needs either a 4096 × 4608 atlas or a split into midtown/residential (two atlases); the repack step
  in `build_city.py` already computes everything for that — it is one line in the district table.
- **Windows:** the bake lights the reveals from the hash-lit windows (35 % of their on-screen radiance). The hash runs in float64
  here and in float32 on the GPU, so a few windows differ between the bake and the emissive layer; an emissive mask in the
  facade textures (the phase-2 wish list) would make both come from one place.
- **Spot tail:** Cycles' spot blend is 7–50 % brighter than the game's smoothstep beyond 12 m from a lamp (in the dim tail,
  < 5 % of peak); a Light Path–driven cone factor would match it exactly.
- **Bake UASTC on System A** and ship `.b64.js` sidecars from the same script — today the KTX2 step runs on the Mac
  (`encode_ktx.sh`) because System A has no `ktx`.

## 6. Repeat after a world change
```
node dump_world.mjs                                   # Mac: world.js → work/world-dump.json (any change in world.js / assets.js / lighting.js)
rsync -az work/world-dump.json build_city.py bake_district.py systema:~/phase3-lightmaps/
ssh systema 'cd ~/phase3-lightmaps && blender -b -P build_city.py'          # CPU, ~15 s: city.blend, bake-plan, lm-layout, assets-uv2
for d in downtown midtown industrial:  systema-belegen "model-research" "lightmaps $d" 20
   ssh systema 'cd ~/phase3-lightmaps && blender -b work/city.blend -P bake_district.py -- '$d' --render --preview'
   systema-frei "model-research"
rsync -az systema:~/phase3-lightmaps/out/ out/ ; rsync -az --include='render_*' --include='preview_*' --exclude='*' systema:~/phase3-lightmaps/work/ work/
./encode_ktx.sh                                       # Mac: out/png/*.png → out/*.ktx2
node preview/shoot.mjs && python3 preview/compare.py  # viewer shots + compare strips
```
`bake_district.py` options: `--spp N --ao-spp N --scale S --ground-scale S --from-raw` (redo fill/denoise/encode without the GPU),
`--no-ground --no-buildings --views all --render --preview --selftest`.

## 7. Status

| # | item | state |
|---|---|---|
| 1 | city rebuilt from the game's own layout (141 buildings, 716 static props, 36 ground cells, 596 static lights, 9 408 emissive quads) | done — `work/city.blend` on System A, `build_city.py` |
| 2 | dusk rig matched (sky + hemisphere as world radiance, lights in radiometric units, key light real-time only) | done — calibrated, `calib_units.py` |
| 3 | downtown (downtown + plaza) buildings + ground cells | done — 4096 × 1280 @ 5 texels/m |
| 4 | midtown (midtown + residential + parking + gas) | done — 4096 × 3584 @ 4.05 texels/m |
| 5 | industrial (industrial + stunt + park) | done — 2048 × 1536 @ 5 texels/m |
| 6 | ground map, whole city | done — 4096² @ 8 texels/m, 100 % coverage |
| 7 | denoise (OIDN), fill, encode, KTX2 | done — 8 files, 25.8 MB on disk, ≈ 75 MB in VRAM with mips (BC7/ASTC 8 bpp + ETC 4 bpp) |
| 8 | verification renders + three.js reference viewer + compare strips (9 viewpoints) | done — `out/verify/` |
| 9 | wiring into the game | **done in round 6** (2026-09-02, `../NOTES.md` §11): packer keeps TEXCOORD_1, loader parses the KTX2, buildings per (kind, district) with `lmRect`, ground in world XZ, hemisphere / env-diffuse / static grid off on lightmapped materials, AO on env specular |

System A was taken in five windows (13:05, 13:17–13:23 ×2, 13:28–13:32, 14:04–14:07 plus the queued industrial section that
waited behind another session's render and ran 14:00–14:03); never longer than 7 minutes at a time, always released in between.
