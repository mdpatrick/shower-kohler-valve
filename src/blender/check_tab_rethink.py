"""Reopen the saved TR02 scene and verify source transforms and displayed CAD."""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'deliverables/current/fabrication/FT02/tab-rethink'
B=Matrix(((.001,0,0,0),(0,0,-.001,0),(0,.001,0,0),(0,0,0,1)))
path=OUT/'TR02_tabs_scans_and_handles.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
reg=json.loads((ROOT/'data/derived/registration.json').read_text())
ass=json.loads((ROOT/'deliverables/current/fabrication/fit-trial/attached_scan_assessment.json').read_text())
expected={
 'data/extracted/shower-hole-valve-polycam/10_14_2026.obj':B@Matrix(reg['raw_to_installed_mm']),
 'data/extracted/polycam-inner-plate-attached/10_15_2026.obj':B@Matrix(ass['raw_to_local_diagnostic_mm'])}
observed=[]
for obj in bpy.data.objects:
    if obj.get('source') in expected:
        # Background file reads can leave inactive matrix_world caches at identity.
        # These source objects have no parent/constraints/animation. Compare the
        # actual persisted location/rotation/scale, not that unevaluated cache.
        assert obj.parent is None and not obj.constraints and not obj.animation_data
        saved=Matrix.LocRotScale(obj.location,obj.rotation_euler.to_quaternion(),obj.scale)
        target=expected[obj['source']]
        error=max(abs(saved[i][j]-target[i][j]) for i in range(4) for j in range(4))
        assert error<1e-6,(obj.name,error)
        assert len(obj.data.vertices)>10000
        observed.append({'object':obj.name,'source':obj['source'],'saved_transform_max_difference':error,'vertices':len(obj.data.vertices)})
assert {x['source'] for x in observed}==set(expected)
scenes=[]
for s in bpy.data.scenes:
    if not s.name.startswith(('TR02','RF01')):continue
    assert s.camera and s.frame_start==1 and s.frame_end==36
    assert s.camera.animation_data and s.camera.animation_data.action
    scenes.append(s.name)
assert len(scenes)==10,scenes
form=[o for o in bpy.data.objects if o.get('CAD_source','').endswith('RF01_MAIN_REMOVABLE_FORM_PETG.stl')]
assert len(form)==3
for o in form:
    points=[v.co for v in o.data.vertices]
    bounds=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
    assert abs(bounds[0]-.240)<1e-6 and abs(bounds[2]-.240)<1e-6 and abs(bounds[1]-.024)<1e-6
plate=bpy.data.objects['2 mm inward support study']
assert plate['CAD_source'].endswith('inward_2.stl')
images=[]
for im in bpy.data.images:
    if im.source=='FILE' and im.size[0]>0:
        assert im.packed_file or im.packed_files,im.name
        images.append(im.name)
result={'status':'PASS','fresh_saved_file_readback':True,'scene_names':scenes,'source_captures':observed,
 'RF01_actual_export_instances':len(form),'RF01_bounds_mm':[240,240,24],
 'factory_handle_scene_backing':'TR02 inward_2 CAD export','packed_images':images,
 'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'physical_checks':'NOT PERFORMED; no fit, repair strength or sealing certification'}
(OUT/'blender_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
