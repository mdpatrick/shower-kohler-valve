from pathlib import Path
import bpy,json,sys
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'build/coordinate_test'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=str(OUT/'test.stl'),forward_axis='Y',up_axis='Z')
o=bpy.context.object;o.name='100x60x4mm_NE_clip_hole_20_15'
B=Matrix(((.001,0,0,0),(0,0,-.001,0),(0,.001,0,0),(0,0,0,1)))
o.data.transform(B);o['source']='CadQuery test.stl';o['units']='meters'
bpy.context.view_layer.update();dims=list(o.dimensions)
assert all(abs(a-b)<1e-7 for a,b in zip(dims,[.1,.004,.06])),dims
verts=[v.co for v in o.data.vertices]
assert min((v-Vector((.1,0,.05))).length for v in verts)<1e-6
assert min((v-Vector((.09,0,.06))).length for v in verts)<1e-6
ring=[v for v in verts if abs(((v.x-.02)**2+(v.z-.015)**2)**.5-.005)<1e-6]
assert len(ring)>40
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
mat=bpy.data.materials.new('Test orange');mat.diffuse_color=(.8,.28,.04,1);o.data.materials.append(mat)
cd=bpy.data.cameras.new('Front');cam=bpy.data.objects.new('Front',cd);scene.collection.objects.link(cam)
cam.location=(.05,-.3,.03);cam.rotation_euler=(Vector((.05,0,.03))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=.12;cd.clip_start=.001;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=4;scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.world=bpy.data.worlds.new('World');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
scene.render.resolution_x=800;scene.render.resolution_y=500;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(OUT/'blender_test.png');bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'coordinate_test.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'test.blend'),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT/'test.blend'))
assert bpy.data.objects.get('100x60x4mm_NE_clip_hole_20_15')
(OUT/'blender_check.json').write_text(json.dumps({'status':'PASS','version':bpy.app.version_string,'dims_m':dims,'hole_ring_vertex_count':len(ring),'NE_marker_verified':True,'save_reopen_verified':True,'CPU_render_saved':True},indent=2)+'\n')
