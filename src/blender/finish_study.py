"""FIN01 appearance-only lighting study using the existing FT02 CAD scene."""
from pathlib import Path
import bpy, json, hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'deliverables/current/fabrication/FT02/finish-study'
OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'deliverables/current/fabrication/FT02/escutcheon_fit_trial_FT02.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.data.scenes['FT02 | proposed appearance']
bpy.context.window.scene=scene
for other in list(bpy.data.scenes):
    if other!=scene:bpy.data.scenes.remove(other)
scene.name='FIN01 | illustrative stainless and Kohler finish'
def xyz(v):return Vector((v[0]/1000,-v[2]/1000,v[1]/1000))
def finish(name,color,rough,anisotropy,grain):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    n=mat.node_tree.nodes;links=mat.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=1;p.inputs['Roughness'].default_value=rough
    socket=p.inputs.get('Anisotropic') or p.inputs.get('Anisotropic IOR Level')
    assert socket is not None, [s.name for s in p.inputs]
    socket.default_value=anisotropy
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=1;tex.inputs['Detail'].default_value=2
    coord=n.new('ShaderNodeTexCoord');scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY'
    scale.inputs[1].default_value=(70000,1000,250)
    links.new(coord.outputs['Object'],scale.inputs[0]);links.new(scale.outputs[0],tex.inputs[0])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=grain;bump.inputs['Distance'].default_value=.000003
    links.new(tex.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],p.inputs['Normal'])
    mat['scope']='Illustrative shader; not measured color, roughness or grain.'
    return mat
steel=finish('FIN01 generic straight-grain brushed stainless',(.52,.53,.54),.32,.45,.20)
nickel=finish('FIN01 approximate Kohler BN silver',(.54,.51,.46),.29,.25,.055)
parts=[]
for ob in scene.objects:
    if ob.type!='MESH':continue
    if ob.name.startswith('FT02_MAIN') or ob.name.startswith('FT02_DIV'):
        ob.data.materials.clear();ob.data.materials.append(steel);parts.append(ob)
    elif ob.name.startswith('Kohler official exterior'):
        ob.data.materials.clear();ob.data.materials.append(nickel)
for ob in list(scene.objects):
    if ob.type=='LIGHT':bpy.data.objects.remove(ob,do_unlink=True)
def area(name,where,power,width,height,target,color):
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='RECTANGLE'
    light.size=width;light.size_y=height;light.color=color
    ob=bpy.data.objects.new(name,light);scene.collection.objects.link(ob)
    ob.location=xyz(where);ob.rotation_euler=(xyz(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob
lights=[area('Broad window reflection',(-300,270,450),4,.22,.65,(0,-20,0),(1,1,1)),
        area('Soft fill',(350,-60,360),1.6,.32,.55,(0,-20,0),(1,1,1)),
        area('Ceiling',(0,380,250),1.5,.4,.2,(0,-20,0),(1,1,1))]
scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get('Background');bg.inputs[0].default_value=(.42,.42,.42,1);bg.inputs[1].default_value=.45
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=6
scene.render.resolution_x=1120;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0
def view(where,target,span,name):
    scene.camera.location=xyz(where);scene.camera.rotation_euler=(xyz(target)-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera.data.ortho_scale=span/1000
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
view((0,-25,800),(0,-25,0),395,'FIN01_front')
view((170,25,750),(0,-25,0),408,'FIN01_oblique')
for ob in lights:ob.data.color=(1,.84,.67)
view((0,-25,800),(0,-25,0),395,'FIN01_warm_light')
for ob in lights:ob.data.color=(1,1,1)
scene.camera.location=xyz((0,-25,800));scene.camera.rotation_euler=(xyz((0,-25,0))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=.395
notes=bpy.data.texts.new('FIN01 - appearance scope')
notes.write('FT02 CAD sizes and official Kohler exterior models on the existing scan-derived travertine wall.\n'
 'Materials and lighting are illustrative. No measured Ponoko lot or Kohler color calibration.\n'
 'Do not use render color, hidden assembly, seal omission or wall derivative as physical evidence.\n'
 'A factory BN finish and #4 brushed stainless may coordinate without matching. A sample beside the existing cover in bathroom light decides.\n')
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FIN01_finish_illustration.blend'),compress=True)
report={'revision':'FIN01','purpose':'Appearance illustration, not a finish approval','source_scene':str(SOURCE.relative_to(ROOT)),
        'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'custom_parts':[{'name':p.name,'source':p.get('source'),'dimensions_mm':list(p.get('CAD_dimensions_mm',[]))} for p in parts],
        'factory_geometry':'Official Kohler exterior CAD already in FT02; hidden connections not shown',
        'wall':'Existing scan-derived appearance wall; not generated new construction evidence',
        'images':['FIN01_front.png','FIN01_oblique.png','FIN01_warm_light.png'],
        'limits':['No physical finish sample inspected','No calibrated color or reflectance match','Actual sheet grain direction and cosmetic condition remain supplier-dependent','No CAD dimensions or physical fit state changed']}
(OUT/'render_provenance.json').write_text(json.dumps(report,indent=2)+'\n')
print('FIN01 rendered with unchanged custom CAD and source wall',flush=True)
