# bau_mech.py — builds the mech completely (geometry, pivots, names, materials), exports mech.glb (Draco) with the
# rig contract of ../src/mech.js, then poses it like the game does and saves mech.blend for render_mech.py.
#   ~/bin/blender -b -P bau_mech.py            (on brain; the folder is synced there by run-brain.sh)
# Repeatable: the same script gives the same mesh. All numbers are game metres, game axes (Y up, +Z front, −X right).
#
# Round 4 (KRITIK-runde-3.md, judged next to the client's reference — form language only, no copy of the design).
# Kept as accepted: wings, brightness, orange dosage, legs, claw feet, waist, symmetry. Changed, in the critique's order:
#   1 SHOULDER PLATES: three overlapping plates per side over a dark under-plate, ≥ 1.0 m wide, 0.9 m hanging over the arm
#   2 ARMS: upper arm = core + two armour shells with a gap; forearm = broad layered gauntlet, no flat bars
#   3 DETAIL DENSITY: no smooth face bigger than ~0.5 × 0.5 m — grooves (recessed lines), steps (offset plates), vents
#   4 HEAD: higher, wider helmet with the glowing visor slit standing free above the shoulder line and the wing roots
#   5 CHEST: the reactor is a dark lens with a thin orange ring; the light grey door panel is gone
#   6 STANCE: hips wider (±0.80) and each leg's geometry turned 10° outward (the pivots stay at zero rotation — mech.js
#     writes Hip/Knee/Foot rotations absolutely every frame, so the stance must live in the mesh, not in the pivots)
import bpy, bmesh, math, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mechlib import *

OUT_GLB = os.path.join(HERE, 'mech.glb'); OUT_BLEND = os.path.join(HERE, 'mech.blend'); OUT_REPORT = os.path.join(HERE, 'mech-report.json')
reset_scene()

# ---------------------------------------------------------------- materials (names are the contract) ----------------
MAT = {
    'body':   make_material('mech_body',   '#1a1d22', 0.18, 0.85),
    'plate':  make_material('mech_plate',  '#252a31', 0.30, 0.75),
    'under':  make_material('mech_under',  '#05060a', 0.90, 0.30),
    'hyd':    make_material('mech_hyd',    '#9aa4b0', 0.22, 0.95),
    'accent': make_material('mech_accent', '#ff7a1a', 0.35, 0.40),
    'glow':   make_material('mech_glow',   '#1a0c04', 0.40, 0.20, emit='#ff7a1a', strength=6.0),
    'eyes':   make_material('mech_eyes',   '#1a0c04', 0.30, 0.20, emit='#ffb347', strength=14.0),
    'edge':   make_material('mech_edge',   '#e8f0ff', 0.15, 0.90),
    'glass':  make_material('mech_glass',  '#0a1418', 0.08, 0.60),
}
body, plate, under, hyd, accent, glow, eyes, edge, glass = (MAT[k] for k in ('body', 'plate', 'under', 'hyd', 'accent', 'glow', 'eyes', 'edge', 'glass'))

# ---------------------------------------------------------------- skeleton --------------------------------------------
P = {}
def piv(name, parent, pos, rot=(0, 0, 0)):
    P[name] = empty(name, pos, parent, rot); return P[name]

LEG_YAW = {'L': 10.0, 'R': -10.0}       # toe-out of the leg GEOMETRY (degrees about the leg's own y axis)
def yawpt(S, p):
    """rotate a leg-local point by the leg's toe-out (used for pivots and anchors inside the turned leg)."""
    v = Matrix.Rotation(rad(LEG_YAW[S]), 3, 'Y') @ Vector(p); return (v.x, v.y, v.z)

root = piv('Mech', None, (0, 0, 0)); root.empty_display_size = 0.5
PELVIS_Y = 3.08                      # mech.js setzt Pelvis.position.y jeden Frame — dort steht dieselbe Zahl.
                                     # 3.08 statt 2.92: gestrecktere Ruhepose (Hip -0.34/Knee 0.72), Sohlen bleiben auf 0.
pelvis = piv('Pelvis', root, (0, PELVIS_Y, 0))
torso = piv('Torso', pelvis, (0, 0.30, 0))
head = piv('Head', torso, (0, 2.32, 0.12))                       # world 5.54: helmet top 6.03, free above shoulders (5.33) and wing roots (5.86)
backpack = piv('Backpack', torso, (0, 1.20, -0.98))              # world (0, 4.42, −0.98): wings, pods, back thrusters hang here
hatch = piv('Hatch', torso, (0, 1.85, 0.80))                    # hinge at the top edge of the door; rotation.x < 0 opens
cockpit = piv('Cockpit', torso, (0, 0.25, 0.50))                # pilot root (player.js parents the character here)
SH = {}; UA = {}; FA = {}; HIP = {}; KNEE = {}; FOOT = {}; POD = {}; NB = {}; NF = {}
SHX, UAX = 1.14, 0.32                                            # arm chain: 1.14 + 0.32 + forearm ±0.29 + 0.12 rad spread ≈ 2.07 m
for s, S in ((1, 'L'), (-1, 'R')):
    SH[S] = piv('Shoulder_' + S, torso, (s * SHX, 1.75, 0))
    UA[S] = piv('UpperArm_' + S, SH[S], (s * UAX, -0.15, 0))
    FA[S] = piv('Forearm_' + S, UA[S], (0, -1.28, 0))
    HIP[S] = piv('Hip_' + S, pelvis, (s * 0.71, -0.15, 0))       # etwas enger: schlanker, weniger gedrungen
    KNEE[S] = piv('Knee_' + S, HIP[S], (0, -1.42, 0))
    FOOT[S] = piv('Foot_' + S, KNEE[S], yawpt(S, (0, -1.38, 0.05)))   # ankle 0.31 m above the sole
    POD[S] = piv('Pod_' + S, backpack, (s * 0.72, 0.30, 0.08))
    NB[S] = piv('Nozzle_Back_' + S, backpack, (s * 0.42, -0.66, -0.20), rot=(0.55, 0, 0))   # local −Y = exhaust: back-down
    NF[S] = piv('Nozzle_Foot_' + S, FOOT[S], yawpt(S, (0, 0.14, -0.30)), rot=(0.35, 0, 0))
muzzle = piv('LaserMuzzle', FA['R'], (-0.03, -0.32, 1.70))
tubes = {}
for S in ('L', 'R'):
    for i in range(6):
        col, row = i % 3, i // 3
        tubes[(S, i)] = empty(f'Tube_{S}_{i}', ((col - 1) * 0.15, -0.10 + row * 0.20, 0.62), POD[S], size=0.05)

BK = Buckets()
def part(pivot, mat, bm): BK.add(pivot, mat, bm)
def lpart(S, pivot, mat, bm):
    """a leg part: the whole geometry is turned by the leg's toe-out about the pivot's y axis, the pivot stays at zero."""
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(rad(LEG_YAW[S]), 3, 'Y'), verts=bm.verts); BK.add(pivot, mat, bm)

