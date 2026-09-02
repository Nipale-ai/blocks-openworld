# mechlib.py — shared helpers for bau_mech.py / render_mech.py (Blender 4.5, headless on brain).
#
# Coordinate rule (same as ../phase2-assets/common.py): the game / glTF frame is X right(−) / left(+), Y up,
# Z forward. Blender is Z up with the model facing −Y. The glTF exporter (+Y up) maps Blender (x, y, z) →
# glTF (x, z, −y), so a game point (x, y, z) is placed at Blender (x, −z, y) — that is B(). EVERY public helper
# takes GAME coordinates (metres) and game-frame rotations; the conversion happens once, at the very end.
#
# Geometry is built with bmesh in "buckets": one mesh object per (pivot, material), so the draw-call count stays
# near the pivot count (the old procedural mech merged the same way). Parts are: tapered / sheared boxes with a
# hard bevel (the armour plates), capped cylinders (joints, pistons, barrels), lathes (nozzle bells) and thin
# strips (emissive seam lights, edge lights). Sharp edges are marked by angle and a Weighted-Normal modifier keeps
# the big faces flat while the bevel strips shade smoothly — the hard-surface look without a subdivision surface.
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix, Euler

C_G2B = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))  # game (x, y, z) → blender (x, −z, y)


def B(x, y, z):
    return Vector((x, -z, y))


def G(v):
    return (v.x, v.z, -v.y)


def log(*a):
    print('[mech]', *a); sys.stdout.flush()


def rad(deg):
    return deg * math.pi / 180.0


def game_rot(rx, ry, rz):
    """three.js Euler 'XYZ' (R = Rx·Ry·Rz, radians, game axes) → 3×3 rotation in the Blender frame."""
    Rg = Matrix.Rotation(rx, 3, 'X') @ Matrix.Rotation(ry, 3, 'Y') @ Matrix.Rotation(rz, 3, 'Z')
    return C_G2B @ Rg @ C_G2B.transposed()


def game_rot_game(rx, ry, rz):
    """the same rotation but expressed in the game frame (for transforming game-coordinate vertices)."""
    return Matrix.Rotation(rx, 3, 'X') @ Matrix.Rotation(ry, 3, 'Y') @ Matrix.Rotation(rz, 3, 'Z')


# ---------------------------------------------------------------- colour / materials -------------------------------
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_lin(h):
    h = h.lstrip('#'); return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))


def make_material(name, color, rough, metal, emit=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*hex_lin(color), 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if emit:
        bsdf.inputs['Emission Color'].default_value = (*hex_lin(emit), 1.0)
        bsdf.inputs['Emission Strength'].default_value = strength
    return m


# ---------------------------------------------------------------- scene / objects ----------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 1.0
    return sc


def link(ob):
    bpy.context.scene.collection.objects.link(ob); return ob


def empty(name, pos, parent=None, rot=(0, 0, 0), size=0.15):
    """pivot at a GAME position (parent-local); rot = game-frame three.js XYZ Euler in radians."""
    e = bpy.data.objects.new(name, None); e.empty_display_size = size; e.empty_display_type = 'PLAIN_AXES'
    link(e)
    if parent is not None: e.parent = parent
    e.location = B(*pos)
    e.rotation_euler = game_rot(*rot).to_euler('XYZ')
    e['name'] = name  # → extras.name; loader.js fixNames() restores contract names from it
    return e


def select_only(obs):
    for o in bpy.context.view_layer.objects: o.select_set(False)
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0] if obs else None


# ---------------------------------------------------------------- part builders (game coords) ----------------------
def _finish_part(bm, pos, rot_deg, mirror=False):
    """rotate (game Euler in degrees, or a ready 3×3 game-frame Matrix) + translate a part built around the origin."""
    R = rot_deg.to_4x4() if isinstance(rot_deg, Matrix) else game_rot_game(rad(rot_deg[0]), rad(rot_deg[1]), rad(rot_deg[2])).to_4x4()
    T = Matrix.Translation(Vector(pos))
    bmesh.ops.transform(bm, matrix=T @ R, verts=bm.verts)
    if mirror:
        for v in bm.verts: v.co.x = -v.co.x
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    return bm


def _bevel_all(bm, offset, segs, profile=0.62):
    if offset <= 0 or segs <= 0: return
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=offset, offset_type='OFFSET', segments=segs, profile=profile,
                    affect='EDGES', clamp_overlap=True, loop_slide=True)


