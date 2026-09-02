# render_mech.py — the inspection renders of mech.blend on brain: Cycles + OptiX on both RTX 5060 Ti, 128 samples, OptiX
# denoise. Six views in the game's landed pose, a thumbnail candidate in a hero pose with a rim light from behind, and a
# pure black-on-white silhouette (Workbench, flat). Output: renders/<name>.png
#   ~/bin/blender -b -P render_mech.py -- [only=name,name] [samples=128]
import bpy, math, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from mechlib import B, G, log, set_pose, aim_hydraulics, hex_lin
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
opts = dict(a.split('=', 1) for a in argv if '=' in a)
ONLY = set(opts.get('only', '').split(',')) - {''}
SAMPLES = int(opts.get('samples', 128))
OUT = os.path.join(HERE, 'renders'); os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'mech.blend'))
sc = bpy.context.scene
rep = json.load(open(os.path.join(HERE, 'mech-report.json')))
O = bpy.data.objects
P = {o.name: o for o in O if o.type == 'EMPTY' and not o.name.startswith(('HydA_', 'HydB_', 'Tube_'))}
HYD = [(O[b], O[r], O[a], O[bb]) for b, r, a, bb in rep['hyd']]
REST = {k: tuple(v) for k, v in rep['rest'].items()}
PELVIS_Y = rep['pelvis_y']

# ---------------------------------------------------------------- GPU / Cycles ----------------------------------------
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'; prefs.refresh_devices()
used = []
for d in prefs.devices:
    d.use = (d.type == 'OPTIX')
    if d.use: used.append(d.name)
log('devices', used)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'GPU'; sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPTIX'; sc.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.02
sc.cycles.max_bounces = 8; sc.cycles.glossy_bounces = 6; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.resolution_x = 1280; sc.render.resolution_y = 720; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.film_transparent = False
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Base Contrast'; sc.view_settings.exposure = 0.35

# ---------------------------------------------------------------- world, floor, lights ---------------------------------
world = bpy.data.worlds.new('W'); world.use_nodes = True; sc.world = world
nt = world.node_tree; bg = nt.nodes['Background']
tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); ramp = nt.nodes.new('ShaderNodeValToRGB'); mapr = nt.nodes.new('ShaderNodeMapRange')
nt.links.new(tc.outputs['Generated'], sep.inputs['Vector']); nt.links.new(sep.outputs['Z'], mapr.inputs['Value']); nt.links.new(mapr.outputs['Result'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
mapr.inputs['From Min'].default_value = 0.3; mapr.inputs['From Max'].default_value = 0.9
def set_world(bottom, top, strength):
    ramp.color_ramp.elements[0].color = (*bottom, 1); ramp.color_ramp.elements[1].color = (*top, 1); bg.inputs['Strength'].default_value = strength

floor_mat = bpy.data.materials.new('floor'); floor_mat.use_nodes = True
fb = floor_mat.node_tree.nodes['Principled BSDF']
fb.inputs['Base Color'].default_value = (0.012, 0.013, 0.016, 1); fb.inputs['Roughness'].default_value = 0.22; fb.inputs['Metallic'].default_value = 0.0
fb.inputs['Specular IOR Level'].default_value = 0.6
fm = bpy.data.meshes.new('floor'); fm.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)]); fm.update()
floor = bpy.data.objects.new('Floor', fm); sc.collection.objects.link(floor); floor.data.materials.append(floor_mat)

def aim(ob, pos, target):
    ob.location = B(*pos); d = B(*target) - B(*pos)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def area(name, pos, target, power, size, color=(1, 1, 1), spread=180):
    L = bpy.data.lights.new(name, 'AREA'); L.energy = power; L.size = size; L.color = color; L.shape = 'SQUARE'; L.spread = math.radians(spread)
    ob = bpy.data.objects.new(name, L); sc.collection.objects.link(ob); aim(ob, pos, target); return ob

cam_data = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cam_data); sc.collection.objects.link(cam); sc.camera = cam
cam_data.sensor_width = 36; cam_data.clip_end = 500

HERO = {'Torso': (0.04, 0.45, 0.0), 'Head': (-0.10, 0.25, 0.0), 'Pelvis': (0.10, 0.0, -0.03),
        'Hip_L': (-1.0, 0, 0.04), 'Knee_L': (1.35, 0, 0), 'Foot_L': (-0.35, 0, 0),
        'Hip_R': (-0.05, 0, -0.02), 'Knee_R': (0.70, 0, 0), 'Foot_R': (-0.65, 0, 0),
        'UpperArm_R': (-1.0, 0, -0.20), 'Forearm_R': (0.72, 0, 0),
        'UpperArm_L': (0.50, 0, 0.50), 'Forearm_L': (-1.30, 0, 0),
        'Shoulder_L': (0.05, 0, 0.06), 'Shoulder_R': (-0.05, 0, -0.04)}