# ---------------------------------------------------------------- helpers -------------------------------------------
def nozzle(pivot, R, mat_bell=plate):
    prof = [(1.00 * R, -0.34), (0.86 * R, -0.10), (0.78 * R, 0.10), (0.84 * R, 0.30), (0.62 * R, 0.36), (0.30 * R, 0.34),
            (0.28 * R, 0.22), (0.50 * R, 0.02), (0.72 * R, -0.16), (0.90 * R, -0.34)]
    part(pivot, mat_bell, lathe(prof, (0, 0, 0), axis='y', segs=32))
    part(pivot, glow, cyl(0.50 * R, 0.50 * R, 0.05, (0, 0.16, 0), 'y', 24, bevel=0.0))
    part(pivot, under, cyl(0.12 * R, 0.20 * R, 0.28, (0, 0.12, 0), 'y', 12, bevel=0.0))
    part(pivot, hyd, cyl(1.02 * R, 1.02 * R, 0.05, (0, -0.10, 0), 'y', 32, bevel=0.01))

def small_thruster(add, pos, rot, R):
    prof = [(1.0 * R, -0.30), (0.85 * R, -0.05), (0.80 * R, 0.20), (0.35 * R, 0.24), (0.32 * R, 0.10), (0.55 * R, -0.08), (0.88 * R, -0.30)]
    add(plate, lathe(prof, pos, axis='y', segs=20, rot=rot))
    add(glow, cyl(0.40 * R, 0.40 * R, 0.04, pos, 'y', 16, rot=rot, bevel=0.0))

def vent(add, pos, size, n, along='z', rot=(0, 0, 0)):
    """a dark recess with n bright fins — a radiator grille."""
    w, h, d = size
    add(under, box(size, pos, rot, bevel=0.008, segs=1))
    for i in range(n):
        t = (i + 0.5) / n - 0.5
        if along == 'z': fp = (pos[0], pos[1], pos[2] + t * d * 0.9); fs = (w + 0.02, h * 0.8, d / n * 0.35)
        elif along == 'y': fp = (pos[0], pos[1] + t * h * 0.9, pos[2]); fs = (w + 0.02, h / n * 0.35, d * 0.8)
        else: fp = (pos[0] + t * w * 0.9, pos[1], pos[2]); fs = (w / n * 0.35, h * 0.8, d + 0.02)
        add(plate, strip(fs, fp, rot))

def groove(add, size, pos, rot=(0, 0, 0)):
    """a recessed panel line: a 2 cm dark strip lying 8 mm proud of the plate — reads as a cut seam."""
    add(under, strip(size, pos, rot))

def seam(add, size, pos, rot=(0, 0, 0)):
    """a seam light: thin (≤ 2 cm) and short."""
    add(glow, strip(size, pos, rot))

S5 = 5; BV = 0.028      # silhouette plates: five bevel segments, 2.8 cm chamfer
S4 = 4

# ================================================================ PELVIS ==============================================
A = lambda mat, bm: part(pelvis, mat, bm)
A(under, box((1.10, 0.64, 0.86), (0, 0.02, 0), faces={'-y': dict(scale=(0.80, 0.80))}, bevel=0.03))
A(plate, box((1.40, 0.20, 1.04), (0, 0.24, 0), faces={'+y': dict(scale=(0.88, 0.88)), '-y': dict(scale=(0.96, 0.96))}))   # belt
groove(A, (1.30, 0.02, 0.03), (0, 0.24, 0.525))
# codpiece: long, pointed downward, stepped; one seam light
A(body, box((0.76, 0.80, 0.30), (0, -0.22, 0.42), rot=(-12, 0, 0), faces={'-y': dict(scale=(0.30, 0.55)), '+y': dict(scale=(1.0, 0.9))}, segs=S5, bevel=BV))
A(plate, box((0.42, 0.46, 0.06), (0, -0.16, 0.595), rot=(-12, 0, 0), faces={'-y': dict(scale=(0.35, 1.0))}, bevel=0.012))
groove(A, (0.02, 0.60, 0.03), (0, -0.30, 0.60), rot=(-12, 0, 0))
seam(A, (0.34, 0.018, 0.04), (0, 0.10, 0.585), rot=(-12, 0, 0))
# rear skirt, kicked back and pointed, with a step
A(plate, box((0.86, 0.72, 0.14), (0, -0.36, -0.46), rot=(16, 0, 0), faces={'-y': dict(scale=(0.45, 1.0))}, segs=S4, bevel=0.02))
A(body, box((0.50, 0.40, 0.05), (0, -0.30, -0.545), rot=(16, 0, 0), faces={'-y': dict(scale=(0.5, 1.0))}, bevel=0.01))
for s, S in ((1, 'L'), (-1, 'R')):
    # side skirts: long, flared, pointed; a second offset plate over it with a dark gap; a groove across
    A(body, box((0.16, 1.05, 0.70), (s * 0.80, -0.46, 0.04), rot=(0, 0, s * 12), faces={'-y': dict(scale=(0.9, 0.32)), '+y': dict(scale=(1.0, 0.95))}, segs=S5, bevel=BV))
    A(plate, box((0.06, 0.72, 0.48), (s * 0.915, -0.52, 0.06), rot=(0, 0, s * 12), faces={'-y': dict(scale=(0.9, 0.35))}, bevel=0.012))
    groove(A, (0.03, 0.02, 0.60), (s * 0.895, -0.12, 0.04), rot=(0, 0, s * 12))
    A(hyd, cyl(0.32, 0.32, 0.16, (s * 0.64, -0.15, 0), 'x', 32, bevel=0.02, bsegs=3))                # hip joint housing ring
    empty('HydA_Waist' + S, (s * 0.36, 0.18, -0.34), pelvis, size=0.05)

# ================================================================ TORSO ==============================================
T = lambda mat, bm: part(torso, mat, bm)
T(under, box((0.58, 0.84, 0.54), (0, 0.32, 0), faces={'-y': dict(scale=(0.92, 0.92))}, bevel=0.03, segs=2))   # waist core
T(plate, cyl(0.36, 0.36, 0.10, (0, 0.02, 0), 'y', 32))                              # waist bearing
T(hyd, cyl(0.38, 0.38, 0.03, (0, 0.06, 0), 'y', 32, bevel=0.0))
for s in (1, -1):
    for zz in (0.20, -0.20):
        T(under, tube((s * 0.23, 0.65, zz), (s * 0.31, -0.28, zz * 1.2), 0.026, 8))
        T(hyd, tube((s * 0.27, 0.65, zz * 0.5), (s * 0.34, -0.28, zz * 0.7), 0.016, 6))
    empty('HydB_Waist' + ('L' if s > 0 else 'R'), (s * 0.27, 0.68, -0.34), torso, size=0.05)
