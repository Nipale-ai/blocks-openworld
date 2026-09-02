# BLOCKS — an open-world game built by one model, overnight

A third-person open-world game that runs in the browser. Drive, get out, walk,
shoot, get chased by police. Built by **Claude Fable 5.1** on 1–2 September 2026,
from written briefs, on local hardware.

**▶ Play: https://nipale-ai.github.io/blocks-openworld/spiel/**

## What it has

- Third-person character: walk, run, sprint, jump
- Four vehicles you enter and leave, with a real tyre-slip physics model —
  suspension per wheel, weight transfer, five-speed automatic, handbrake slides
- Weapon wheel with bullet time: pistol, machine gun, rocket launcher
- **Wanted system, one to five stars** — patrol cars with sirens and light bars,
  officers on foot, roadblocks, evasion
- A city in six districts at dusk: street lights that pool on the road, lit
  windows, neon, wet asphalt
- **Four radio stations**, generated on the same machine — one with vocals
- Pedestrians, traffic, explosive barrels, wrecks

## How it was built

Nobody wrote gameplay code by hand. Each round was a written brief and an
automated gate; the model built, tested itself and iterated. Everything in
`vorgehen/` is the real material — the briefs, the gates, the tools, the
measurements.

| Round | Result | Wall clock | Cost |
|---|---|---|---|
| Graybox — every system, placeholder art | green, first try | 80 min | $31.34 |
| Police, wanted stars, camera fix | green, first try | 123 min | $32.11 |
| Dusk lighting | green, first try | 51 min | $19.92 |
| 3D assets in Blender (22 models) | green, first try | 60 min | $28.66 |
| Wiring the assets in, compression | green, first try | 21 min | $12.22 |
| Radio and video | green, first try | 32 min | — |
| Wiring the media in | green, first try | 26 min | $11.91 |

**Every round passed on the first attempt.** Costs are list-price equivalents
reported by the API, not what was actually billed.

## The local machine did the heavy lifting

An RTX 5090 in the next room, reached over SSH. The model wrote scripts and sent
them there:

- **Blender 5.2**, headless and scripted — 22 models, 171,758 triangles: four
  vehicles with LOD variants, three weapons, eight characters, two building
  sets, props
- **ComfyUI** — 73 PBR texture sets; photographic base textures via Z-Image-Turbo
- **ACE-Step** — four radio tracks, checked against spectrograms before use
- **LTX-2.5** — the clips playing on the billboards

Rendering time and token cost are decoupled: the model writes a script, the card
runs it, waiting costs nothing.

## What is weak, honestly

- **The character model** — tube arms with a visible shoulder seam, stub hands.
  It is the asset that got the least attention and it shows.
- **Baked lighting is missing.** Indirect light — neon colouring the wall
  opposite — was still being computed when this was published.
- The `POLICE` lettering was mirrored in one round because a numeric check
  passed while nobody looked at the image. It was found by looking.

## Repository layout

```
spiel/         the game — open index.html, or serve the folder
vorgehen/
  specs/       the briefs, one per round, unedited
  werkzeuge/   gates and tools, including the brightness check
  messungen/   cost and token measurements per round
  bilder/      screenshots and asset render sheets
  BAUPROTOKOLL-*.md   the model's own build notes
```

## The gate that mattered most

An earlier run shipped a game where 82 % of the frame was near-black while its
own report said the screenshots looked fine. So the gate measures pixel
brightness and fails if more than a third of the frame is black, or more than
half of the lower frame — where the ground is. `vorgehen/werkzeuge/pruefe_openworld.mjs`.

A green check nobody looked at is not a verdict.
