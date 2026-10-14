"""Build the local inspection workspace from preserved scans + CadQuery outputs."""
from pathlib import Path
import bpy,bmesh,json,math,sys
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'deliverables/current/blender';VIEWS=ROOT/'deliverables/current/review/views'
OUT.mkdir(parents=True,exist_ok=True);VIEWS.mkdir(parents=True,exist_ok=True)
d=json.loads((ROOT/'data/derived/resolved.json').read_text());reg=json.loads((ROOT/'data/derived/registration.json').read_text())
cad=json.loads((ROOT/'data/derived/cad/parts.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.name=f"Installation {d['revision']} - provisional"
scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=False
scene.render.threads_mode='FIXED';scene.render.threads=6
scene.render.resolution_x=1300;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard'
scene.world=bpy.data.worlds.new('Neutral world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.69,.73,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
collections={}
def coll(name):
    if name not in collections:
        c=bpy.data.collections.new(name);scene.collection.children.link(c);collections[name]=c
    return collections[name]
def move(o,c):
    for old in list(o.users_collection):old.objects.unlink(o)
    coll(c).objects.link(o)
def xyz(p):return Vector((p[0]/1000,-p[2]/1000,p[1]/1000))
B=Matrix(reg['installed_mm_to_blender_m'])
def material(name,color,emission=False):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    if emission:
        n=m.node_tree.nodes.new('ShaderNodeEmission');n.inputs[0].default_value=(*color,1)
        m.node_tree.links.new(n.outputs[0],m.node_tree.nodes['Material Output'].inputs['Surface'])
    else:
        bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=.1;bs.inputs['Roughness'].default_value=.55
    return m

# Preserve exactly one full-resolution wall mesh in this deliberate self-contained snapshot.
bpy.ops.wm.obj_import(filepath=str(ROOT/'data/extracted/shower-hole-valve-polycam/10_14_2026.obj'),forward_axis='Y',up_axis='Z')
wall=[];raw=[]
for i,o in enumerate(list(bpy.context.selected_objects)):
    if o.type!='MESH':continue
    o.name=f'SCAN-WALL_FULL_{i}';o.matrix_world=Matrix(reg['raw_to_blender_m']);move(o,'00A_SOURCE_WALL_FULL')
    o['evidence_id']='SCAN-WALL';o['quality']='primary spatial reference; physical scale conditional';o['raw_mesh_preserved']=True;raw.append(o)
    proxy=o.copy();proxy.data=o.data.copy();proxy.name=f'WALL_DISPLAY_PROXY_{i}';coll('01_OBSERVED_WALL').objects.link(proxy);wall.append(proxy)
    bpy.context.view_layer.objects.active=proxy
    bpy.ops.object.select_all(action='DESELECT');proxy.select_set(True)
    dec=proxy.modifiers.new('Display reduction ONLY','DECIMATE');dec.ratio=.18;bpy.ops.object.modifier_apply(modifier=dec.name)
    proxy['approximation']='18% face display proxy; not used for fine coverage or numerical geometry checks'
    for index,source_mat in enumerate(list(proxy.data.materials)):
        if not source_mat:continue
        m=source_mat.copy();m.name='Proxy texture '+str(index);proxy.data.materials[index]=m
        tex=next((n for n in m.node_tree.nodes if n.type=='TEX_IMAGE'),None)
        if tex and tex.image:
            im=tex.image.copy();im.name='Display '+im.name
            factor=min(1,2048/max(im.size));im.scale(max(1,int(im.size[0]*factor)),max(1,int(im.size[1]*factor)));tex.image=im
        if tex:
            em=m.node_tree.nodes.new('ShaderNodeEmission');m.node_tree.links.new(tex.outputs['Color'],em.inputs[0]);m.node_tree.links.new(em.outputs[0],m.node_tree.nodes.get('Material Output').inputs['Surface'])
    print('Wall proxy faces',len(proxy.data.polygons),flush=True)

# Keep original component captures separate and unregistered, explicitly excluded by default.
for index,name in enumerate(['plates-side-1-polycam','plates-side-2-polycam']):
    bpy.ops.wm.obj_import(filepath=str(ROOT/'data/extracted'/name/'10_14_2026.obj'),forward_axis='Y',up_axis='Z')
    for o in list(bpy.context.selected_objects):
        if o.type!='MESH':continue
        o.name=f'SCAN-PLATE-{index+1}_RAW_UNREGISTERED';move(o,'00B_SECONDARY_SCANS_RAW')
        o['evidence_id']=f'SCAN-PLATE-{index+1}';o['registration']='NONE. Raw source coordinates, no physical scale asserted.';o['quality']='Severe warp and reflected surroundings; excluded from dimensional fit.'

objects={}
for p in cad['parts']:
    bpy.ops.wm.stl_import(filepath=str(ROOT/p['stl']),forward_axis='Y',up_axis='Z')
    o=bpy.context.object;o.name=p['id'];o.data.transform(B);o.location=xyz(p['location_mm'])
    name=p['collection']
    if p['id']=='GASKET-01':name='02B_FACTORY_GASKET'
    move(o,name);o.data.materials.clear();o.data.materials.append(material(p['id']+' material',p['color']))
    for k in ['id','evidence','status','tessellation_tolerance_mm']:o[k]=p[k]
    o['state']='proposed_provisional';o['CAD_source']=p['step'] or p['stl'];objects[p['id']]=o

red=material('Observed damage',(0.82,.12,.10),True);amber=material('Uncertain feature',(.95,.57,.05),True)
teal=material('Candidate outline',(.04,.68,.78),True);white=material('Nominal trim outline',(.94,.95,.91),True)
def line(name,points,mat,width=.0005,collection='06_DATUMS_AND_COVERAGE',closed=False):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=width;cu.bevel_resolution=1
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for v,p in zip(sp.points,points):v.co=(*p,1)
    sp.use_cyclic_u=closed;o=bpy.data.objects.new(name,cu);coll(collection).objects.link(o);o.data.materials.append(mat);o['display_only']=True;return o
for f in d['features']:
    if 'contour_mm' not in f:continue
    line(f['id']+' | '+f['name'],[xyz((p[0],p[1],65)) for p in f['contour_mm']],red if f['status']=='scan-derived' else amber,.00045,closed=f['geometry']=='polygon')
center=d['trim_center_mm']
for name,r,mat in [('NOMINAL_TRIM',d['nominal']['trim_diameter_mm']/2,white),('CUSTOM_DRAFT',d['candidate']['diameter_mm']/2,teal)]:
    line(name,[xyz((center[0]+r*math.cos(t*2*math.pi/256),center[1]+r*math.sin(t*2*math.pi/256),66)) for t in range(256)],mat,.0006,closed=True)
for id,p in reg['landmarks_installed_mm'].items():
    x,y,z=p['point_mm'];line(id+' cross X',[xyz((x-2,y,70)),xyz((x+2,y,70))],white)
    line(id+' cross Y',[xyz((x,y-2,70)),xyz((x,y+2,70))],white)
coll('USER_NOTES')

# Exploded duplicates share CAD mesh data and can never enter assembly exports.
exploded=[]
for id,o in objects.items():
    if id.startswith(('VALVE','STUD-')) and not id.endswith('NUT'):continue
    cp=o.copy();cp.data=o.data;cp.name='EXPLODED_ONLY__'+id;coll('08_EXPLODED_DISPLAY_ONLY').objects.link(cp)
    off=30 if id=='CUSTOM-01' or id=='NEW-SEAL-PATH' else 65 if id=='GASKET-01' else 100 if id=='PLATE-INNER' or id.endswith('NUT') else 150 if id=='TRIM-OUTER' else 205
    cp.location.y-=off/1000;cp['display_only']=True;cp['explosion_offset_mm']=off;exploded.append(cp)

def camera(name,loc,target,span):
    cd=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,cd);coll('07_CAMERAS_AND_LIGHTS').objects.link(o)
    o.location=xyz(loc);o.rotation_euler=(xyz(target)-o.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=span/1000;cd.clip_start=.001;cd.clip_end=20;return o
cams={
 'coverage':camera('CAM_01_Coverage',(center[0],center[1],900),(center[0],center[1],0),300),
 'overview':camera('CAM_00_Overview',(0,0,1000),(0,0,0),620),
 'assembled':camera('CAM_02_Assembled',(300,240,650),(0,40,20),350),
 'exploded':camera('CAM_03_Exploded',(470,300,700),(0,40,100),460),
 'inner_front':camera('CAM_04_Inner_front',(0,40,600),(0,40,0),210),
 'inner_back':camera('CAM_05_Inner_back',(0,40,-600),(0,40,0),210),
 'outer_front':camera('CAM_05B_Outer_front',(center[0],center[1],600),(center[0],center[1],0),230),
 'outer_back':camera('CAM_05C_Outer_back',(center[0],center[1],-600),(center[0],center[1],0),230),
 'gasket':camera('CAM_06_Gasket',(0,40,800),(0,40,0),260)
}
for loc,power,size in [((250,300,450),1.2,.5),((-300,150,200),.6,.5)]:
    ld=bpy.data.lights.new('Soft light','AREA');lo=bpy.data.objects.new('Soft light',ld);coll('07_CAMERAS_AND_LIGHTS').objects.link(lo);lo.location=xyz(loc);lo.rotation_euler=(xyz((0,40,0))-lo.location).to_track_quat('-Z','Y').to_euler();ld.energy=power;ld.shape='DISK';ld.size=size

def section(name,pts):
    p1,p2=Vector(pts[0]),Vector(pts[1]);delta=p2-p1;n=Vector((delta.y,-delta.x,0)).normalized()
    bn=Vector((n.x,-n.z,n.y));bp=xyz((p1.x,p1.y,0));collection='09_SECTION_'+name
    for o in wall+list(objects.values()):
        if o.type!='MESH':continue
        mesh=o.data.copy();mesh.transform(o.matrix_world)
        bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=bp,plane_no=bn,clear_outer=True,clear_inner=False,dist=1e-6)
        bm.to_mesh(mesh);bm.free();ob=bpy.data.objects.new('SECTION_ONLY_'+name+'_'+o.name,mesh);coll(collection).objects.link(ob);ob['display_only']=True
    mid=(p1+p2)/2;mid.z=35;loc=mid+n*600
    cams['section_'+name]=camera('CAM_SECTION_'+name,list(loc),list(mid),240)
    return collection
sec_controls=section('controls',d['controls_mm']);sec_studs=section('studs',d['studs_mm'])

# Restore only a dedicated user-authored collection, never generated fit-critical edits.
notes=OUT/'user_notes.blend'
if notes.exists():
    with bpy.data.libraries.load(str(notes),link=False) as (src,dst):dst.collections=[x for x in src.collections if x=='USER_NOTES']
    for c in dst.collections:
        if c:scene.collection.children.link(c)

layers={
 'Observed':['01_OBSERVED_WALL'],
 'Coverage':['01_OBSERVED_WALL','06_DATUMS_AND_COVERAGE'],
 'Assembled':['01_OBSERVED_WALL','02_INNER_AND_GASKET','02B_FACTORY_GASKET','03_OUTER_TRIM','04_CUSTOM_CANDIDATE','05_PROPOSED_MATERIALS'],
 'Exploded':['01_OBSERVED_WALL','08_EXPLODED_DISPLAY_ONLY'],
 'Inner':['02_INNER_AND_GASKET','02B_FACTORY_GASKET'],
 'Gasket':['01_OBSERVED_WALL','02B_FACTORY_GASKET','06_DATUMS_AND_COVERAGE'],
 'Section_controls':[sec_controls], 'Section_studs':[sec_studs],
 'Full_source':['00A_SOURCE_WALL_FULL'],
 'CAD_only':['01_OBSERVED_ENVELOPES','02_INNER_AND_GASKET','02B_FACTORY_GASKET','03_OUTER_TRIM','04_CUSTOM_CANDIDATE','05_PROPOSED_MATERIALS']}
default=scene.view_layers[0];default.name='Coverage'
for name,visible in layers.items():
    vl=default if name=='Coverage' else scene.view_layers.new(name)
    for c in vl.layer_collection.children:c.exclude=c.name not in visible+['07_CAMERAS_AND_LIGHTS','USER_NOTES']
    vl.use=False
def render(name,layer):
    for vl in scene.view_layers:vl.use=vl.name==layer
    bpy.context.window.view_layer=scene.view_layers[layer];scene.camera=cams[name]
    scene.render.filepath=str(VIEWS/(name+'.png'));bpy.ops.render.render(write_still=True)
for name,layer in [('coverage','Coverage'),('overview','Observed'),('assembled','Assembled'),('exploded','Exploded'),('inner_front','Inner'),('inner_back','Inner'),('outer_front','Assembled'),('outer_back','Assembled'),('gasket','Gasket'),('section_controls','Section_controls'),('section_studs','Section_studs')]:
    hidden=[]
    if name.startswith('inner_'):hidden=[o for id,o in objects.items() if id.endswith('NUT')]
    if name.startswith('outer_'):hidden=wall+[o for id,o in objects.items() if id!='TRIM-OUTER']
    for o in hidden:o.hide_render=True
    render(name,layer)
    for o in hidden:o.hide_render=False

# Projection matrices let the worksheet attach contacts to the actual rendered model.
from bpy_extras.object_utils import world_to_camera_view
projection={}
for name,cam in cams.items():
    projection[name]={'world_to_camera': [list(row) for row in cam.matrix_world.inverted()], 'ortho_scale_m':cam.data.ortho_scale,
                      'resolution':[scene.render.resolution_x,scene.render.resolution_y], 'coordinate_mapping':'installed mm -> Blender m (X,-Z,Y)/1000'}
(ROOT/'deliverables/current/review/view_geometry.json').write_text(json.dumps(projection,indent=2)+'\n')

# Export only installed-pose display proxy and CAD meshes. Blender glTF conversion is (X,Z,-Y).
vl=scene.view_layers.new('EXPORT_TEMP')
for c in vl.layer_collection.children:c.exclude=c.name not in layers['CAD_only']+['01_OBSERVED_WALL']
bpy.context.window.view_layer=vl
bpy.ops.object.select_all(action='DESELECT')
for o in wall+list(objects.values()):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'deliverables/current/review/installation_DRAFT.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
for o in objects.values():o.select_set(False)
bpy.ops.export_scene.gltf(filepath=str(OUT/'wall_display_proxy.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
bpy.context.window.view_layer=scene.view_layers['Coverage'];scene.view_layers.remove(vl)
for vl in scene.view_layers:vl.use=vl.name=='Coverage'
scene.camera=cams['coverage']
scene['revision']=d['revision'];scene['readiness']='DRAFT / NOT FOR FABRICATION. No physical fit.';scene['scale']=reg['scale_status']
scene['instructions']='View Layers select Observed/Coverage/Assembled/Exploded/Inner/Sections. Select a named camera and View > Cameras > Set Active Object as Camera. See local HTML for easy review.'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.overlay.show_overlays=False;area.spaces.active.shading.type='MATERIAL'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f"installation_{d['revision']}_DRAFT.blend"),compress=True)
# Reopen is the verification, not merely a successful save call.
bpy.ops.wm.open_mainfile(filepath=str(OUT/f"installation_{d['revision']}_DRAFT.blend"))
assert bpy.data.objects.get('CUSTOM-01') and bpy.data.objects.get('PLATE-INNER')
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()]
assert not missing,missing
report={'status':'PASS','version':bpy.app.version_string,'revision':d['revision'],'saved_reopened':True,'missing_images':missing,'CAD_custom_part_source':'data/derived/cad/CUSTOM-01.stl','views_rendered':list(cams),'source_wall_mesh_copies':1,'notes':'Decimated display proxy plus one full source wall; source textures packed. Exploded/section copies display-only.'}
(OUT/'scene_check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