# chest core: wide and deep at the collar, 0.6 at the waist
T(under, box((1.36, 1.48, 1.16), (0, 1.40, 0), faces={'-y': dict(scale=(0.44, 0.52)), '+y': dict(scale=(0.96, 0.96))}, bevel=0.04))
# collar deck (grooved) + neck (long, visible — the head stands on it)
T(plate, box((1.64, 0.18, 1.18), (0, 2.00, -0.04), faces={'+y': dict(scale=(0.86, 0.80)), '+z': dict(scale=(0.80, 1.0)), '-y': dict(scale=(0.96, 1.0))}, bevel=0.025, segs=S4))
T(body, box((0.94, 0.16, 0.44), (0, 2.05, 0.52), faces={'+z': dict(scale=(0.70, 0.45))}, bevel=0.015))
groove(T, (0.02, 0.03, 0.90), (0, 2.095, -0.04)); groove(T, (1.2, 0.03, 0.02), (0, 2.095, 0.30))
T(hyd, cyl(0.15, 0.19, 0.42, (0, 2.28, 0.12), 'y', 20))
# Kopf-Einfassung (Ansage Niklas 03.09.2026): Nackenschild hinten, Kragenwangen seitlich, hohe Brustplatte vorn —
# der Helm sitzt tief zwischen Panzerung, nicht frei auf einem Hals.
T(body, box((1.14, 0.98, 0.46), (0, 2.50, -0.58),
            faces={'+y': dict(scale=(0.40, 0.56), shift=(0, -0.06)), '-z': dict(scale=(0.86, 0.92)), '-y': dict(scale=(0.98, 1.0))}, segs=S5, bevel=0.03))
T(body, box((0.34, 0.44, 0.34), (0, 2.94, -0.62), faces={'+y': dict(scale=(0.36, 0.44), shift=(0, -0.04))}, segs=S4, bevel=0.02))   # Grat
for s2 in (1, -1):                                                   # Schulterrampen: fuehren die Schraege zum Kragen
    T(plate, box((0.40, 0.10, 0.40), (s2 * 0.40, 2.72, -0.50), rot=(0, 0, s2 * 26),
                 faces={('+x' if s2 > 0 else '-x'): dict(scale=(0.6, 0.7))}, bevel=0.012))
T(plate, box((0.52, 0.62, 0.06), (0, 2.56, -0.31), faces={'+y': dict(scale=(0.46, 1.0))}, bevel=0.012))
seam(T, (0.34, 0.018, 0.04), (0, 2.82, -0.32))
for s2 in (1, -1):
    T(body, box((0.30, 0.74, 0.66), (s2 * 0.54, 2.32, -0.22), rot=(0, 0, s2 * -7),
                faces={'+y': dict(scale=(0.62, 0.70)), '+z': dict(scale=(1.0, 0.72))}, segs=S4, bevel=0.025))
    T(plate, box((0.07, 0.48, 0.40), (s2 * 0.72, 2.30, -0.18), rot=(0, 0, s2 * -7), faces={'+y': dict(scale=(0.7, 0.8))}, bevel=0.01))
    groove(T, (0.02, 0.40, 0.03), (s2 * 0.755, 2.30, -0.18), rot=(0, 0, s2 * -7))
T(body, box((0.86, 0.46, 0.38), (0, 2.16, 0.46), faces={'+y': dict(scale=(0.62, 0.54)), '+z': dict(scale=(0.76, 0.66))}, segs=S4, bevel=0.026))
T(glow, box((0.34, 0.03, 0.04), (0, 2.30, 0.645), bevel=0.0, segs=0))
T(under, cyl(0.22, 0.24, 0.08, (0, 2.15, 0.12), 'y', 20, bevel=0.0))
# back plate (long, tapered, grooved, stepped)
T(plate, box((1.20, 1.38, 0.30), (0, 1.30, -0.66), faces={'-y': dict(scale=(0.62, 1.0)), '+y': dict(scale=(0.92, 1.0))}, bevel=0.025, segs=S4))
T(body, box((0.70, 0.60, 0.05), (0, 1.55, -0.83), faces={'-y': dict(scale=(0.7, 1.0))}, bevel=0.01))
for s in (1, -1): groove(T, (0.02, 1.1, 0.03), (s * 0.34, 1.30, -0.815))
# cockpit cavity + seat (seen when the hatch is open)
T(under, box((0.72, 1.20, 0.46), (0, 1.22, 0.46), bevel=0.02, segs=1))
T(hyd, box((0.44, 0.08, 0.30), (0, 0.70, 0.46), bevel=0.01, segs=1))
T(hyd, box((0.44, 0.50, 0.06), (0, 1.00, 0.30), bevel=0.01, segs=1))
T(glass, box((0.40, 0.26, 0.03), (0, 1.48, 0.46), bevel=0.0, segs=0))
for s, S in ((1, 'L'), (-1, 'R')):
    # breast plates: long, thick, angled; two grooves, a step, a vent slot
    T(body, box((0.70, 1.08, 0.42), (s * 0.43, 1.42, 0.56), rot=(-8, s * 18, 0), faces={'+y': dict(scale=(0.80, 1.0), shift=(s * -0.04, 0)), '-y': dict(scale=(0.55, 0.8))}, segs=S5, bevel=BV))
    groove(T, (0.025, 0.86, 0.03), (s * 0.30, 1.30, 0.775), rot=(-8, s * 18, 0))
    groove(T, (0.40, 0.02, 0.03), (s * 0.43, 1.66, 0.79), rot=(-8, s * 18, 0))
    groove(T, (0.34, 0.02, 0.03), (s * 0.43, 1.18, 0.755), rot=(-8, s * 18, 0))
    T(body, box((0.26, 0.30, 0.04), (s * 0.50, 1.40, 0.785), rot=(-8, s * 18, 0), faces={'-y': dict(scale=(0.7, 1.0))}, bevel=0.008))   # step
    vent(T, (s * 0.52, 1.74, 0.77), (0.20, 0.10, 0.04), 3, along='x', rot=(-8, s * 18, 0))
    seam(T, (0.30, 0.018, 0.04), (s * 0.40, 1.02, 0.62), rot=(0, s * 16, 0))
    # flank plates: long, thick, tapered; groove + step + vent
    T(body, box((0.34, 1.18, 1.00), (s * 0.80, 1.42, -0.06), faces={'-y': dict(scale=(0.85, 0.55)), '+y': dict(scale=(1.0, 0.95))}, segs=S5, bevel=BV))
    groove(T, (0.03, 0.02, 0.80), (s * 0.975, 1.62, -0.06)); groove(T, (0.03, 0.80, 0.02), (s * 0.975, 1.42, -0.40))
    T(plate, box((0.05, 0.50, 0.40), (s * 0.985, 1.30, 0.16), faces={'-y': dict(scale=(1.0, 0.7))}, bevel=0.01))   # step
    vent(T, (s * 0.955, 1.46, -0.30), (0.05, 0.36, 0.30), 4, along='y')

