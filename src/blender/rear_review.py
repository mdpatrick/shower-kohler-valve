"""REAR01: preserve the model and add explicit current-state / rear-photo scenes.

The photographs are reference boards, not a registered reconstruction. No CAD,
captured mesh, dimensional landmark or original material is changed.
"""
from pathlib import Path
import array
import hashlib
import json
import bpy

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'deliverables/current/fabrication/concentric-border-study/paired_concentric_CB01_DRAFT.blend'
OUT = ROOT / 'deliverables/current/blender/installation_REAR01_DRAFT.blend'
REVIEW = ROOT / 'deliverables/current/review/rear'
RECORD = ROOT / 'docs/physical_checks/rear_installation_2026-10-15.json'
record = json.loads(RECORD.read_text())
bpy.ops.wm.open_mainfile(filepath=str(BASE))


def signatures():
    result = {}
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        vv = array.array('f', [0]) * (len(o.data.vertices) * 3)
        ii = array.array('i', [0]) * len(o.data.loops)
        o.data.vertices.foreach_get('co', vv)
        o.data.loops.foreach_get('vertex_index', ii)
        uv = array.array('f', [0]) * (len(o.data.loops) * 2)
        if o.data.uv_layers.active:
            o.data.uv_layers.active.data.foreach_get('uv', uv)
        result[o.name] = dict(vertices=hashlib.sha256(vv.tobytes()).hexdigest(),
            topology=hashlib.sha256(ii.tobytes()).hexdigest(),
            uv=hashlib.sha256(uv.tobytes()).hexdigest(),
            basis=[list(r) for r in o.matrix_basis],
            parent=o.parent.name if o.parent else None)
    return result


before = signatures()
foam_names = []
for o in bpy.data.objects:
    if any(word in o.name.lower() for word in ['foam', 'gasket']):
        o['current_installation_state'] = 'NOT INSTALLED; removed factory plate component / reference only'
        o['foam_record'] = str(RECORD.relative_to(ROOT))
        foam_names.append(o.name)
for s in bpy.data.scenes:
    s['current_exposed_state'] = 'No foam or trim installed. Foam shown elsewhere belongs to the removed factory inner plate.'
    s['rear_geometry_limit'] = 'The front scan is not a surveyed rear assembly. See REAR01 | current rear photos.'

# An unambiguous as-found scene contains the scan alone, no invented rear solids.
front = bpy.data.scenes.new('REAR01 | current front scan ONLY')
front.world = bpy.data.scenes['F005 | paired escutcheons'].world
front.unit_settings.system = 'METRIC'
front.unit_settings.length_unit = 'MILLIMETERS'
for name in ['F005 Observed unchanged', 'F005 Cameras and lights']:
    front.collection.children.link(bpy.data.collections[name])
front.camera = bpy.data.objects['F005 Front pair']
front['state'] = 'CURRENT EXPOSED INSTALLATION: preserved front scan only; foam and removed trim excluded.'
front['rear_limit'] = 'Front-captured surfaces seen from behind are not the rear plumbing or framing. Use the rear photo scene.'
front['physical_scale'] = 'Original provisional scan registration retained.'

# Photo boards are in a separate, explicitly unscaled display coordinate system.
scene = bpy.data.scenes.new('REAR01 | current rear photos')
bpy.context.window.scene = scene
scene['state'] = 'CURRENT REAR PHOTO EVIDENCE; no installed foam. Boards are NOT spatially registered.'
scene['photo_scale'] = 'Display layout only; do not measure these boards as installation geometry.'
scene['dimensional_update'] = 'NONE'
scene.world = bpy.data.worlds.new('REAR01 neutral board')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.025, .04, .05, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = 1
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 1
scene.render.threads_mode = 'FIXED'
scene.render.threads = 4
scene.render.resolution_x = 2000
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1


def emission(name, color):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    emit = nodes.new('ShaderNodeEmission')
    emit.inputs[0].default_value = (*color, 1)
    m.node_tree.links.new(emit.outputs[0], output.inputs['Surface'])
    return m, emit


white, _ = emission('REAR01 white text', (.9, .94, .96))
amber, _ = emission('REAR01 contact indicator', (1, .5, .12))


def label(name, text, x, y, size=.025, material=white):
    data = bpy.data.curves.new(name, 'FONT')
    data.body = text
    data.size = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = (x, y, .01)
    obj.data.materials.append(material)
    return obj


