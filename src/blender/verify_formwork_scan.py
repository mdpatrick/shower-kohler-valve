"""Reopen FS01 and verify saved evidence, units, transforms and packed texture."""
from pathlib import Path
import json
import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'deliverables/current/analysis/formwork-scan-FS01'
analysis = json.loads((OUT/'analysis.json').read_text())
cfg = json.loads((ROOT/'canon/formwork_scan_assessment_FS01.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(OUT/'formwork_scan_FS01.blend'))
scene = bpy.context.scene
observed = bpy.data.collections['OBSERVED | new Polycam, form-calibrated diagnostic']
ideal = bpy.data.collections['REFERENCE | ideal CAD form; toggle only for comparison']
meshes = [o for o in observed.objects if o.type == 'MESH']
assert len(meshes) == 1
assert len(meshes[0].data.vertices) == analysis['input_vertices']
assert scene.unit_settings.system == 'METRIC' and scene.unit_settings.scale_length == 1
mapping = Matrix(((.001,0,0,0),(0,0,-.001,0),(0,.001,0,0),(0,0,0,1)))
expected = mapping @ Matrix(analysis['raw_to_form_diagnostic_mm'])
assert max(abs(meshes[0].matrix_world[i][j]-expected[i][j]) for i in range(4) for j in range(4)) < 1e-6
assert meshes[0]['source_sha256'] == cfg['archive_sha256']
assert ideal.hide_render and ideal.hide_viewport and len(ideal.objects) == 1
assert len([o for o in scene.objects if o.type == 'MESH']) == 2
file_images = [i for i in bpy.data.images if i.source == 'FILE']
assert file_images and all(i.packed_file is not None for i in file_images)
result = {
    'status': 'PASS_SAVED_FILE_READBACK',
    'observed_vertices': len(meshes[0].data.vertices),
    'packed_texture_count': len(file_images),
    'metric_units_and_single_coordinate_conversion_verified': True,
    'ideal_CAD_collection_hidden_and_separate': True,
    'primary_scene_not_opened_or_modified': True,
    'physical_fit_verified': False,
}
(OUT/'blender_readback.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result))