# ================================================================ HATCH: dark lens, thin orange ring ================
H = lambda mat, bm: part(hatch, mat, bm)
H(body, box((0.64, 1.30, 0.14), (0, -0.67, 0.0), faces={'-y': dict(scale=(0.58, 1.0)), '+y': dict(scale=(0.96, 1.0))}, segs=S5, bevel=BV))
H(body, box((0.40, 0.62, 0.05), (0, -0.56, 0.09), faces={'-y': dict(scale=(0.60, 1.0))}, bevel=0.012))   # step, same tone (no light wedge)
groove(H, (0.02, 0.50, 0.03), (0, -0.56, 0.115)); groove(H, (0.44, 0.02, 0.03), (0, -0.22, 0.08)); groove(H, (0.30, 0.02, 0.03), (0, -1.20, 0.08))
H(glass, cyl(0.085, 0.085, 0.05, (0, -1.00, 0.095), 'z', 32, bevel=0.0))                   # the dark lens
H(glow, lathe([(0.088, 0.075), (0.104, 0.075), (0.104, 0.115), (0.088, 0.115)], (0, -1.00, 0.0), axis='z', segs=32))   # thin orange ring
H(under, lathe([(0.104, 0.07), (0.13, 0.07), (0.13, 0.10), (0.104, 0.10)], (0, -1.00, 0.0), axis='z', segs=32))   # dark bezel
H(accent, strip((0.14, 0.03, 0.02), (0, -0.30, 0.12), rot=(0, 0, 35)))

# ================================================================ HEAD: helmet, wide face, free above the shoulders ==
K = lambda mat, bm: part(head, mat, bm)
K(hyd, cyl(0.13, 0.15, 0.20, (0, -0.02, 0), 'y', 20))
# Keil: hinten hoch und breit, nach vorn schmal und flach auslaufend — kein Kasten
K(body, box((0.49, 0.40, 0.96), (0, 0.20, 0.12),
            faces={'+z': dict(scale=(0.34, 0.30), shift=(0, -0.09)), '-z': dict(scale=(0.70, 0.62), shift=(0, -0.05)),
                   '+y': dict(scale=(0.72, 0.80), shift=(0, -0.10))}, segs=S5, bevel=0.022))
K(body, box((0.20, 0.20, 0.74), (0, 0.42, 0.02),                                     # Grat obenauf
            faces={'+z': dict(scale=(0.22, 0.30), shift=(0, -0.06)), '-z': dict(scale=(0.85, 0.7))}, segs=S4, bevel=0.014))
K(plate, box((0.40, 0.05, 0.44), (0, 0.40, -0.22), faces={'-z': dict(scale=(0.60, 1.0))}, bevel=0.01))
groove(K, (0.02, 0.14, 0.44), (0, 0.475, -0.06))
# Dreiecks-Visier: laeuft nach vorn spitz zu und faellt schraeg ab
K(under, box((0.50, 0.20, 0.50), (0, 0.19, 0.30), rot=(-16, 0, 0),
             faces={'+z': dict(scale=(0.30, 0.34), shift=(0, -0.03)), '+y': dict(scale=(0.86, 0.9))}, bevel=0.012, segs=1))
for s in (1, -1):                                                    # Dreiecks-Visier: zwei schraege Balken bilden ein V
    K(eyes, box((0.30, 0.062, 0.10), (s * 0.115, 0.225, 0.345), rot=(-16, 0, s * 21), bevel=0.0, segs=0))
    K(under, box((0.34, 0.045, 0.07), (s * 0.125, 0.285, 0.335), rot=(-16, 0, s * 21), bevel=0.0, segs=0))   # Blende darueber
K(eyes, box((0.075, 0.05, 0.09), (0, 0.168, 0.352), rot=(-16, 0, 0), bevel=0.0, segs=0))                     # Spitze des V
K(under, box((0.28, 0.12, 0.40), (0, 0.02, 0.20), faces={'+z': dict(scale=(0.42, 0.34), shift=(0, 0.02))}, bevel=0.01))   # Kinnkeil
for s in (1, -1):
    K(plate, box((0.06, 0.28, 0.60), (s * 0.255, 0.17, 0.04), rot=(0, 0, s * -4),
                 faces={'+z': dict(scale=(0.34, 0.30), shift=(0, -0.06)), '-z': dict(scale=(1.0, 0.78))}, bevel=0.01))     # Wangenkeil
    K(accent, box((0.03, 0.045, 0.26), (s * 0.28, 0.24, 0.08), rot=(0, 0, s * -4), bevel=0.0, segs=0))
    groove(K, (0.025, 0.02, 0.34), (s * 0.265, 0.08, 0.02))

# ================================================================ BACKPACK: Ruecken-Fluegel (Runde 6 neu), pods, thrusters =======
Bp = lambda mat, bm: part(backpack, mat, bm)
Bp(under, box((1.16, 1.04, 0.56), (0, -0.05, 0), faces={'+y': dict(scale=(0.82, 0.88)), '-y': dict(scale=(0.88, 0.88))}, bevel=0.04))
Bp(plate, box((0.26, 1.04, 0.18), (0, 0.0, -0.33), faces={'+y': dict(scale=(0.65, 1.0)), '-y': dict(scale=(0.85, 1.0))}, bevel=0.015))
seam(Bp, (0.60, 0.018, 0.04), (0, 0.46, -0.31))
vent(Bp, (0, -0.32, -0.43), (0.30, 0.26, 0.06), 4, along='y')
# ---- Ruecken-Faecher (Runde 6): drei lange Klingen je Seite, von der Schulter nach hinten bis knapp ueber den Boden.
#      Jede Klinge haengt an einem eigenen Pivot (Wing1_L … Wing3_R) — im Flug faechern sie auf, am Boden liegen sie an.
#      Die RUHELAGE steckt in der Geometrie, nicht im Pivot: set_pose() und mech.js nullen jeden Pivot, den sie nicht
#      selbst setzen — eine Neigung am Empty waere jedes Mal weggedreht worden (Befund 01:12). Pivot 0 = angelegt.
WING_BLADES = [   # (x-Wurzel, Laenge, Breite, Neigung nach hinten, Faecherung nach aussen, Dicke)
    (0.32, 4.60, 0.72, 0.30, 0.06, 0.115),
    (0.70, 4.70, 0.78, 0.34, 0.18, 0.125),
    (1.02, 4.30, 0.64, 0.40, 0.32, 0.100),
]
for s, S in ((1, 'L'), (-1, 'R')):
    for i, (bx, BL, BW, brx, brz, BT) in enumerate(WING_BLADES):
        wg = piv('Wing%d_%s' % (i + 1, S), backpack, (s * bx, 0.62, -0.10))
        R = game_rot_game(brx, 0, s * brz)
        Wl = lambda mat, sz, lp, q=wg, RR=R, **kw: part(q, mat, box(sz, tuple(RR @ Vector(lp)), rot=RR, **kw))
        Wc = lambda mat, *a2, q=wg, RR=R, **kw: part(q, mat, cyl(*a2, rot=RR, **kw))
        out = '+x' if s > 0 else '-x'
        part(wg, hyd, cyl(0.13, 0.13, 0.34, tuple(R @ Vector((0, 0.06, 0))), 'x', 20, rot=R, bevel=0.018, bsegs=2))
        Wl(under, (BW + 0.10, 0.34, 0.34), (0, -0.14, 0.0), faces={'-y': dict(scale=(0.86, 0.82))}, bevel=0.02)
        yc = -0.30 - BL * 0.5
        Wl(body, (BW, BL, BT), (0, yc, 0),
           faces={'-y': dict(scale=(0.34, 0.62), shift=(s * 0.15, -0.01)), '+y': dict(scale=(0.80, 0.92))},
           segs=S5, bevel=0.02)
        Wl(plate, (BW * 0.54, BL * 0.72, 0.04), (s * 0.04, yc + 0.30, BT * 0.5 + 0.015),
           faces={'-y': dict(scale=(0.40, 1.0), shift=(s * 0.11, 0))}, bevel=0.01)
        Wl(edge, (0.055, BL * 0.90, 0.06), (s * (BW * 0.5 - 0.025), yc + 0.04, 0.0),
           faces={'-y': dict(scale=(0.8, 0.8), shift=(s * 0.07, 0))}, bevel=0.0, segs=0)
        for k in (0.20, 0.42, 0.64, 0.84):
            Wl(under, (BW * (0.92 - k * 0.6), 0.03, 0.028), (s * k * 0.07, -0.30 - BL * k, BT * 0.5 + 0.02), bevel=0.0, segs=0)
        if i == 1:
            Wl(glow, (0.04, 0.70, 0.028), (s * (BW * 0.5 - 0.09), -1.10, BT * 0.5 + 0.03), bevel=0.0, segs=0)
            part(wg, under, cyl(0.10, 0.12, 0.24, tuple(R @ Vector((s * -0.02, -0.66, -BT * 0.5 - 0.10))), 'z', 16, rot=R, bevel=0.012))
            part(wg, accent, cyl(0.07, 0.07, 0.04, tuple(R @ Vector((s * -0.02, -0.66, -BT * 0.5 - 0.24))), 'z', 14, rot=R, bevel=0.0))

