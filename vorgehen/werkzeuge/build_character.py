# build_character.py — skinned biped for player / civilians / officers (contract: NOTES.md 5.1).
#   blender -b -P build_character.py -- player officer civ0 civ1 civ2 civ3
# 16 bones with the contract names and rest positions, all joints exported with IDENTITY rotation (Blender bones point
# +Z with roll 0; the exporter's Y-up conversion makes them identity in glTF, translations = game-frame offsets).
# Mesh = lofted tubes (torso, neck, head, arms, legs, hands, shoes) with per-ring skin weights blended at the joints,
# one 1024² texture set painted per palette (face, hair, shirt, trousers, shoes; officer: uniform, badge, tie, stripe)
# plus geometry for ears, nose, hair cap, and for officers a peaked cap, duty belt with buckle, holster and pouches.
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

BONES = [('Hips', None, (0, 0.95, 0)), ('Spine', 'Hips', (0, 1.10, 0)), ('Chest', 'Spine', (0, 1.30, 0)), ('Head', 'Chest', (0, 1.52, 0)),
         ('UpperArm_L', 'Chest', (0.22, 1.45, 0)), ('Forearm_L', 'UpperArm_L', (0.24, 1.17, 0)), ('Hand_L', 'Forearm_L', (0.24, 0.92, 0)),
         ('UpperArm_R', 'Chest', (-0.22, 1.45, 0)), ('Forearm_R', 'UpperArm_R', (-0.24, 1.17, 0)), ('Hand_R', 'Forearm_R', (-0.24, 0.92, 0)),
         ('Thigh_L', 'Hips', (0.11, 0.95, 0)), ('Shin_L', 'Thigh_L', (0.11, 0.50, 0)), ('Foot_L', 'Shin_L', (0.11, 0.08, 0)),
         ('Thigh_R', 'Hips', (-0.11, 0.95, 0)), ('Shin_R', 'Thigh_R', (-0.11, 0.50, 0)), ('Foot_R', 'Shin_R', (-0.11, 0.08, 0))]

PALETTES = {
    'player': dict(skin='#e9bd93', hair='#2a1d14', shirt='#e0632d', pants='#2c3340', shoes='#1c1a19', sleeves='short', cop=False),
    'officer': dict(skin='#d9a982', hair='#0d1426', shirt='#1d2c52', pants='#161a24', shoes='#0f0f10', sleeves='long', cop=True),
    'civ0': dict(skin='#f1c9a5', hair='#5a3a22', shirt='#3c6db8', pants='#4a4a4a', shoes='#4d3a2a', sleeves='short', cop=False),
    'civ1': dict(skin='#b8825a', hair='#1a1a1a', shirt='#f0f0f0', pants='#233a5e', shoes='#e8e8e8', sleeves='long', cop=False),
    'civ2': dict(skin='#8c5a3c', hair='#1a1a1a', shirt='#d9b545', pants='#6d5b45', shoes='#1c1a19', sleeves='short', cop=False),
    'civ3': dict(skin='#f5d6b8', hair='#c8a060', shirt='#8d5cc0', pants='#3d2b1f', shoes='#4d3a2a', sleeves='long', cop=False),
    'civ4': dict(skin='#d9a982', hair='#8b8b8b', shirt='#3fa06a', pants='#7d7d7d', shoes='#1c1a19', sleeves='short', cop=False),
    'civ5': dict(skin='#f1c9a5', hair='#2a1d14', shirt='#333842', pants='#2c3340', shoes='#1c1a19', sleeves='long', cop=False),
}

# atlas regions (u0, v0, u1, v1)
REG = {'head': (0.0, 0.70, 0.5, 1.0), 'torso': (0.5, 0.55, 1.0, 1.0), 'arm_L': (0.0, 0.40, 0.25, 0.70), 'arm_R': (0.25, 0.40, 0.5, 0.70),
       'leg_L': (0.5, 0.15, 0.75, 0.55), 'leg_R': (0.75, 0.15, 1.0, 0.55), 'hand': (0.0, 0.28, 0.25, 0.40), 'foot': (0.25, 0.28, 0.5, 0.40),
       'hair': (0.0, 0.15, 0.25, 0.28), 'cap': (0.25, 0.15, 0.5, 0.28), 'belt': (0.0, 0.0, 0.5, 0.15), 'skin': (0.5, 0.0, 0.75, 0.15), 'metal': (0.75, 0.0, 1.0, 0.15)}