def box(size, pos, rot=(0, 0, 0), faces=None, bevel=0.02, segs=3, mirror=False):
    """A box (w, h, d) in game axes, centred at pos, with per-face edits BEFORE the bevel:
    faces = {'+z': dict(scale=(a, b), shift=(dx, dy), push=p), ...}. For a face on axis A the tuple refers to the
    two remaining axes in x-y-z order (for ±z: (x, y); for ±y: (x, z); for ±x: (y, z)). scale shrinks the face
    about its centre (trapezoid / wedge / pyramid), shift slides it sideways (shear, rake), push moves it along its
    own axis. Every face stays planar (affine image of the original), so the bevel and the export stay clean."""
    w, h, d = size
    bm = bmesh.new()
    r = bmesh.ops.create_cube(bm, size=1.0); verts = r['verts']
    for v in verts: v.co = Vector((v.co.x * w, v.co.y * h, v.co.z * d))
    if faces:
        for key, spec in faces.items():
            axis = 'xyz'.index(key[1]); sign = 1 if key[0] == '+' else -1
            others = [i for i in range(3) if i != axis]
            sc = spec.get('scale', (1, 1)); sh = spec.get('shift', (0, 0)); push = spec.get('push', 0.0)
            for v in verts:
                if (v.co[axis] > 0) != (sign > 0): continue
                co = v.co.copy()
                co[others[0]] = co[others[0]] * sc[0] + sh[0]
                co[others[1]] = co[others[1]] * sc[1] + sh[1]
                co[axis] += sign * push
                v.co = co
    _bevel_all(bm, bevel, segs)
    return _finish_part(bm, pos, rot, mirror)


