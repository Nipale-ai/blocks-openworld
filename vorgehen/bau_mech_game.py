# bau_mech_game.py — Spiel-Ableitung aus mech-hero.blend: Decimate auf ≤80k Dreiecke,
# Flat-Materialien (glTF kann die prozeduralen Knoten nicht tragen), Draco-Export.
#   ~/bin/blender -b -P bau_mech_game.py            (auf brain, nach MECH_HERO=1 bau_mech.py)
# Rig-Vertrag bleibt: Pivots sind Empties, Meshes bleiben pro (Pivot, Material) getrennt.
import bpy, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mechlib import log, hex_lin, export_glb

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'mech-hero.blend'))

# Hero-only-Elemente entfernen (Klinge — der Spiel-Code kennt sie nicht)
for ob in [o for o in bpy.data.objects if o.name.startswith('Blade_')]:
    bpy.data.objects.remove(ob, do_unlink=True)
log('removed hero-only blade objects')

# ---------------------------------------------------------------- 1) Flat-Materialien (Namen bleiben) ----------------
FLAT = {
    'mech_body': ('#1a1d22', 0.18, 0.85), 'mech_plate': ('#252a31', 0.30, 0.75),
    'mech_under': ('#05060a', 0.90, 0.30), 'mech_hyd': ('#9aa4b0', 0.22, 0.95),
    'mech_accent': ('#ff7a1a', 0.35, 0.40), 'mech_glow': ('#1a0c04', 0.40, 0.20),
    'mech_eyes': ('#1a0c04', 0.30, 0.20), 'mech_edge': ('#e8f0ff', 0.15, 0.90),
    'mech_glass': ('#0a1418', 0.08, 0.60),
}
for name, (col, rough, metal) in FLAT.items():
    m = bpy.data.materials.get(name)
    if not m:
        continue
    nt = m.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    if not bsdf:
        continue
    for inp in ('Roughness', 'Base Color', 'Metallic'):
        for l in list(bsdf.inputs[inp].links):
            nt.links.remove(l)
    bsdf.inputs['Base Color'].default_value = (*hex_lin(col), 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal

# ---------------------------------------------------------------- 2) Decimate (große Objekte, kleine bleiben) --------
def tri_count(ob):
    if ob.type != 'MESH':
        return 0
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).data
    return sum(len(p.vertices) - 2 for p in me.polygons)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
before = sum(tri_count(o) for o in meshes)
log('before', before, 'tris,', len(meshes), 'meshes')

# Ziel: ≤80k. Große Objekte (Detailträger) werden reduziert, kleine Detailteile (Bolzen, Fugen)
# bleiben unangetastet — sonst verschwindet genau der Detailgewinn.
TARGET = 75000
big = [o for o in meshes if tri_count(o) > 900]
small_tris = sum(tri_count(o) for o in meshes if tri_count(o) <= 900)
big_tris = before - small_tris
ratio = min(1.0, (TARGET - small_tris) / max(big_tris, 1))
log('big', len(big), 'objects', big_tris, 'tris -> ratio', round(ratio, 3), '| small', small_tris, 'tris kept')

for ob in big:
    mod = ob.modifiers.new('dec', 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.modifier_apply(modifier=mod.name)

after = sum(tri_count(o) for o in meshes)
log('after', after, 'tris')
assert after <= 80000, 'game band: %d' % after

# ---------------------------------------------------------------- 3) Export + Report --------------------------------
root = bpy.data.objects.get('Mech')
assert root is not None, 'Mech root missing'
OUT_GLB = os.path.join(HERE, 'mech-game.glb')
export_glb(OUT_GLB, root, draco=True)

PFLICHT = ['Mech', 'Pelvis', 'Torso', 'Head', 'Backpack', 'Hatch', 'Cockpit', 'LaserMuzzle', 'Pod_L', 'Pod_R',
           'Nozzle_Back_L', 'Nozzle_Back_R', 'Shoulder_L', 'Shoulder_R', 'UpperArm_L', 'UpperArm_R',
           'Forearm_L', 'Forearm_R', 'Hip_L', 'Hip_R', 'Knee_L', 'Knee_R', 'Foot_L', 'Foot_R',
           'Nozzle_Foot_L', 'Nozzle_Foot_R', 'Eyes'] + [f'Tube_{S}_{i}' for S in 'LR' for i in range(6)]
missing = [n for n in PFLICHT if n not in bpy.data.objects]
assert not missing, 'contract names missing: ' + ', '.join(missing)
hero_rep = json.load(open(os.path.join(HERE, 'mech-hero-report.json')))
json.dump({'triangles': after, 'objects': len(meshes), 'ratio': ratio, 'contract_ok': True,
           'pelvis_y': hero_rep['pelvis_y'], 'hyd': hero_rep['hyd'], 'rest': hero_rep['rest'],
           'extents_game_pose': hero_rep['extents_game_pose'], 'symmetry_x': hero_rep['symmetry_x']},
          open(os.path.join(HERE, 'mech-game-report.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'mech-game.blend'))
log('game export ok', OUT_GLB, after, 'tris')