class Loft:
    """collects rings; each ring = list of game-space points (same count), a v value, and bone weights [(bone, w)]."""
    def __init__(self):
        self.verts = []; self.faces = []; self.uvs = []; self.weights = []; self.rings = []
    def ring(self, pts, v, w, region, u_fn=None):
        base = len(self.verts); n = len(pts)
        for i, p in enumerate(pts):
            self.verts.append(p); self.weights.append(w)
        self.rings.append((base, n, v, region, u_fn)); return len(self.rings) - 1
    def bridge(self, r0, r1):
        b0, n, v0, reg, uf0 = self.rings[r0]; b1, n1, v1, _, uf1 = self.rings[r1]; assert n == n1
        u0r, v0r, u1r, v1r = REG[reg]; m = 0.015 * (v1r - v0r); v0r, v1r = v0r + m, v1r - m
        for i in range(n):
            j = (i + 1) % n
            self.faces.append((b0 + i, b0 + j, b1 + j, b1 + i))
            ua, ub = i / n, (i + 1) / n
            self.uvs.append([(u0r + ua * (u1r - u0r), v0r + v0 * (v1r - v0r)), (u0r + ub * (u1r - u0r), v0r + v0 * (v1r - v0r)),
                             (u0r + ub * (u1r - u0r), v0r + v1 * (v1r - v0r)), (u0r + ua * (u1r - u0r), v0r + v1 * (v1r - v0r))])
    def pole(self, r, point, w, region, v, top=True):
        b, n, vr, reg, _ = self.rings[r]; pi = len(self.verts); self.verts.append(point); self.weights.append(w)
        u0r, v0r, u1r, v1r = REG[region]; m = 0.015 * (v1r - v0r); v0r, v1r = v0r + m, v1r - m
        for i in range(n):
            j = (i + 1) % n
            self.faces.append((b + i, b + j, pi) if top else (b + j, b + i, pi))
            self.uvs.append([(u0r + i / n * (u1r - u0r), v0r + vr * (v1r - v0r)), (u0r + (i + 1) / n * (u1r - u0r), v0r + vr * (v1r - v0r)), (u0r + (i + 0.5) / n * (u1r - u0r), v0r + v * (v1r - v0r))]
                            if top else [(u0r + (i + 1) / n * (u1r - u0r), v0r + vr * (v1r - v0r)), (u0r + i / n * (u1r - u0r), v0r + vr * (v1r - v0r)), (u0r + (i + 0.5) / n * (u1r - u0r), v0r + v * (v1r - v0r))])
    def chain(self, ring_ids):
        for a, b in zip(ring_ids, ring_ids[1:]): self.bridge(a, b)


