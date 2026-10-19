"""FS01 observed scan, with an explicitly optional ideal CAD overlay."""
from pathlib import Path
import bpy, json, math
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'deliverables/current/analysis/formwork-scan-FS01'
cfg = json.loads((ROOT/'canon/formwork_scan_assessment_FS01.json').read_text())
r = json.loads((OUT/'analysis.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
s.unit_settings.system = 'METRIC'; s.unit_settings.scale_length = 1
s.render.engine = 'BLENDER_WORKBENCH'
s.display.shading.light = 'STUDIO'; s.display.shading.color_type = 'TEXTURE'
s.display.shading.show_shadows = False; s.display.shading.background_type = 'WORLD'
s.world = bpy.data.worlds.new('Background'); s.world.color = (.84, .87, .89)
s.view_settings.view_transform = 'Standard'
s.render.resolution_x = 1800; s.render.resolution_y = 1800; s.render.resolution_percentage = 100
s.render.image_settings.file_format = 'PNG'

observed = bpy.data.collections.new('OBSERVED | new Polycam, form-calibrated diagnostic')
s.collection.children.link(observed)
bpy.ops.wm.obj_import(filepath=str(ROOT/cfg['extracted_obj']), forward_axis='Y', up_axis='Z')
mapping = Matrix(((.001,0,0,0),(0,0,-.001,0),(0,.001,0,0),(0,0,0,1)))
scan_t = mapping @ Matrix(r['raw_to_form_diagnostic_mm'])
scan_objects = list(bpy.context.selected_objects)
for o in scan_objects:
    for c in list(o.users_collection): c.objects.unlink(o)
    observed.objects.link(o); o.matrix_world = scan_t
    o['source_sha256'] = cfg['archive_sha256']; o['assumption'] = cfg['owner_assumption']
    o['status'] = 'Observed mesh, uniform diagnostic calibration; no local warp correction'

ideal = bpy.data.collections.new('REFERENCE | ideal CAD form; toggle only for comparison')
s.collection.children.link(ideal)
bpy.ops.wm.stl_import(filepath=str(ROOT/cfg['selected_reference']))
printed_to_front = Matrix(((1,0,0,-120),(0,-1,0,120),(0,0,-1,0),(0,0,0,1)))
for o in list(bpy.context.selected_objects):
    for c in list(o.users_collection): c.objects.unlink(o)
    ideal.objects.link(o); o.matrix_world = mapping @ printed_to_front
    o.name = 'IDEAL CAD RF03 D24 | not an observed surface'
    o.color = (.05,.55,.65,1); o.display_type = 'WIRE'
    o['source'] = cfg['selected_reference']
ideal.hide_render = True; ideal.hide_viewport = True

cam = bpy.data.objects.new('Front measurement view', bpy.data.cameras.new('Front measurement view'))
s.collection.objects.link(cam); s.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = .285
for name, position in [('scan_front',(0,-.8,0)),('scan_oblique',(.4,-.8,.2))]:
    cam.location = position
    cam.rotation_euler = (Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath = str(OUT/(name+'.png')); bpy.ops.render.render(write_still=True)
cam.location = (0,-.8,0); cam.rotation_euler = (Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
s['read_first'] = 'FS01: scale from exact-print assumption; no tighter-form release. See index.html and analysis.json.'
s['CAD_transform'] = 'print XYZ -> front-frame mm -> Blender (x,-z,y)/1000; applied once'
bpy.ops.file.pack_all()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.shading.color_type = 'TEXTURE'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'formwork_scan_FS01.blend'))
meta = {'observed_mesh_objects': len(scan_objects), 'vertices': sum(len(o.data.vertices) for o in scan_objects if o.type == 'MESH'),
        'ideal_CAD_overlay_hidden': True, 'units': 'Blender meters', 'source_archive': cfg['archive'],
        'renders': ['scan_front.png','scan_oblique.png'], 'no_primary_scene_modified': True}
(OUT/'blender_check.json').write_text(json.dumps(meta, indent=2)+'\n')
