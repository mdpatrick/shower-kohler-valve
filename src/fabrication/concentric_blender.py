"""CB01 scene built from the existing credible F005 scene and CB01 CAD meshes.

All existing objects/data are retained. New display copies and layers are separate.
"""
from pathlib import Path
import bpy
import hashlib
import json
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'deliverables/current/fabrication/concentric-border-study'
BASE = ROOT / 'deliverables/current/fabrication/F005/paired_escutcheons_F005_DRAFT.blend'
A = json.loads((OUT / 'analysis.json').read_text())
REQ = json.loads((ROOT / 'canon/concentric_border_requirement.json').read_text())
P = json.loads((OUT / 'package_manifest.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(BASE))


def source_signature():
    result = {}
    # Local geometry plus object transform, without relying on excluded depsgraph state.
    for cname in ['00A_SOURCE_WALL_FULL', '01_OBSERVED_WALL']:
        for o in bpy.data.collections[cname].objects:
            if o.type != 'MESH':
                continue
            import array
            vertices = array.array('f', [0.0]) * (len(o.data.vertices) * 3)
            o.data.vertices.foreach_get('co', vertices)
            loops = array.array('i', [0]) * len(o.data.loops)
            o.data.loops.foreach_get('vertex_index', loops)
            uv = array.array('f', [0.0]) * (len(o.data.loops) * 2)
            if o.data.uv_layers.active:
                o.data.uv_layers.active.data.foreach_get('uv', uv)
            result[o.name] = {
                'vertices': hashlib.sha256(vertices.tobytes()).hexdigest(),
                'topology': hashlib.sha256(loops.tobytes()).hexdigest(),
                'uv': hashlib.sha256(uv.tobytes()).hexdigest(),
                'basis': [list(v) for v in o.matrix_basis],
                'parent': o.parent.name if o.parent else None,
            }
    return result


before = source_signature()
scene = bpy.data.scenes.new('CB01 | concentric paired escutcheons')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.threads_mode = 'FIXED'
scene.render.threads = 6
scene.render.resolution_x = 1250
scene.render.resolution_y = 1400
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.world = bpy.data.scenes['F005 | paired escutcheons'].world

for name in ['F005 Appearance wall only', 'F005 Official exterior appearance',
             'F005 Observed unchanged', 'F005 Cameras and lights', '00A_SOURCE_WALL_FULL']:
    scene.collection.children.link(bpy.data.collections[name])


def collection(name):
    c = bpy.data.collections.new('CB01 ' + name)
    scene.collection.children.link(c)
    return c


def xyz(p):
    return Vector((p[0] / 1000, -p[2] / 1000, p[1] / 1000))


B = Matrix(((.001, 0, 0, 0), (0, 0, -.001, 0), (0, .001, 0, 0), (0, 0, 0, 1)))
steel = bpy.data.materials['F005 satin stainless concept']
custom = {}
groups = {}
for variant in A['variants']:
    vid = variant['id']
    group = collection(vid + ' custom CAD')
    groups[vid] = group
    for kind in ['MAIN', 'DIV']:
        part = next(p for p in P['parts'] if p['id'] == f'{kind}-{vid}-SS060')
        bpy.ops.wm.stl_import(filepath=str(OUT / part['stl']), forward_axis='Y', up_axis='Z')
        o = bpy.context.object
        o.name = 'CB01 ' + part['id']
        o.data.transform(B)
        o.location = xyz((*A['centers_installed_mm'][kind], 1))
        for c in list(o.users_collection):
            c.objects.unlink(o)
        group.objects.link(o)
        o.data.materials.clear()
        o.data.materials.append(steel)
        o['CAD_source'] = part['step']
        o['CAD_sha256'] = part['sha256']['step']
        o['evidence'] = 'CB01 CAD master. Inferred cover center. Physical fit unverified.'
        o['assumed_seal_gap_mm'] = 1
        custom[part['id']] = o

# Exploded C1 uses the same factory components/offsets as the earlier diagnostic.
exploded = collection('Exploded C1')
for old in bpy.data.collections['F005 Exploded A'].objects:
    if old.name in ['F005 EXPLODED MAIN-A', 'F005 EXPLODED DIV-A']:
        continue
    o = old.copy()
    o.name = 'CB01 ' + old.name.replace('F005 ', '')
    exploded.objects.link(o)
for kind in ['MAIN', 'DIV']:
    old = custom[f'{kind}-C1-SS060']
    o = old.copy()
    o.name = 'CB01 EXPLODED ' + kind + '-C1'
    exploded.objects.link(o)
    o.location.y -= .025
    o['display_offset_mm'] = 25

# A separately named derived state carries fitted tips without moving the captured mesh.
loc = json.loads((OUT / 'stud_locator_analysis.json').read_text())
model = json.loads((OUT / 'reconciled_model_state.json').read_text())
locator_group = collection('LOC01 diagnostic tabs')
bpy.ops.wm.stl_import(filepath=str(OUT / loc['diagnostic_CAD'][1]), forward_axis='Y', up_axis='Z')
locator = bpy.context.object
locator.name = 'CB01 LOC01 upper tabs | unresolved fit'
locator.data.transform(B)
locator.location = xyz((*A['centers_installed_mm']['MAIN'], 1))
for old in list(locator.users_collection):
    old.objects.unlink(locator)
locator_group.objects.link(locator)
locator.data.materials.clear()
locator.data.materials.append(steel)
locator['status'] = 'DIAGNOSTIC ONLY: intersects unchanged scan at trial placement. See LOC01 analysis.'
locator['hole_sizes_are_assumptions'] = True
for key, point in model['tip_centers_installed_mm'].items():
    datum = bpy.data.objects.new('RECON-001 fitted tip ' + key, None)
    locator_group.objects.link(datum)
    datum.location = xyz(point)
    datum.empty_display_type = 'SPHERE'
    datum.empty_display_size = .002
    datum['model_state'] = model['id']
    datum['not_measured_axis_intersection'] = True
cd = bpy.data.cameras.new('CB01 Locator front')
cam = bpy.data.objects.new('CB01 Locator front', cd)
locator_group.objects.link(cam)
cam.location = xyz((A['centers_installed_mm']['MAIN'][0], A['centers_installed_mm']['MAIN'][1], 700))
cam.rotation_euler = (xyz((*A['centers_installed_mm']['MAIN'], 0)) - cam.location).to_track_quat('-Z','Y').to_euler()
cd.type = 'ORTHO'; cd.ortho_scale = .265; cd.clip_start = .001; cd.clip_end = 20

common = ['F005 Appearance wall only', 'F005 Official exterior appearance', 'F005 Cameras and lights']
layers = {
    'C1 concentric appearance': common + [groups['C1'].name],
    'C2 equal 15 mm borders': common + [groups['C2'].name],
    'Observed unchanged': ['F005 Observed unchanged', 'F005 Cameras and lights'],
    'Exploded C1': ['F005 Observed unchanged', exploded.name, 'F005 Cameras and lights'],
    'LOC01 tabs diagnostic': [locator_group.name, 'F005 Cameras and lights'],
}
for i, (name, visible) in enumerate(layers.items()):
    vl = scene.view_layers[0] if i == 0 else scene.view_layers.new(name)
    vl.name = name
    for c in vl.layer_collection.children:
        c.exclude = c.name not in visible
    vl.use = False

for prop in ['use_stamp_time', 'use_stamp_date', 'use_stamp_render_time', 'use_stamp_frame',
             'use_stamp_filename', 'use_stamp_camera', 'use_stamp_scene', 'use_stamp_hostname',
             'use_stamp_marker', 'use_stamp_memory', 'use_stamp_lens']:
    setattr(scene.render, prop, False)
scene.render.use_stamp = True
scene.render.use_stamp_note = True
scene.render.use_stamp_labels = False
scene.render.stamp_font_size = 16
scene.render.stamp_background = (.025, .06, .08, .9)
scene.render.stamp_foreground = (1, 1, 1, 1)

views = [('C1_front', 'C1 concentric appearance', 'Front pair'),
         ('C1_oblique', 'C1 concentric appearance', 'Oblique pair'),
         ('C2_front', 'C2 equal 15 mm borders', 'Front pair'),
         ('C2_oblique', 'C2 equal 15 mm borders', 'Oblique pair'),
         ('C1_exploded', 'Exploded C1', 'Exploded'),
         ('LOC01_tabs', 'LOC01 tabs diagnostic', 'LOCATOR')]
for filename, layer, camera in views:
    for vl in scene.view_layers:
        vl.use = vl.name == layer
    bpy.context.window.view_layer = scene.view_layers[layer]
    scene.camera = cam if camera == 'LOCATOR' else bpy.data.objects['F005 ' + camera]
    scene.render.stamp_note_text = ('LOC01 | DIAGNOSTIC TAB TRIAL - assumed holes / axes; unresolved scan conflicts'
        if camera == 'LOCATOR' else 'CB01 | EXPLODED - display offsets only; rear foam/fit unresolved'
        if 'exploded' in filename else f'CB01 {filename[:2]} | CONDITIONAL APPEARANCE - depth/foam/fit unresolved')
    scene.render.filepath = str(OUT / 'views' / (filename + '.png'))
    bpy.ops.render.render(write_still=True)
    print('Rendered', filename, flush=True)

for vl in scene.view_layers:
    vl.use = vl.name == 'C1 concentric appearance'
bpy.context.window.view_layer = scene.view_layers['C1 concentric appearance']
scene.camera = bpy.data.objects['F005 Oblique pair']
scene['study_revision'] = 'CB01'
scene['evidence_revision'] = 'R005 plus separate RECON-001 (not adopted into placement)'
scene['status'] = 'DRAFT_NOT_FOR_FABRICATION'
scene['geometry_rule'] = 'Custom circles share inferred cover centers; no intentional XY offsets.'
scene['limits'] = 'Hardware omitted only in cosmetic wall copy. Observed scan and F005 states preserved.'
scene['thickness_shown_mm'] = 1.524
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
bpy.ops.file.pack_all()
path = OUT / 'paired_concentric_CB01_DRAFT.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
bpy.ops.wm.open_mainfile(filepath=str(path))
assert before == source_signature(), 'Original scan/proxy changed'
scene = bpy.data.scenes['CB01 | concentric paired escutcheons']
bpy.context.window.scene = scene
checks = []
for vid, layer in [('C1', 'C1 concentric appearance'), ('C2', 'C2 equal 15 mm borders')]:
    bpy.context.window.view_layer = scene.view_layers[layer]
    bpy.context.view_layer.update()
    for kind in ['MAIN', 'DIV']:
        part = next(p for p in P['parts'] if p['id'] == f'{kind}-{vid}-SS060')
        o = bpy.data.objects['CB01 ' + part['id']]
        co = [o.matrix_world @ Vector(c) for c in o.bound_box]
        bounds = [max(v[i] for v in co) - min(v[i] for v in co) for i in range(3)]
        expected = [part['diameter_mm'], part['thickness_mm'], part['diameter_mm']]
        assert max(abs(x * 1000 - y) for x, y in zip(bounds, expected)) < .06
        center = A['centers_installed_mm'][kind]
        assert (o.location - xyz((*center, 1))).length < 1e-7
        cover = bpy.data.objects['F005 KOHLER ' + ('T14489-4' if kind == 'MAIN' else 'T14491-4') + ' component 0']
        assert abs(o.location.x - cover.location.x) < 1e-9
        assert abs(o.location.z - cover.location.z) < 1e-9
        checks.append({'part': part['id'], 'CAD_bounds_and_placement': 'PASS', 'cover_origin_shared': True})
missing = [i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file
           and not Path(bpy.path.abspath(i.filepath)).exists()]
assert not missing
bpy.context.window.view_layer = scene.view_layers['C1 concentric appearance']
# Save the default view after QA too.
bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
(OUT / 'blender_validation.json').write_text(json.dumps({
    'status': 'PASS - software checks only', 'saved_and_reopened': True,
    'source_scan_and_proxy_signatures_unchanged': before == source_signature(),
    'source_signatures': before, 'missing_images': missing, 'custom_checks': checks,
    'rendered_views': [v[0] for v in views],
    'appearance_limit': 'Official exterior tessellation; ideal circles define the border. No physical fit proven.',
    'input_package_sha256': hashlib.sha256((OUT / 'package_manifest.json').read_bytes()).hexdigest(),
}, indent=2) + '\n')
print('CB01 saved, reopened and checked', flush=True)
