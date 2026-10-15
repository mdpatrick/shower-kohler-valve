from pathlib import Path
import json
import bpy
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/attached_scan'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'raw_inspection.blend'))
T=Matrix(json.loads((OUT/'wall_frame.json').read_text())['raw_to_wall_frame_units'])
for o in bpy.data.objects:
    if o.type=='MESH':o.matrix_world=T
s=bpy.context.scene;c=s.camera
target=T@Vector((0,1.63,0));target.z=0
c.location=target+Vector((0,0,8));c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
c.data.ortho_scale=1.4
s.render.resolution_x=1800;s.render.resolution_y=1800
s.render.filepath=str(OUT/'plane_front.png');bpy.ops.render.render(write_still=True)
(OUT/'plane_view.json').write_text(json.dumps({'center':list(target),'span':1.4,'pixels':1800}))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'plane_inspection.blend'))