# views: name, camera position, target (game coords), lens mm, pose, light rig
VIEWS = [
    ('01_front',        (0.0, 3.0, 16.5),  (0.0, 3.0, 0.0), 45, 'rest', 'studio'),
    ('02_front34',      (7.4, 4.4, 13.6),  (0.0, 3.0, 0.0), 45, 'rest', 'studio'),
    ('03_seite',        (16.2, 3.0, 0.5),  (0.0, 3.0, 0.0), 45, 'rest', 'studio'),
    ('04_ruecken34',    (-9.6, 4.2, -12.6), (0.0, 3.05, 0.0), 45, 'rest', 'studio'),
    ('05_detail_brust', (1.7, 4.7, 4.3),   (0.0, 4.15, 0.6), 60, 'rest', 'studio'),
    ('06_detail_fuss',  (2.7, 1.05, 3.3),  (0.62, 0.42, 0.45), 55, 'rest', 'studio'),
    ('07_thumbnail',    (6.2, 4.9, 9.6),   (0.0, 3.0, 0.0), 35, 'hero', 'hero'),   # from above the shoulder line: the wings show their top faces
    ('08_silhouette',   (7.4, 4.4, 13.6),  (0.0, 3.0, 0.0), 45, 'rest', 'silhouette'),
    ('09_top',          (0.0, 16.0, 0.01), (0.0, 3.0, 0.0), 40, 'rest', 'studio'),     # diagnostics: plan view
    ('10_wing',         (3.5, 5.8, 9.0),   (1.2, 5.4, -1.0), 50, 'rest', 'studio'),   # diagnostics: level with the wing
]

lights = []
def clear_lights():
    global lights
    for l in lights: bpy.data.objects.remove(l, do_unlink=True)
    lights = []

def rig(kind):
    clear_lights()
    if kind == 'studio':
        set_world((0.035, 0.040, 0.055), (0.42, 0.47, 0.58), 1.0)   # lighter world: the metallic lack mirrors it, that is where the anthracite tone comes from
        lights.append(area('Key', (7.0, 9.5, 7.5), (0, 3.2, 0), 1500, 6.0, (1.0, 0.96, 0.90)))
        lights.append(area('FillFront', (-7.5, 4.5, 9.5), (0, 3.2, 0), 380, 6.0, (0.85, 0.9, 1.0)))   # second light from front-side, ~25 % of the key
        lights.append(area('Rim', (-6.5, 7.5, -8.5), (0, 3.4, 0), 2800, 4.0, (0.72, 0.84, 1.0)))
        lights.append(area('Fill', (-8.0, 3.0, 6.0), (0, 3.0, 0), 300, 5.0, (0.85, 0.9, 1.0)))
        lights.append(area('Top', (0.0, 11.0, 1.0), (0, 3.0, 0), 600, 6.0, (0.9, 0.93, 1.0)))
    elif kind == 'hero':
        set_world((0.012, 0.014, 0.022), (0.22, 0.26, 0.34), 1.0)
        lights.append(area('Rim', (-6.0, 8.0, -7.0), (0, 3.6, 0), 9000, 3.0, (0.82, 0.9, 1.0)))
        lights.append(area('Rim2', (7.0, 6.5, -7.5), (0, 3.4, 0), 5000, 2.5, (1.0, 0.62, 0.30)))
        lights.append(area('Key', (8.0, 6.0, 9.0), (0, 3.2, 0), 1500, 5.0, (0.80, 0.86, 1.0)))
        lights.append(area('FillFront', (-7.5, 4.5, 9.5), (0, 3.2, 0), 420, 6.0, (0.7, 0.8, 1.0)))
        lights.append(area('Fill', (-9.0, 3.0, 7.0), (0, 3.0, 0), 300, 5.0, (0.6, 0.72, 1.0)))
        lights.append(area('Ground', (2.5, 0.3, 5.5), (0, 2.0, 0), 260, 3.0, (1.0, 0.55, 0.25)))

for name, pos, target, lens, pose, kind in VIEWS:
    if ONLY and name not in ONLY: continue
    set_pose(P, HERO if pose == 'hero' else REST, 2.72 if pose == 'hero' else PELVIS_Y); aim_hydraulics(HYD)
    aim(cam, pos, target); cam_data.lens = lens
    sc.render.filepath = os.path.join(OUT, name + '.png')
    if kind == 'silhouette':
        sc.render.engine = 'BLENDER_WORKBENCH'; floor.hide_render = True; clear_lights()
        sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'SINGLE'; sh.single_color = (0, 0, 0)
        sh.background_type = 'VIEWPORT'; sh.background_color = (1, 1, 1); sh.show_shadows = False; sh.show_cavity = False
        sc.display.render_aa = '8'; sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
        world.color = (1, 1, 1); set_world((1, 1, 1), (1, 1, 1), 1.0)
    else:
        sc.render.engine = 'CYCLES'; floor.hide_render = False; rig(kind)
    log('render', name, 'pose', pose, 'rig', kind)
    bpy.ops.render.render(write_still=True)
    log('wrote', sc.render.filepath)
log('done')