for s, S in ((1, 'L'), (-1, 'R')):
    pod = POD[S]; Pd = lambda mat, bm, pod=pod: part(pod, mat, bm)
    Pd(plate, box((0.54, 0.42, 1.04), (0, 0, 0), faces={'+z': dict(scale=(0.86, 0.82)), '-z': dict(scale=(0.80, 0.70)), '+y': dict(scale=(0.92, 0.96))}, segs=S4, bevel=0.02))
    Pd(under, box((0.46, 0.36, 0.05), (0, 0, 0.505), bevel=0.008, segs=1))
    groove(Pd, (0.02, 0.32, 0.03), (s * 0.275, 0, 0.0)); groove(Pd, (0.40, 0.02, 0.03), (0, 0.215, 0.0))
    for i in range(6):
        col, row = i % 3, i // 3; x, y = (col - 1) * 0.15, -0.10 + row * 0.20
        Pd(under, cyl(0.06, 0.06, 0.12, (x, y, 0.54), 'z', 14, bevel=0.0, cap=True))
        Pd(accent, cyl(0.032, 0.032, 0.03, (x, y, 0.585), 'z', 12, bevel=0.0))
    nozzle(NB[S], 0.29)

# ================================================================ SHOULDERS / ARMS ===================================
for s, S in ((1, 'L'), (-1, 'R')):
    sh, ua, fa = SH[S], UA[S], FA[S]
    Sh = lambda mat, bm, sh=sh: part(sh, mat, bm); Ua = lambda mat, bm, ua=ua: part(ua, mat, bm); Fa = lambda mat, bm, fa=fa: part(fa, mat, bm)
    Sh(hyd, cyl(0.20, 0.20, 0.42, (s * -0.06, -0.05, 0), 'x', 32, bevel=0.02, bsegs=3))
    srot = (6, 0, s * 6)
    # 1 THE SHOULDER: dark under-plate, big main plate (1.06 wide, 0.90 hanging), lower outer plate, top cap — three layers with gaps
    Sh(under, box((0.96, 0.84, 1.34), (s * 0.36, -0.14, 0.0), rot=srot, faces={'+z': dict(scale=(0.45, 0.3), shift=(0, -0.25)), '-y': dict(scale=(0.75, 0.75))}, bevel=0.01, segs=1))
    Sh(body, box((1.06, 0.90, 1.50), (s * 0.38, -0.08, 0.0), rot=srot, faces={'+z': dict(scale=(0.42, 0.28), shift=(0, -0.30)), '-z': dict(scale=(0.88, 0.85)), '-y': dict(scale=(0.72, 0.70)), '+y': dict(scale=(0.92, 0.92))}, segs=S5, bevel=BV))
    Sh(body, box((0.86, 0.46, 1.24), (s * 0.46, -0.50, 0.06), rot=srot, faces={'+z': dict(scale=(0.50, 0.40), shift=(0, -0.15)), '-y': dict(scale=(0.80, 0.80)), '+y': dict(scale=(0.96, 1.0))}, segs=S5, bevel=0.024))   # lower plate, hangs over the arm
    Sh(plate, box((0.66, 0.06, 0.94), (s * 0.32, 0.40, -0.04), rot=srot, faces={'+z': dict(scale=(0.50, 1.0)), '-z': dict(scale=(0.85, 1.0))}, bevel=0.012))   # top cap
    # grosse Schulterplatte: steht ueber dem Helm (world 6.03) und deckt den Kopf seitlich — Ansage Niklas 03.09.2026
    prot = (9, s * 7, s * 21); pout = '+x' if s > 0 else '-x'
    Sh(under, box((1.34, 0.09, 1.16), (s * 0.60, 0.90, -0.10), rot=prot,
                  faces={pout: dict(scale=(0.66, 0.60), shift=(0, -0.10))}, bevel=0.015, segs=1))
    Sh(body, box((1.46, 0.23, 1.32), (s * 0.62, 1.00, -0.12), rot=prot,
                 faces={pout: dict(scale=(0.58, 0.54), shift=(0, -0.12)), '+z': dict(scale=(0.86, 0.88)), '-z': dict(scale=(0.92, 0.94))},
                 segs=S5, bevel=0.028))
    Sh(plate, box((0.92, 0.05, 0.74), (s * 0.72, 1.10, -0.06), rot=prot,
                  faces={pout: dict(scale=(0.62, 0.7))}, bevel=0.012))
    Sh(glow, box((0.52, 0.03, 0.05), (s * 0.50, 1.06, 0.56), rot=prot, faces={pout: dict(scale=(0.5, 0.6))}, bevel=0.0, segs=0))
    Sh(hyd, cyl(0.10, 0.10, 0.44, (s * 0.30, 0.66, -0.16), 'y', 16, rot=(0, 0, s * 16), bevel=0.014))   # Traeger
    groove(Sh, (0.90, 0.02, 0.03), (s * 0.60, 1.09, -0.34), rot=prot)
    groove(Sh, (0.02, 0.60, 0.03), (s * 0.76, -0.02, 0.10), rot=srot); groove(Sh, (0.60, 0.02, 0.03), (s * 0.40, 0.22, 0.76), rot=srot)
    groove(Sh, (0.02, 0.03, 0.90), (s * 0.30, 0.37, -0.10), rot=srot)
    vent(Sh, (s * 0.905, 0.10, -0.40), (0.05, 0.24, 0.30), 4, along='y', rot=srot)
    Sh(edge, strip((0.015, 0.02, 0.90), (s * 0.86, 0.30, -0.08), rot=srot))                    # thin white edge light on the outer top edge
    seam(Sh, (0.02, 0.018, 0.50), (s * 0.60, -0.62, 0.30), rot=srot)
    if s > 0: Sh(accent, strip((0.02, 0.10, 0.30), (s * 0.905, -0.40, -0.30), rot=srot))
    # 2 UPPER ARM: core + two armour shells (outer, front) over it with a gap, back plate, hose
    Ua(under, cyl(0.19, 0.17, 1.20, (0, -0.60, 0), 'y', 18))
    Ua(body, box((0.30, 1.08, 0.54), (s * 0.13, -0.60, 0), rot=(0, 0, s * -3), faces={'-y': dict(scale=(0.70, 0.66)), '+y': dict(scale=(0.90, 0.88))}, segs=S5, bevel=0.024))   # outer shell
    Ua(body, box((0.36, 0.86, 0.16), (s * 0.02, -0.66, 0.30), faces={'-y': dict(scale=(0.66, 1.0)), '+y': dict(scale=(0.9, 1.0))}, segs=S4, bevel=0.018))   # front shell
    Ua(plate, box((0.32, 0.64, 0.12), (0, -0.64, -0.30), faces={'-y': dict(scale=(0.60, 1.0))}, bevel=0.012))                                         # back plate
    Ua(plate, box((0.06, 0.60, 0.40), (s * 0.30, -0.50, 0.0), rot=(0, 0, s * -3), faces={'-y': dict(scale=(1.0, 0.70))}, bevel=0.01))               # offset outer panel
    groove(Ua, (0.03, 0.02, 0.40), (s * 0.28, -0.86, 0.0), rot=(0, 0, s * -3)); groove(Ua, (0.28, 0.02, 0.03), (s * 0.02, -0.40, 0.385))
    Ua(under, tube((s * -0.08, -0.20, -0.20), (s * -0.04, -1.08, -0.24), 0.02, 8))
    empty('HydA_Elbow' + S, (s * -0.05, -0.35, -0.28), ua, size=0.05)
    empty('HydB_Elbow' + S, (s * -0.03, -0.52, -0.31), fa, size=0.05)
    # 2 FOREARM: broad layered gauntlet — elbow disc, wide cuff at the elbow, main block, top plate, outer blade, wrist ring, fist
    Fa(hyd, cyl(0.19, 0.19, 0.40, (0, -0.05, 0), 'x', 32, bevel=0.02, bsegs=3))
    Fa(body, box((0.54, 0.44, 0.60), (0, -0.34, 0.02), faces={'-y': dict(scale=(0.92, 0.92)), '+y': dict(scale=(0.80, 0.80))}, segs=S4, bevel=0.022))      # cuff
    Fa(body, box((0.52, 1.12, 0.54), (0, -0.74, 0.02), faces={'-y': dict(scale=(0.78, 0.82)), '+y': dict(scale=(0.92, 0.92))}, segs=S5, bevel=BV))       # main block
    Fa(plate, box((0.40, 0.60, 0.06), (0, -0.70, 0.315), faces={'-y': dict(scale=(0.62, 1.0))}, bevel=0.012))                                            # top (front) plate
    groove(Fa, (0.02, 0.50, 0.03), (0, -0.70, 0.35)); groove(Fa, (0.36, 0.02, 0.03), (0, -0.98, 0.30)); groove(Fa, (0.36, 0.02, 0.03), (0, -0.54, 0.31))
    Fa(body, box((0.06, 1.40, 0.56), (s * 0.26, -0.86, 0.0), faces={'-y': dict(scale=(1.0, 0.22)), '+y': dict(scale=(1.0, 0.80))}, segs=S4, bevel=0.015))   # outer blade, pointed past the fist
    Fa(edge, strip((0.012, 0.50, 0.03), (s * 0.295, -0.70, 0.20)))
    Fa(hyd, cyl(0.24, 0.24, 0.06, (0, -1.24, 0.02), 'y', 24, bevel=0.0))                                                                              # wrist ring
    Fa(plate, box((0.42, 0.32, 0.44), (0, -1.42, 0.05), faces={'-y': dict(scale=(0.80, 0.80))}, bevel=0.018))                                          # fist
    for k in range(3): groove(Fa, (0.02, 0.24, 0.05), ((k - 1) * 0.12, -1.42, 0.27))
    if s < 0:   # right: the laser on TOP of the forearm — housing, barrel, muzzle, one glow ring
        # Minigun um 50 % hochskaliert (Ansage Niklas 03.09.2026) — Muendung bleibt auf z 1.70, wo LaserMuzzle sitzt
        Fa(plate, box((0.36, 0.36, 1.40), (s * 0.03, -0.30, 0.46), faces={'+z': dict(scale=(0.70, 0.70)), '-z': dict(scale=(0.9, 0.9))}, segs=S4, bevel=0.022))
        AX = (s * 0.03, -0.30)
        Fa(plate, cyl(0.172, 0.172, 0.30, (AX[0], AX[1], 1.03), 'z', 24, bevel=0.016))                                   # Gehaeuse, aus dem die Laeufe treten
        Fa(under, cyl(0.150, 0.150, 0.08, (AX[0], AX[1], 1.20), 'z', 24, bevel=0.0))                                     # hintere Laufklemme
        for k in range(6):
            a = k * math.pi / 3.0
            Fa(hyd, cyl(0.039, 0.039, 0.66, (AX[0] + 0.102 * math.cos(a), AX[1] + 0.102 * math.sin(a), 1.31), 'z', 12, bevel=0.0))
        Fa(under, cyl(0.054, 0.054, 0.62, (AX[0], AX[1], 1.30), 'z', 12, bevel=0.0))                                     # Mittelspindel
        Fa(under, lathe([(0.112, 1.52), (0.168, 1.53), (0.168, 1.66), (0.128, 1.67), (0.112, 1.67)], (AX[0], AX[1], 0), axis='z', segs=24))   # Muendungsring
        Fa(glow, cyl(0.180, 0.180, 0.03, (AX[0], AX[1], 0.90), 'z', 24, bevel=0.0))                                      # oranger Ring am Gehaeuse
        Fa(accent, strip((0.018, 0.16, 0.30), (s * 0.215, -0.30, 0.28)))
    P['LaserMuzzle'].location = B(-0.03, -0.32, 1.70)