def ellipse(cx, cy, cz, rx, rz, n=14, start=0.5, flat_back=0.0):
    """horizontal ring around (cx, cy, cz); u runs from the back (seam) over the character's left to the front."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * (i / n + start)  # start 0.5 -> first point at the back (-z)
        x = cx + rx * math.sin(a); z = cz + rz * math.cos(a)
        if flat_back and z < cz: z = cz + (z - cz) * (1 - flat_back)
        pts.append((x, cy, z))
    return pts


def limb(loft, region, joints, radii, bones, n=12, sub=3, rx_scale=1.0, rz_scale=1.0, v_range=(0.0, 1.0)):
    """tube through joint points (top -> bottom). radii per joint. bones per segment; weights blend at joints."""
    rings = []; total = sum(math.dist(joints[i], joints[i + 1]) for i in range(len(joints) - 1)); acc = 0.0
    for s in range(len(joints) - 1):
        p0, p1 = joints[s], joints[s + 1]; r0, r1 = radii[s], radii[s + 1]; seg = math.dist(p0, p1)
        ts = [k / sub for k in range(sub + (1 if s == len(joints) - 2 else 0))]
        for t in ts:
            p = tuple(p0[i] + (p1[i] - p0[i]) * t for i in range(3)); r = r0 + (r1 - r0) * t
            v = v_range[0] + (v_range[1] - v_range[0]) * (1 - (acc + seg * t) / total)
            # weights: blend toward the next bone near the lower joint, toward the previous near the upper joint
            wb = bones[s]
            if t >= 0.999 and s + 1 < len(bones): w = [(wb, 0.5), (bones[s + 1], 0.5)]
            elif t > 0.66 and s + 1 < len(bones): w = [(wb, 0.85), (bones[s + 1], 0.15)]
            elif t < 0.34 and t > 0.001 and s > 0: w = [(wb, 0.85), (bones[s - 1], 0.15)]
            else: w = [(wb, 1.0)]
            rings.append(loft.ring(ellipse(p[0], p[1], p[2], r * rx_scale, r * rz_scale, n), v, w, region))
        acc += seg
    loft.chain(rings); return rings


def build_body(pal):
    L = Loft(); cop = pal['cop']
    # ---- torso: hips -> shoulders (horizontal rings), bones Hips / Spine / Chest
    torso = [((0, 0.84, 0), 0.165, 0.105, [('Hips', 1)]), ((0, 0.90, 0), 0.170, 0.110, [('Hips', 1)]), ((0, 0.98, 0), 0.160, 0.105, [('Hips', 0.8), ('Spine', 0.2)]),
             ((0, 1.06, 0), 0.150, 0.100, [('Hips', 0.4), ('Spine', 0.6)]), ((0, 1.14, 0), 0.155, 0.102, [('Spine', 1)]), ((0, 1.22, 0), 0.170, 0.108, [('Spine', 0.7), ('Chest', 0.3)]),
             ((0, 1.30, 0), 0.185, 0.115, [('Spine', 0.4), ('Chest', 0.6)]), ((0, 1.38, 0), 0.200, 0.120, [('Chest', 1)]), ((0, 1.44, 0), 0.215, 0.115, [('Chest', 1)]),
             ((0, 1.49, 0), 0.190, 0.100, [('Chest', 1)]), ((0, 1.52, 0), 0.075, 0.065, [('Chest', 0.6), ('Head', 0.4)])]
    rings = []
    for (c, rx, rz, w) in torso:
        v = (c[1] - 0.84) / (1.52 - 0.84)
        rings.append(L.ring(ellipse(c[0], c[1], c[2], rx, rz, 20, flat_back=0.15), v * 0.92, w, 'torso'))
    L.chain(rings); L.pole(rings[0], (0, 0.82, 0), [('Hips', 1)], 'torso', 0.0, top=False)
    # ---- neck + head (rings), bone Head (neck base shared with Chest)
    head = [((0, 1.52, 0), 0.060, 0.058, [('Chest', 0.5), ('Head', 0.5)]), ((0, 1.56, 0), 0.060, 0.060, [('Head', 1)]), ((0, 1.585, 0.005), 0.078, 0.088, [('Head', 1)]),
            ((0, 1.62, 0.008), 0.092, 0.104, [('Head', 1)]), ((0, 1.66, 0.006), 0.100, 0.110, [('Head', 1)]), ((0, 1.70, 0.004), 0.100, 0.112, [('Head', 1)]),
            ((0, 1.74, 0.0), 0.096, 0.106, [('Head', 1)]), ((0, 1.77, -0.004), 0.080, 0.088, [('Head', 1)]), ((0, 1.79, -0.008), 0.050, 0.055, [('Head', 1)])]
    rings = []
    for (c, rx, rz, w) in head:
        v = (c[1] - 1.52) / (1.80 - 1.52)
        rings.append(L.ring(ellipse(c[0], c[1], c[2], rx, rz, 20, flat_back=0.1), v, w, 'head'))
    L.chain(rings); L.pole(rings[-1], (0, 1.80, -0.01), [('Head', 1)], 'head', 1.0, top=True)
    # ---- arms (hang straight down): shoulder -> elbow -> wrist, then hand
    for sx, side in ((1, 'L'), (-1, 'R')):
        # Mehr Stuetzstellen statt drei: Deltoid, Bizeps, Ellbogen, Unterarmbauch,
        # Handgelenk. Ein linear fallender Radius ueber drei Gelenke ergibt einen
        # Kegel — genau das sah wie ein Rohr aus.
        # Der erste Ring muss INNERHALB der Torso-Kontur liegen, sonst steht die
        # Schulter als Klotz ab (Fehler im ersten Versuch: Ring bei y=1.505,
        # x=0.205, r=0.070 reichte bis 0.275 — Torso dort nur 0.168 breit).
        # Jetzt: klein und weit innen starten, Deltoid-Maximum tiefer legen.
        j = [(sx * 0.135, 1.455, 0), (sx * 0.185, 1.425, 0), (sx * 0.215, 1.375, 0),
             (sx * 0.232, 1.30, 0), (sx * 0.24, 1.17, 0), (sx * 0.242, 1.06, 0),
             (sx * 0.24, 0.92, 0)]
        r = [0.052, 0.062, 0.064, 0.056, 0.042, 0.046, 0.032]
        bn = ['UpperArm_' + side, 'UpperArm_' + side, 'UpperArm_' + side,
              'UpperArm_' + side, 'Forearm_' + side, 'Forearm_' + side]
        ar_ = limb(L, 'arm_' + side, j, r, bn, n=14, sub=3, rx_scale=1.0, rz_scale=1.06)
        # Der oberste Ring sitzt jetzt IN der Schulterkontur und wird vom Torso
        # ueberdeckt — kein Deckel mehr, deshalb auch kein sichtbarer Absatz.
        L.pole(ar_[0], (sx * 0.11, 1.465, 0), [('UpperArm_' + side, 1)], 'arm_' + side, 1.0, top=True)
        # hand: palm rings then finger block
        hr = []
        for (y, rx, rz, w) in ((0.92, 0.034, 0.025, [('Forearm_' + side, 0.5), ('Hand_' + side, 0.5)]),
                               (0.895, 0.040, 0.021, [('Hand_' + side, 1)]),
                               (0.855, 0.044, 0.019, [('Hand_' + side, 1)]),
                               (0.825, 0.042, 0.018, [('Hand_' + side, 1)])):
            hr.append(L.ring(ellipse(sx * 0.24, y, 0.005, rx, rz, 12), (y - 0.76) / (0.92 - 0.76), w, 'hand'))
        L.chain(hr)
        # Vier Finger statt eines Stummels. Leicht gekruemmt und unterschiedlich
        # lang — eine Hand mit gleich langen geraden Fingern liest sich als Klotz.
        fw = [('Hand_' + side, 1)]
        for fi, (dx, laenge, dick) in enumerate(((-0.019, 0.072, 0.0092), (-0.006, 0.078, 0.0098),
                                                  (0.007, 0.074, 0.0094), (0.019, 0.063, 0.0084))):
            fr = []
            for t in (0.0, 0.34, 0.68, 1.0):
                px = sx * (0.24 + dx * 1.0)
                py = 0.822 - laenge * t
                pz = 0.006 + 0.012 * t * t          # Finger kruemmen sich leicht nach vorn
                rr = dick * (1.0 - 0.34 * t)
                fr.append(L.ring(ellipse(px, py, pz, rr, rr * 0.86, 6), 0.5, fw, 'hand'))
            L.chain(fr)
            L.pole(fr[-1], (sx * (0.24 + dx), 0.822 - laenge - 0.004, 0.019), fw, 'hand', 0.5, top=False)
        # thumb
        tr = []
        for (t, r) in ((0.0, 0.012), (1.0, 0.009)):
            p = (sx * (0.24 + 0.035 + 0.03 * t), 0.885 - 0.02 * t, 0.012 + 0.03 * t)
            tr.append(L.ring(ellipse(p[0], p[1], p[2], r, r, 8), 0.5, [('Hand_' + side, 1)], 'hand'))
        L.chain(tr); L.pole(tr[-1], (sx * (0.24 + 0.075), 0.86, 0.05), [('Hand_' + side, 1)], 'hand', 0.5, top=False)
    # ---- legs: hip -> knee -> ankle
    for sx, side in ((1, 'L'), (-1, 'R')):
        j = [(sx * 0.11, 0.95, 0), (sx * 0.11, 0.50, 0), (sx * 0.105, 0.10, 0)]
        lr_ = limb(L, 'leg_' + side, j, [0.090, 0.066, 0.050], ['Thigh_' + side, 'Shin_' + side], n=14, sub=4, rx_scale=0.92, rz_scale=1.0)
        L.pole(lr_[0], (sx * 0.11, 0.97, 0), [('Thigh_' + side, 1)], 'leg_' + side, 1.0, top=True)
        # shoe: rings along z (vertical rings), heel to toe
        sr = []
        prof = [(-0.08, 0.045, 0.036, 0.04), (-0.04, 0.052, 0.040, 0.045), (0.02, 0.055, 0.040, 0.045), (0.08, 0.055, 0.036, 0.04), (0.14, 0.048, 0.026, 0.028), (0.18, 0.030, 0.014, 0.015)]
        for k, (z, rx, ry, yc) in enumerate(prof):
            pts = []
            n = 12
            for i in range(n):
                a = 2 * math.pi * i / n
                pts.append((sx * 0.11 + rx * math.cos(a), max(0.004, yc + ry * math.sin(a)), z))
            w = [('Shin_' + side, 0.3), ('Foot_' + side, 0.7)] if k == 0 else [('Foot_' + side, 1)]
            sr.append(L.ring(pts, k / (len(prof) - 1), w, 'foot'))
        L.chain(sr); L.pole(sr[0], (sx * 0.11, 0.04, -0.09), [('Foot_' + side, 1)], 'foot', 0.0, top=False); L.pole(sr[-1], (sx * 0.11, 0.02, 0.19), [('Foot_' + side, 1)], 'foot', 1.0, top=True)
        # ankle connector
        ar = [L.ring(ellipse(sx * 0.105, 0.10, 0, 0.046, 0.05, 14), 0.02, [('Shin_' + side, 0.5), ('Foot_' + side, 0.5)], 'leg_' + side),
              L.ring(ellipse(sx * 0.11, 0.06, 0.0, 0.05, 0.052, 14), 0.0, [('Foot_' + side, 1)], 'leg_' + side)]
        L.chain(ar)
    # ---- ears, nose (skin region), hair cap or police cap, belt
    for sx in (1, -1):
        er = [L.ring(ellipse(sx * 0.098, 1.665, 0.0, 0.004, 0.018, 8), 0.5, [('Head', 1)], 'skin'), L.ring(ellipse(sx * 0.112, 1.665, 0.0, 0.006, 0.014, 8), 0.5, [('Head', 1)], 'skin')]
        L.chain(er); L.pole(er[-1], (sx * 0.118, 1.665, 0.0), [('Head', 1)], 'skin', 0.5, top=True); L.pole(er[0], (sx * 0.094, 1.665, 0.0), [('Head', 1)], 'skin', 0.5, top=False)
    nr = [L.ring([(0.016, 1.655, 0.104), (0.0, 1.640, 0.108), (-0.016, 1.655, 0.104), (0.0, 1.678, 0.106)], 0.5, [('Head', 1)], 'skin')]
    L.pole(nr[0], (0, 1.652, 0.128), [('Head', 1)], 'skin', 0.5, top=True); L.pole(nr[0], (0, 1.66, 0.09), [('Head', 1)], 'skin', 0.5, top=False)
    if not cop:
        hr = []
        hair = [((0, 1.66, -0.01), 0.106, 0.112, 0.35), ((0, 1.71, -0.006), 0.108, 0.118, 0.5), ((0, 1.75, -0.004), 0.104, 0.112, 0.7), ((0, 1.785, -0.008), 0.086, 0.094, 0.85), ((0, 1.805, -0.012), 0.050, 0.055, 0.95)]
        for (c, rx, rz, v) in hair:
            pts = ellipse(c[0], c[1], c[2], rx, rz, 20, flat_back=0.1)
            # front hairline: lift the front points so the forehead stays visible
            pts = [(x, y + (0.045 * max(0.0, z) / rz if v < 0.45 else 0.0), z) for (x, y, z) in pts]
            hr.append(L.ring(pts, v, [('Head', 1)], 'hair'))
        L.chain(hr); L.pole(hr[-1], (0, 1.815, -0.012), [('Head', 1)], 'hair', 1.0, top=True)
    else:
        # peaked cap: crown (rings), band and a flat peak in front
        cr = []
        for (c, rx, rz, v) in (((0, 1.735, -0.01), 0.112, 0.118, 0.0), ((0, 1.755, -0.01), 0.116, 0.122, 0.2), ((0, 1.80, -0.02), 0.118, 0.125, 0.5), ((0, 1.83, -0.03), 0.100, 0.108, 0.8), ((0, 1.845, -0.035), 0.050, 0.055, 0.95)):
            cr.append(L.ring(ellipse(c[0], c[1], c[2], rx, rz, 20), v, [('Head', 1)], 'cap'))
        L.chain(cr); L.pole(cr[-1], (0, 1.85, -0.035), [('Head', 1)], 'cap', 1.0, top=True); L.pole(cr[0], (0, 1.735, -0.01), [('Head', 1)], 'cap', 0.0, top=False)
        pr = [L.ring([(0.09, 1.742, 0.05), (0.0, 1.742, 0.10), (-0.09, 1.742, 0.05), (-0.09, 1.735, 0.05), (0.0, 1.735, 0.10), (0.09, 1.735, 0.05)], 0.1, [('Head', 1)], 'cap'),
              L.ring([(0.10, 1.728, 0.11), (0.0, 1.722, 0.19), (-0.10, 1.728, 0.11), (-0.10, 1.722, 0.11), (0.0, 1.716, 0.19), (0.10, 1.722, 0.11)], 0.1, [('Head', 1)], 'cap')]
        L.chain(pr); L.pole(pr[1], (0, 1.72, 0.20), [('Head', 1)], 'cap', 0.1, top=True)
        # duty belt + buckle + holster + pouches
        br = [L.ring(ellipse(0, 0.955, 0, 0.178, 0.118, 20, flat_back=0.15), 0.2, [('Hips', 1)], 'belt'), L.ring(ellipse(0, 1.0, 0, 0.176, 0.116, 20, flat_back=0.15), 0.8, [('Hips', 1)], 'belt')]
        L.chain(br)
    return L


def add_box_part(L, size, center, w, region, v=0.5):
    """axis-aligned box as 2 rings (bottom/top) + poles (for buckle, holster, pouches, radio)"""
    x, y, z = center; hw, hh, hd = size[0] / 2, size[1] / 2, size[2] / 2
    r0 = L.ring([(x - hw, y - hh, z - hd), (x + hw, y - hh, z - hd), (x + hw, y - hh, z + hd), (x - hw, y - hh, z + hd)], 0.0, w, region)
    r1 = L.ring([(x - hw, y + hh, z - hd), (x + hw, y + hh, z - hd), (x + hw, y + hh, z + hd), (x - hw, y + hh, z + hd)], 1.0, w, region)
    L.bridge(r0, r1); L.pole(r1, (x, y + hh, z), w, region, 1.0, top=True); L.pole(r0, (x, y - hh, z), w, region, 0.0, top=False)


def paint_textures(name, pal):
    N = 1024; alb = canvas(N, N, (0.5, 0.5, 0.5, 1)); o = canvas(N, N, (1, 0.8, 0, 1)); hgt = np.zeros((N, N), np.float32)
    skin, hair, shirt, pants, shoes = (hex_srgb(pal[k]) for k in ('skin', 'hair', 'shirt', 'pants', 'shoes'))
    cop = pal['cop']; cloth = fbm(N, N, 64, 4, 3); folds = fbm(N, N, 128, 3, 9)
    def region(key, col, rough, metal=0.0, texture=None):
        u0, v0, u1, v1 = REG[key]; rect_uv(alb, u0, v0, u1, v1, (*col, 1)); rect_uv(o, u0, v0, u1, v1, (1, rough, metal, 1))
        if texture == 'cloth':
            x0, y0, x1, y1 = int(u0 * N), int(v0 * N), int(u1 * N), int(v1 * N)
            hgt[y0:y1, x0:x1] = folds[y0:y1, x0:x1] * 0.35 + cloth[y0:y1, x0:x1] * 0.08
            alb[y0:y1, x0:x1, :3] *= (0.92 + 0.12 * cloth[y0:y1, x0:x1])[..., None]
    def band(key, v_lo, v_hi, col, rough=None, u_lo=0.0, u_hi=1.0, blend=1.0):
        u0, v0, u1, v1 = REG[key]
        rect_uv(alb, u0 + u_lo * (u1 - u0), v0 + v_lo * (v1 - v0), u0 + u_hi * (u1 - u0), v0 + v_hi * (v1 - v0), (*col, 1), blend)
        if rough is not None: rect_uv(o, u0 + u_lo * (u1 - u0), v0 + v_lo * (v1 - v0), u0 + u_hi * (u1 - u0), v0 + v_hi * (v1 - v0), (1, rough, 0, 1))
    # skin / face
    region('head', skin, 0.55); region('skin', skin, 0.55); region('hand', skin, 0.55)
    dark = tuple(c * 0.55 for c in skin); lip = (min(1, skin[0] * 0.95), skin[1] * 0.62, skin[2] * 0.62)
    for ue in (0.5 - 0.052, 0.5 + 0.052):  # eyes: white, iris, pupil, brow
        band('head', 0.505, 0.535, (0.93, 0.93, 0.92), u_lo=ue - 0.022, u_hi=ue + 0.022)
        band('head', 0.507, 0.533, (0.25, 0.18, 0.10) if pal['hair'] != '#c8a060' else (0.30, 0.45, 0.55), u_lo=ue - 0.010, u_hi=ue + 0.010)
        band('head', 0.512, 0.528, (0.03, 0.03, 0.03), u_lo=ue - 0.005, u_hi=ue + 0.005)
        band('head', 0.560, 0.575, hair if not cop else (0.12, 0.10, 0.08), u_lo=ue - 0.028, u_hi=ue + 0.028)
    band('head', 0.290, 0.305, lip, u_lo=0.5 - 0.034, u_hi=0.5 + 0.034)  # mouth
    band('head', 0.255, 0.29, tuple(c * 0.93 for c in skin), u_lo=0.5 - 0.04, u_hi=0.5 + 0.04, blend=0.5)  # chin shade
    band('head', 0.0, 0.14, tuple(c * 0.9 for c in skin), blend=0.5)  # neck shade
    # hair on the back / sides of the head above the hairline (front stays skin higher up)
    hb = hair if not cop else (0.10, 0.10, 0.12)
    band('head', 0.62, 1.0, hb, 0.7, u_lo=0.0, u_hi=0.30); band('head', 0.62, 1.0, hb, 0.7, u_lo=0.70, u_hi=1.0)
    band('head', 0.72, 1.0, hb, 0.7, u_lo=0.30, u_hi=0.70)
    region('hair', hair if not cop else (0.10, 0.10, 0.12), 0.65)
    x0, y0, x1, y1 = (int(c * N) for c in (REG['hair'][0], REG['hair'][1], REG['hair'][2], REG['hair'][3]))
    strands = np.abs(np.sin(np.arange(x1 - x0)[None, :] * 0.9 + folds[y0:y1, x0:x1] * 8)) * 0.5
    hgt[y0:y1, x0:x1] = strands; alb[y0:y1, x0:x1, :3] *= (0.8 + 0.4 * strands)[..., None]
    # torso: trousers below the belt line (v < 0.21), shirt above
    region('torso', shirt, 0.85, texture='cloth')
    band('torso', 0.0, 0.21, pants, 0.8)
    if cop:
        band('torso', 0.19, 0.245, (0.08, 0.07, 0.06), 0.45)                       # belt
        band('torso', 0.88, 1.0, (0.10, 0.12, 0.18), u_lo=0.44, u_hi=0.56)          # collar / tie top
        band('torso', 0.30, 0.88, (0.09, 0.10, 0.14), u_lo=0.485, u_hi=0.515)       # tie
        band('torso', 0.62, 0.70, (0.85, 0.72, 0.30), 0.3, u_lo=0.555, u_hi=0.59)   # badge (character's left chest)
        band('torso', 0.60, 0.72, tuple(c * 0.85 for c in shirt), u_lo=0.40, u_hi=0.46); band('torso', 0.60, 0.72, tuple(c * 0.85 for c in shirt), u_lo=0.54, u_hi=0.60)  # pocket flaps
        band('torso', 0.72, 0.725, (0.06, 0.07, 0.10), u_lo=0.38, u_hi=0.62)
        band('torso', 0.84, 0.90, (0.20, 0.24, 0.40), u_lo=0.0, u_hi=0.08); band('torso', 0.84, 0.90, (0.20, 0.24, 0.40), u_lo=0.92, u_hi=1.0)  # epaulettes at the seam sides
    else:
        band('torso', 0.90, 0.96, tuple(c * 0.8 for c in shirt), u_lo=0.42, u_hi=0.58)  # neckline
        band('torso', 0.24, 0.26, tuple(c * 0.85 for c in shirt))                       # hem
        if pal['sleeves'] == 'long': band('torso', 0.30, 0.88, tuple(c * 0.9 for c in shirt), u_lo=0.495, u_hi=0.505)  # placket
    # arms: sleeve on top, skin below
    for key in ('arm_L', 'arm_R'):
        region(key, skin, 0.55)
        if pal['sleeves'] == 'long': band(key, 0.10, 1.0, shirt, 0.85); band(key, 0.10, 0.14, tuple(c * 0.8 for c in shirt))
        else: band(key, 0.58, 1.0, shirt, 0.85); band(key, 0.58, 0.62, tuple(c * 0.8 for c in shirt))
        if cop: band(key, 0.80, 0.90, (0.85, 0.72, 0.30), 0.4, u_lo=0.0 if key == 'arm_L' else 0.7, u_hi=0.3 if key == 'arm_L' else 1.0)  # shoulder patch
    # legs
    for key in ('leg_L', 'leg_R'):
        region(key, pants, 0.8, texture='cloth')
        band(key, 0.0, 1.0, tuple(c * 0.85 for c in pants), u_lo=0.24, u_hi=0.26); band(key, 0.0, 1.0, tuple(c * 0.85 for c in pants), u_lo=0.74, u_hi=0.76)
        if cop: band(key, 0.0, 1.0, (0.55, 0.55, 0.62), u_lo=0.245, u_hi=0.275)  # uniform stripe on the outer seam
        band(key, 0.0, 0.05, tuple(c * 0.75 for c in pants))  # hem shadow
    region('foot', shoes, 0.45); band('foot', 0.0, 1.0, (0.12, 0.11, 0.10), 0.7, u_lo=0.0, u_hi=1.0, blend=0.0)
    band('foot', 0.0, 1.0, tuple(c * 0.6 for c in shoes), u_lo=0.0, u_hi=0.03)  # sole edge hint
    region('cap', (0.10, 0.12, 0.18), 0.7); band('cap', 0.0, 0.25, (0.04, 0.04, 0.05), 0.35)
    band('cap', 0.55, 0.75, (0.85, 0.72, 0.30), 0.3, u_lo=0.47, u_hi=0.53)  # cap badge front
    region('belt', (0.08, 0.07, 0.06), 0.45); region('metal', (0.75, 0.72, 0.60), 0.3, 1.0)
    return (save_image('char_%s_albedo' % name, alb), save_image('char_%s_orm' % name, o, True),
            save_image('char_%s_normal' % name, normal_rgba(height_to_normal(hgt, 1.6)), True))


def build(name):
    pal = PALETTES[name]; reset_scene()
    alb, o, nrm = paint_textures(name, pal)
    mat = pbr_material('character_' + name, base=alb, orm_img=o, normal_img=nrm, normal_strength=0.6)
    # ---- armature
    arm_data = bpy.data.armatures.new('CharacterRig'); arm = bpy.data.objects.new('CharacterRig', arm_data); link(arm)
    select_only(arm); bpy.ops.object.mode_set(mode='EDIT')
    ebs = {}
    for bname, parent, pos in BONES:
        eb = arm_data.edit_bones.new(bname); eb.head = B(*pos); eb.tail = eb.head + Vector((0, 0, 0.08)); eb.roll = 0.0; eb.use_connect = False
        if parent: eb.parent = ebs[parent]
        ebs[bname] = eb
    bpy.ops.object.mode_set(mode='OBJECT')
    # ---- mesh
    L = build_body(pal)
    if pal['cop']:
        add_box_part(L, (0.05, 0.05, 0.02), (0, 0.975, 0.125), [('Hips', 1)], 'metal')
        add_box_part(L, (0.045, 0.14, 0.07), (-0.19, 0.90, 0.02), [('Hips', 1)], 'belt')      # holster (right hip)
        add_box_part(L, (0.05, 0.08, 0.04), (0.17, 0.93, 0.08), [('Hips', 1)], 'belt')         # pouch left front
        add_box_part(L, (0.06, 0.07, 0.035), (0.0, 0.93, -0.125), [('Hips', 1)], 'belt')       # pouch back
        add_box_part(L, (0.03, 0.09, 0.03), (0.085, 1.34, 0.115), [('Chest', 1)], 'metal')      # radio on the chest
    ob = object_from_pydata('CharacterMesh', L.verts, L.faces, uvs=L.uvs, mat=mat)
    ob.parent = arm
    groups = {b[0]: ob.vertex_groups.new(name=b[0]) for b in BONES}
    for i, w in enumerate(L.weights):
        tot = sum(x for _, x in w)
        for bname, x in w: groups[bname].add([i], x / tot, 'REPLACE')
    mod = ob.modifiers.new('arm', 'ARMATURE'); mod.object = arm
    shade_smooth(ob, 70)
    # weapon socket: child of Hand_R at (0, -0.08, 0.03) with rotation.x = +90 deg in the game frame
    sock = add_empty('WeaponSocket', (-0.24, 0.84, 0.03), None, rot_deg=(90, 0, 0))
    bpy.context.view_layer.update(); target = sock.matrix_world.copy()
    bone = arm.data.bones['Hand_R']
    sock.parent = arm; sock.parent_type = 'BONE'; sock.parent_bone = 'Hand_R'; sock.matrix_parent_inverse = Matrix.Identity(4)
    bone_space = arm.matrix_world @ bone.matrix_local @ Matrix.Translation((0, bone.length, 0))
    sock.matrix_basis = bone_space.inverted() @ target
    bpy.context.view_layer.update()
    log('socket world', [round(c, 4) for c in G(sock.matrix_world.translation)], 'target', [round(c, 4) for c in G(target.translation)])
    arm['height'] = 1.8
    path = os.path.join(OUT, 'character_%s.glb' % name)
    export_glb(path, [arm]); report([arm], os.path.join(OUT, 'character_%s_report.json' % name))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'character_%s.blend' % name))


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['player']
    for k in args: build(k)