def cyl(r_top, r_bot, h, pos, axis='y', segs=24, rot=(0, 0, 0), bevel=0.015, bsegs=2, mirror=False, cap=True):
    """capped cylinder / cone along a GAME axis; h along the axis, centred at pos. Cap-edge bevel for the light line."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=segs, radius1=r_bot, radius2=r_top, depth=h)
    # created along local z → rotate onto the requested game axis
    if axis == 'y': M = Matrix.Rotation(rad(-90), 4, 'X')
    elif axis == 'x': M = Matrix.Rotation(rad(90), 4, 'Y')
    else: M = Matrix.Identity(4)
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    if cap and bevel > 0:
        caps = [f for f in bm.faces if len(f.verts) > 4]
        edges = list({e for f in caps for e in f.edges})
        bmesh.ops.bevel(bm, geom=edges, offset=min(bevel, h * 0.3, min(r_top, r_bot) * 0.4), offset_type='OFFSET', segments=bsegs, profile=0.62, affect='EDGES', clamp_overlap=True)
    return _finish_part(bm, pos, rot, mirror)


def lathe(profile, pos, axis='y', segs=24, rot=(0, 0, 0), closed=True, mirror=False):
    """solid of revolution: profile = [(r, t), ...] with t along the GAME axis (r ≥ 0.002 — points on the axis are
    merged into a pole). closed=True joins the last point to the first (a wall with thickness, no caps needed)."""
    bm = bmesh.new()
    vs = [bm.verts.new((max(r, 0.002), 0.0, t)) for r, t in profile]
    n = len(vs)
    for i in range(n - 1): bm.edges.new((vs[i], vs[i + 1]))
    if closed: bm.edges.new((vs[-1], vs[0]))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), dvec=(0, 0, 0), angle=2 * math.pi, steps=segs, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.004)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if axis == 'y': M = Matrix.Rotation(rad(-90), 4, 'X')
    elif axis == 'x': M = Matrix.Rotation(rad(90), 4, 'Y')
    else: M = Matrix.Identity(4)
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return _finish_part(bm, pos, rot, mirror)


def tube(p0, p1, r, segs=8, bevel=0.0):
    """cylinder from game point p0 to p1 (cables, rods)."""
    a, b = Vector(p0), Vector(p1); d = b - a; L = d.length
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r, depth=L)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    M = Matrix.Translation((a + b) * 0.5) @ q.to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    return bm


def strip(size, pos, rot=(0, 0, 0), mirror=False):
    """a thin un-bevelled box — emissive seam lights, edge lights, panel lines."""
    return box(size, pos, rot, None, bevel=0.0, segs=0, mirror=mirror)


# ---------------------------------------------------------------- buckets -------------------------------------------
class Buckets:
    """collects parts per (pivot, material); to_objects() makes one mesh object per bucket, parented to the pivot."""
    def __init__(self):
        self.b = {}

    def add(self, pivot, mat, bm):
        key = (pivot.name, mat.name)
        if key not in self.b: self.b[key] = (pivot, mat, bmesh.new())
        dst = self.b[key][2]
        for v in bm.verts: v.co = B(*v.co)   # game → Blender, once
        tmp = bpy.data.meshes.new('_tmp'); bm.to_mesh(tmp); bm.free()
        dst.from_mesh(tmp); bpy.data.meshes.remove(tmp)

    def to_objects(self, names=None, sharp_deg=48.0):
        names = names or {}
        out = []
        for (pname, mname), (pivot, mat, bm) in self.b.items():
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            for f in bm.faces: f.smooth = True
            lim = rad(sharp_deg)
            for e in bm.edges:
                e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0.0) > lim)
            name = names.get((pname, mname)) or f'{pname}_{mname.replace("mech_", "")}'
            me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.update()
            me.materials.append(mat)
            ob = bpy.data.objects.new(name, me); link(ob); ob.parent = pivot; ob['name'] = name
            m = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); m.keep_sharp = True; m.mode = 'FACE_AREA'; m.weight = 60
            out.append(ob)
        self.b = {}
        return out


def apply_modifiers(objects):
    for ob in objects:
        if ob.type != 'MESH' or not ob.modifiers: continue
        with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
            for m in list(ob.modifiers):
                bpy.ops.object.modifier_apply(modifier=m.name)


def tri_count(ob):
    if ob.type != 'MESH': return 0
    dg = bpy.context.evaluated_depsgraph_get(); me = ob.evaluated_get(dg).data
    return sum(len(p.vertices) - 2 for p in me.polygons)


# ---------------------------------------------------------------- pose / hydraulics ---------------------------------
def set_pose(P, pose, pelvis_y=None):
    """pose = {pivot: (rx, ry, rz) game radians}; pivots not named are zeroed. pelvis_y = game height of Pelvis."""
    for name, e in P.items():
        r = pose.get(name, (0, 0, 0))
        e.rotation_euler = game_rot(*r).to_euler('XYZ')
    if pelvis_y is not None: P['Pelvis'].location = B(0, pelvis_y, 0)
    bpy.context.view_layer.update()


def aim_hydraulics(hyds):
    """hyds = [(body_ob, rod_ob, anchorA_ob, anchorB_ob)] — place like mech.js does: body at A, local +Z (game) → B,
    body length 0.6·L, rod length L. Geometry runs along game +Z = Blender −Y from 0 to 1."""
    bpy.context.view_layer.update()
    for body, rod, a, b in hyds:
        pa = a.matrix_world.translation.copy(); pb = b.matrix_world.translation.copy()
        d = pb - pa; L = max(d.length, 0.01)
        q = Vector((0, -1, 0)).rotation_difference(d.normalized())
        for ob, k in ((body, 0.6), (rod, 1.0)):
            ob.rotation_mode = 'QUATERNION'; ob.location = pa; ob.rotation_quaternion = q; ob.scale = (1, L * k, 1)
    bpy.context.view_layer.update()


# ---------------------------------------------------------------- export ---------------------------------------------
def export_glb(path, root, draco=True):
    allobs = []
    def rec(o):
        allobs.append(o)
        for c in o.children: rec(c)
    rec(root)
    select_only(allobs)
    props = {p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties}
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
              export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT',
              export_extras=True, export_animations=False, export_lights=False, export_cameras=False,
              export_draco_mesh_compression_enable=draco, export_draco_mesh_compression_level=6,
              export_draco_position_quantization=14, export_draco_normal_quantization=10, export_draco_texcoord_quantization=12,
              export_vertex_color='NONE', export_shared_accessors=True, export_unused_images=False, export_unused_textures=False,
              export_original_specular=False, export_hierarchy_full_collections=False, export_gn_mesh=False,
              export_optimize_animation_size=False, export_try_sparse_sk=False, export_morph=False, export_skins=False)
    kw = {k: v for k, v in kw.items() if k in props}
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    bpy.ops.export_scene.gltf(**kw)
    log('exported', path, os.path.getsize(path) // 1024, 'kB', 'draco' if draco else 'raw')