# ================================================================ LEGS (accepted geometry, turned 10° outward) ======
for s, S in ((1, 'L'), (-1, 'R')):
    hip, knee, foot = HIP[S], KNEE[S], FOOT[S]
    Hp = lambda mat, bm, hip=hip, S=S: lpart(S, hip, mat, bm); Kn = lambda mat, bm, knee=knee, S=S: lpart(S, knee, mat, bm); Ft = lambda mat, bm, foot=foot, S=S: lpart(S, foot, mat, bm)
    # thigh
    Hp(hyd, cyl(0.26, 0.26, 0.38, (0, 0, 0), 'x', 32, bevel=0.02, bsegs=3))
    Hp(under, cyl(0.24, 0.20, 1.35, (0, -0.72, 0), 'y', 18))
    Hp(body, box((0.62, 1.15, 0.50), (s * 0.02, -0.66, 0.16), rot=(-6, 0, 0), faces={'-y': dict(scale=(0.70, 0.72)), '+y': dict(scale=(0.88, 0.88))}, segs=S5, bevel=BV))
    Hp(plate, box((0.36, 0.58, 0.05), (s * 0.02, -0.54, 0.405), rot=(-6, 0, 0), faces={'-y': dict(scale=(0.62, 1.0))}, bevel=0.012))   # offset thigh panel
    groove(Hp, (0.30, 0.02, 0.03), (s * 0.02, -0.95, 0.395), rot=(-6, 0, 0)); groove(Hp, (0.02, 0.40, 0.03), (s * 0.24, -0.62, 0.41), rot=(-6, 0, 0))
    Hp(body, box((0.14, 1.34, 0.50), (s * 0.36, -0.74, -0.04), rot=(0, 0, s * 3), faces={'-y': dict(scale=(1.0, 0.50)), '+y': dict(scale=(1.0, 0.85))}, segs=S4, bevel=0.015))   # long outer strip
    groove(Hp, (0.03, 0.02, 0.40), (s * 0.43, -0.45, -0.04), rot=(0, 0, s * 3)); groove(Hp, (0.03, 0.02, 0.36), (s * 0.43, -0.95, -0.04), rot=(0, 0, s * 3))
    Hp(plate, box((0.34, 0.90, 0.20), (s * -0.18, -0.64, -0.30), faces={'-y': dict(scale=(0.60, 1.0))}, bevel=0.012))
    Hp(plate, box((0.40, 0.84, 0.16), (0, -0.62, -0.34), faces={'-y': dict(scale=(0.55, 1.0))}, bevel=0.012))
    Hp(body, box((0.50, 0.46, 0.44), (0, -1.26, 0.20), rot=(-10, 0, 0), faces={'-y': dict(scale=(0.70, 0.75)), '+y': dict(scale=(0.90, 0.90))}, segs=S5, bevel=0.02))   # knee cap
    seam(Hp, (0.26, 0.018, 0.04), (0, -1.03, 0.41), rot=(-8, 0, 0))
    Hp(under, tube((s * 0.18, -0.30, -0.28), (s * 0.13, -1.22, -0.28), 0.026, 8))
    empty('HydA_Knee' + S, yawpt(S, (s * 0.02, -0.50, -0.34)), hip, size=0.05)
    empty('HydB_Knee' + S, yawpt(S, (s * 0.02, -0.70, -0.30)), knee, size=0.05)
    empty('HydA_Ankle' + S, yawpt(S, (0, -0.72, 0.26)), knee, size=0.05)
    empty('HydB_Ankle' + S, yawpt(S, (0, 0.0, 0.34)), foot, size=0.05)
    # shin
    Kn(hyd, cyl(0.22, 0.22, 0.46, (0, 0, 0), 'x', 32, bevel=0.02, bsegs=3))
    Kn(body, box((0.14, 0.42, 0.74), (0, -0.14, 0.44), rot=(-25, 0, 0), faces={'+z': dict(scale=(0.25, 0.08)), '-z': dict(scale=(1.0, 0.9))}, segs=S5, bevel=0.012))   # knee blade
    Kn(under, cyl(0.20, 0.18, 1.25, (0, -0.68, 0), 'y', 18))
    Kn(body, box((0.50, 1.15, 0.46), (0, -0.66, 0.14), faces={'-y': dict(scale=(0.68, 0.70)), '+y': dict(scale=(0.85, 0.88))}, segs=S5, bevel=BV))
    Kn(plate, box((0.30, 0.60, 0.05), (0, -0.60, 0.365), faces={'-y': dict(scale=(0.62, 1.0))}, bevel=0.012))   # offset shin panel
    groove(Kn, (0.34, 0.02, 0.03), (0, -1.02, 0.36)); groove(Kn, (0.02, 0.36, 0.03), (0, -0.40, 0.37))
    Kn(body, box((0.14, 1.30, 0.50), (s * 0.31, -0.72, -0.08), faces={'-y': dict(scale=(1.0, 0.40)), '+y': dict(scale=(1.0, 0.9))}, segs=S4, bevel=0.015))   # long outer strip
    groove(Kn, (0.03, 0.02, 0.40), (s * 0.38, -0.50, -0.08)); groove(Kn, (0.03, 0.02, 0.34), (s * 0.38, -1.00, -0.08))
    Kn(plate, box((0.26, 0.96, 0.46), (s * -0.24, -0.72, -0.12), faces={'-y': dict(scale=(0.9, 0.60))}, bevel=0.018))
    Kn(plate, box((0.44, 0.90, 0.26), (0, -0.74, -0.30), faces={'-y': dict(scale=(0.8, 0.70)), '+y': dict(scale=(0.9, 0.9))}, bevel=0.018))
    Kn(plate, box((0.36, 0.32, 0.36), (0, -1.20, -0.04), faces={'-y': dict(scale=(0.80, 0.80))}, bevel=0.015))                          # ankle guard
    seam(Kn, (0.018, 0.40, 0.03), (0, -0.58, 0.395))
    small_thruster(Kn, (s * 0.13, -0.86, -0.40), (0.6, 0, 0), 0.11)
    small_thruster(Kn, (s * -0.11, -0.86, -0.40), (0.6, 0, 0), 0.11)
    # foot: long pointed toes far forward, heel spike, instep plate, sole; nozzle at the heel
    Ft(hyd, cyl(0.16, 0.16, 0.38, (0, 0, 0), 'x', 24, bevel=0.015, bsegs=3))
    Ft(under, box((0.56, 0.28, 0.86), (0, -0.16, 0.06), faces={'+z': dict(scale=(0.85, 0.8)), '-z': dict(scale=(0.75, 0.8))}, bevel=0.03))
    Ft(body, box((0.60, 0.20, 0.82), (0, -0.04, 0.22), rot=(8, 0, 0), faces={'+z': dict(scale=(0.70, 0.35)), '-z': dict(scale=(0.90, 1.0))}, segs=S5, bevel=0.02))
    groove(Ft, (0.02, 0.03, 0.50), (0, 0.06, 0.20), rot=(8, 0, 0))
    for k, (x, L, ry) in enumerate(((-0.21, 0.96, -9), (0.0, 1.10, 0), (0.21, 0.96, 9))):
        Ft(body, box((0.17, 0.19, L), (x, -0.20, 0.34 + L * 0.5), rot=(0, ry, 0), faces={'+z': dict(scale=(0.20, 0.10), shift=(0, -0.07)), '-z': dict(scale=(1.0, 0.9))}, segs=S5, bevel=0.012))
    Ft(body, box((0.24, 0.19, 0.62), (0, -0.20, -0.52), faces={'-z': dict(scale=(0.28, 0.22), shift=(0, -0.03))}, segs=S5, bevel=0.012))   # heel spike
    Ft(under, box((0.50, 0.05, 0.82), (0, -0.285, 0.06), bevel=0.01, segs=1))
    seam(Ft, (0.30, 0.018, 0.04), (0, -0.10, 0.575), rot=(8, 0, 0))
    nozzle(NF[S], 0.18)

