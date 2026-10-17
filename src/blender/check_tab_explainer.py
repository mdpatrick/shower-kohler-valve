"""Read back the explanatory animation without rebuilding or altering it."""
import json
from pathlib import Path

import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'deliverables/current/fabrication/FT02/tab-explainer'
bpy.ops.wm.open_mainfile(filepath=str(OUT / 'FT02_tab_explanation.blend'))
scene = bpy.context.scene
B = Matrix(((.001, 0, 0, 0), (0, 0, -.001, 0), (0, .001, 0, 0), (0, 0, 0, 1)))
registration = json.loads((ROOT / 'data/derived/registration.json').read_text())
expected = B @ Matrix(registration['raw_to_installed_mm'])
captures = [o for o in scene.objects if o.get('source') ==
            'data/extracted/shower-hole-valve-polycam/10_14_2026.obj']
assert captures
capture_names = {o.name for o in captures}
assert scene.frame_end == 540 and scene.render.fps == 15
assert scene.camera is not None
checked = []
for frame, visible in [
    (46, {'Original captured wall and valve', 'tabbed_candidate'}),
    (301, {'Original captured wall and valve', 'tabbed_candidate', 'Callout around scan overlap'}),
    (346, {'backing_section', 'foam_section'}),
    (451, {'backing_section', 'foam_section'}),
    (511, {'Original captured wall and valve', 'plain'}),
]:
    if 'Original captured wall and valve' in visible:
        visible = visible | capture_names
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    actual = {o.name for o in scene.objects if o.type == 'MESH' and not o.hide_render}
    viewport = {o.name for o in scene.objects if o.type == 'MESH' and not o.hide_viewport}
    assert actual == visible, (frame, actual, visible)
    assert viewport == visible, (frame, viewport, visible)
    for capture in captures:
        assert max(abs(capture.matrix_world[i][j] - expected[i][j])
                   for i in range(4) for j in range(4)) < 1e-7
    checked.append({'frame': frame, 'visible': sorted(actual), 'capture_transform': 'UNCHANGED'})
packed = [im.name for im in bpy.data.images if im.packed_file]
assert packed, 'No packed capture texture'
result = {'status': 'PASS', 'saved_scene_reopened': True, 'chapters_checked': checked,
          'packed_images': packed, 'physical_fit': 'NOT PERFORMED'}
(OUT / 'blender_readback.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result), flush=True)
