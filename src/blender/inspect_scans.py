"""Raw-coordinate evidence views; no scaling or inter-scan registration."""
from pathlib import Path
import bpy, math, json
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/scan_inspection'; OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=1
scene.render.resolution_x=1200; scene.render.resolution_y=1200; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.world=bpy.data.worlds.new('World'); scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(0.12,0.15,0.18,1)
scene.view_settings.view_transform='Standard'
cd=bpy.data.cameras.new('Inspection'); cam=bpy.data.objects.new('Inspection',cd)
scene.collection.objects.link(cam); scene.camera=cam; cd.type='ORTHO';cd.clip_end=100
for name in ['shower-hole-valve-polycam','plates-side-1-polycam','plates-side-2-polycam']:
    for o in list(bpy.data.objects):
        if o!=cam:bpy.data.objects.remove(o,do_unlink=True)
    p=ROOT/'data/extracted'/name/'10_14_2026.obj'
    bpy.ops.wm.obj_import(filepath=str(p),forward_axis='Y',up_axis='Z')
    objects=[o for o in bpy.context.selected_objects if o.type=='MESH']
    verts=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    lo=Vector([min(v[i] for v in verts) for i in range(3)])
    hi=Vector([max(v[i] for v in verts) for i in range(3)])
    center=(lo+hi)/2; extent=hi-lo
    print('RAW_BOUNDS',name, list(lo),list(hi), flush=True)
    for o in objects:
        for mat in o.data.materials:
            if not mat:continue
            mat.use_nodes=True;nodes=mat.node_tree.nodes;links=mat.node_tree.links
            tex=next((n for n in nodes if n.type=='TEX_IMAGE'),None)
            output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
            em=nodes.new('ShaderNodeEmission');em.inputs['Color'].default_value=(.7,.7,.7,1)
            if tex:links.new(tex.outputs['Color'],em.inputs['Color'])
            links.new(em.outputs[0],output.inputs['Surface'])
    for label,direction,up in [('zplus',(0,0,1),'Y'),('yplus',(0,1,0),'Z'),('xplus',(1,0,0),'Z')]:
        cam.location=center+Vector(direction)*max(extent)*3
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z',up).to_euler()
        cd.ortho_scale=max(extent)*1.12
        scene.render.filepath=str(OUT/(name+'-'+label+'.png'))
        bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'-RAW.blend')))