# ---------------------------------------------------------------- bucket objects ----------------------------------
NAMES = {('Head', 'mech_eyes'): 'Eyes'}
objects = BK.to_objects(NAMES)

# ---------------------------------------------------------------- hydraulic pistons (aimed per frame by mech.js) ----
HYD = []
for nm in ('WaistL', 'WaistR', 'ElbowL', 'ElbowR', 'KneeL', 'KneeR', 'AnkleL', 'AnkleR'):
    R = 0.05 if nm.startswith('Waist') else 0.06 if nm.startswith('Elbow') else 0.08 if nm.startswith('Knee') else 0.05
    a = bpy.data.objects['HydA_' + nm]; b = bpy.data.objects['HydB_' + nm]
    def unit_cyl(name, r, mat, segs):   # along game +Z from 0 to 1 (Blender −Y), parented to the root
        bm = cyl(r, r, 1.0, (0, 0, 0.5), 'z', segs, bevel=0.0)
        for v in bm.verts: v.co = B(*v.co)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
        ob = bpy.data.objects.new(name, me); link(ob); ob.parent = root; ob['name'] = name; return ob
    bodyo = unit_cyl(f'Hyd_{nm}_body', R, hyd, 14); rodo = unit_cyl(f'Hyd_{nm}_rod', R * 0.5, edge, 10)
    HYD.append((bodyo, rodo, a, b)); objects += [bodyo, rodo]

