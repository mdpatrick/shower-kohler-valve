from pathlib import Path
import bpy,json
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'build/scan_inspection/shower-hole-valve-polycam-RAW.blend'))
reg=json.loads((ROOT/'data/derived/registration.json').read_text());M=Matrix(reg['raw_to_blender_m'])
for o in bpy.data.objects:
    if o.type=='MESH':o.matrix_world=M
scene=bpy.context.scene;cam=scene.camera
scene.cycles.samples=1;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=6
for name,center,span,size in [('wall_aligned',(0,40,0),620,1800),('wall_detail',(0,40,0),280,2200)]:
    target=Vector((center[0]/1000,-center[2]/1000,center[1]/1000))
    cam.location=target+Vector((0,-2,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=span/1000;cam.data.clip_start=.001
    scene.render.resolution_x=size;scene.render.resolution_y=size
    scene.render.filepath=str(ROOT/'build/scan_inspection'/f'{name}.png');bpy.ops.render.render(write_still=True)
    (ROOT/'build/scan_inspection'/f'{name}.json').write_text(json.dumps({'center_installed_mm':center,'span_mm':span,'pixels':size}))