label('REAR01 heading', 'CURRENT REAR INSTALLATION', -1.06, .58, .042)
label('REAR01 subheading', 'Actual photographs | no installed foam | no dimensional registration', -1.06, .52, .025)
for p, x in zip(record['photos'], [-.55, .55]):
    path = ROOT / p['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == p['sha256']
    img = bpy.data.images.load(str(path), check_existing=True)
    img.pack()
    width = 1.04
    height = width * img.size[1] / img.size[0]
    mesh = bpy.data.meshes.new('REAR01 photo plane ' + p['view'])
    mesh.from_pydata([(-width/2, -height/2, 0), (width/2, -height/2, 0),
                     (width/2, height/2, 0), (-width/2, height/2, 0)], [], [(0, 1, 2, 3)])
    uv = mesh.uv_layers.new()
    for loop, value in zip(uv.data, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        loop.uv = value
    obj = bpy.data.objects.new('REAR01 UNREGISTERED PHOTO ' + p['view'], mesh)
    scene.collection.objects.link(obj)
    obj.location = (x, .02, 0)
    material, emit = emission('REAR01 photo ' + p['view'], (1, 1, 1))
    tex = material.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = img
    material.node_tree.links.new(tex.outputs['Color'], emit.inputs[0])
    obj.data.materials.append(material)
    obj['source_sha256'] = p['sha256']
    obj['not_registered_to_model'] = True
    label('REAR01 title ' + p['view'],
          'Threaded rod beside wood' if p['view'] == 'close' else 'Wider rear / framing context',
          x - width/2, .44, .027)

label('REAR01 note 1', 'Rod/wood contact is consistent with your report; both stud paths still need tracing.', -1.06, -.43, .026)
label('REAR01 note 2', 'The foam measurements describe the removed factory inner plate, not cavity filling.', -1.06, -.48, .026)
label('REAR01 note 3', 'Front scan retained separately. Rear dimensions and any drilling/cutting remedy remain unresolved.', -1.06, -.53, .024)
camera_data = bpy.data.cameras.new('REAR01 photo camera')
camera = bpy.data.objects.new('REAR01 photo camera', camera_data)
scene.collection.objects.link(camera)
camera.location = (0, .01, 4)
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 2.3
scene.camera = camera

notes = bpy.data.texts.new('READ FIRST - REAR01 current state')
notes.write('CURRENT INSTALLATION: exposed valve, no installed foam or factory trim.\n'
    'The approximately 6 mm foam section belongs to the removed factory inner plate.\n'
    'Use REAR01 | current rear photos for genuine rear evidence. Photo planes are unscaled and unregistered.\n'
    'Use REAR01 | current front scan ONLY for the preserved front capture without trim/gasket/envelopes.\n'
    'The rear of a front surface capture is not a reconstructed rear assembly.\n'
    'Older trial, appearance and exploded scenes are retained as design references.\n'
    'A threaded rod appears to end at wood; this supports the reported obstruction, not a selected remedy.\n'
    'Trace each front trim stud through to its rear end and establish adjustment/engagement before any modification.\n'
    'REAR01 changes no CAD, dimensions, registration, fit results or manufacturing status.\n')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.shading.type = 'MATERIAL'
            area.spaces.active.overlay.show_overlays = False
REVIEW.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(REVIEW / 'rear_photos_REAR01.png')
bpy.ops.render.render(write_still=True)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT))
after = signatures()
assert all(after[name] == sig for name, sig in before.items())
assert len(bpy.data.scenes['REAR01 | current front scan ONLY'].collection.children) == 2
visible_front = {o.name for o in bpy.data.scenes['REAR01 | current front scan ONLY'].objects}
assert not visible_front.intersection(foam_names)
missing = [i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file
           and not Path(bpy.path.abspath(i.filepath)).exists()]
assert not missing
validation = dict(status='PASS - source preservation and scene-content checks',
    saved_and_reopened=True, source_file=str(BASE.relative_to(ROOT)),
    source_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),
    original_mesh_objects_preserved=len(before), original_mesh_geometry_uv_and_placement_unchanged=True,
    no_foam_in_current_front_scene=True, foam_reference_objects_labeled=foam_names,
    photo_hashes={p['path']:p['sha256'] for p in record['photos']},
    missing_images=missing, default_scene=bpy.context.scene.name,
    physically_registered_rear_model=False, dimensional_changes=False,
    physical_fit='NOT PERFORMED', fabrication_release='NOT GIVEN')
(REVIEW / 'blender_validation.json').write_text(json.dumps(validation, indent=2) + '\n')
print(json.dumps(validation, indent=2), flush=True)