# ---------------------------------------------------------------- finish: modifiers, counts, checks, export --------
apply_modifiers(objects)
bpy.context.view_layer.update()
tris = {o.name: tri_count(o) for o in objects}
total = sum(tris.values())
log('objects', len(objects), 'triangles', total)
for n, t in sorted(tris.items(), key=lambda kv: -kv[1])[:12]: log(f'  {n:28s} {t:6d}')
glow_parts = sum(1 for o in objects if o.data.materials and o.data.materials[0].name == 'mech_glow')
assert 40000 <= total <= 80000, 'triangle band: %d' % total

PFLICHT = ['Mech', 'Pelvis', 'Torso', 'Head', 'Backpack', 'Hatch', 'Cockpit', 'LaserMuzzle', 'Pod_L', 'Pod_R', 'Nozzle_Back_L', 'Nozzle_Back_R',
           'Shoulder_L', 'Shoulder_R', 'UpperArm_L', 'UpperArm_R', 'Forearm_L', 'Forearm_R', 'Hip_L', 'Hip_R', 'Knee_L', 'Knee_R', 'Foot_L', 'Foot_R',
           'Nozzle_Foot_L', 'Nozzle_Foot_R', 'Eyes'] + [f'Tube_{S}_{i}' for S in 'LR' for i in range(6)]
missing = [n for n in PFLICHT if n not in bpy.data.objects]
assert not missing, 'contract names missing: ' + ', '.join(missing)
for n in PFLICHT: assert bpy.data.objects[n].get('name') == n, n

REST = {'Hip_L': (-0.34, 0, 0), 'Hip_R': (-0.34, 0, 0), 'Knee_L': (0.72, 0, 0), 'Knee_R': (0.72, 0, 0), 'Foot_L': (-0.38, 0, 0), 'Foot_R': (-0.38, 0, 0),
        'UpperArm_L': (0, 0, 0.12), 'UpperArm_R': (0, 0, -0.12), 'Forearm_L': (-0.35, 0, 0), 'Forearm_R': (-0.35, 0, 0)}
def extents(skip=(), skip_prefix=()):
    dg = bpy.context.evaluated_depsgraph_get(); lo = [1e9] * 3; hi = [-1e9] * 3
    for o in objects:
        if o.type != 'MESH' or o.name in skip or o.name.startswith(skip_prefix): continue
        me = o.evaluated_get(dg).data; M = o.matrix_world
        for v in me.vertices:
            g = G(M @ v.co)
            for i in range(3): lo[i] = min(lo[i], g[i]); hi[i] = max(hi[i], g[i])
    return lo, hi
set_pose(P, REST, PELVIS_Y); aim_hydraulics(HYD); lo, hi = extents()
log('game-pose extents  x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f' % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
sym = abs(abs(lo[0]) - abs(hi[0]))
log('symmetry |min x| vs max x: %.3f m · glow parts %d' % (sym, glow_parts))
assert hi[1] <= 6.80 + 1e-3, 'too tall: %.3f' % hi[1]        # Schulterplatten stehen ueber dem Helm
klo, khi = extents(skip_prefix=('Wing',))            # Kernkoerper ohne den Ruecken-Faecher: der darf ausladen
log('Faecher-Spannweite %.2f m · Kernbreite %.2f m' % (max(-lo[0], hi[0]) * 2, max(-klo[0], khi[0]) * 2))
assert max(-klo[0], khi[0]) <= 2.70 + 1e-3, 'too wide (Kern): %.3f' % max(-klo[0], khi[0])
assert sym <= 0.02, 'arms asymmetric by %.3f m' % sym
set_pose(P, {}, PELVIS_Y); aim_hydraulics(HYD)
export_glb(OUT_GLB, root, draco=True)
export_glb(OUT_GLB.replace('.glb', '-raw.glb'), root, draco=False)

set_pose(P, REST, PELVIS_Y); aim_hydraulics(HYD)
json.dump({'round': 4, 'triangles': total, 'objects': len(objects), 'per_object': tris, 'extents_game_pose': {'min': lo, 'max': hi}, 'symmetry_x': sym, 'pelvis_y': PELVIS_Y,
           'glow_parts': glow_parts, 'leg_yaw_deg': LEG_YAW, 'hyd': [(b.name, r.name, a.name, bb.name) for b, r, a, bb in HYD], 'rest': REST}, open(OUT_REPORT, 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
log('saved', OUT_BLEND)
