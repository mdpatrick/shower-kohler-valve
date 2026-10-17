"""TR02 camera clips from real CAD, both retained captures, and official exterior CAD."""
from pathlib import Path
import bpy,json,math,sys
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[2];BUILD=ROOT/'build/FT02/tab_rethink';OUT=ROOT/'deliverables/current/fabrication/FT02/tab-rethink'
cfg=json.loads((BUILD/'analysis.json').read_text());B=Matrix(((.001,0,0,0),(0,0,-.001,0),(0,.001,0,0),(0,0,0,1)))
preview='preview' in sys.argv
only=sys.argv[sys.argv.index('--only')+1].split(',') if '--only' in sys.argv else None
def xyz(p):return Vector((p[0]/1000,-p[2]/1000,p[1]/1000))
def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
def scene(name):
    s=bpy.data.scenes.new(name);bpy.context.window.scene=s
    s.unit_settings.system='METRIC';s.unit_settings.length_unit='MILLIMETERS'
    s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='TEXTURE'
    s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH'
    s.display.shading.curvature_ridge_factor=1.1;s.display.shading.show_object_outline=False
    s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new(name+' world');s.world.color=(.86,.90,.92)
    s.display.render_aa='8';s.render.resolution_x=1200;s.render.resolution_y=700;s.render.resolution_percentage=100
    s.render.threads_mode='FIXED';s.render.threads=4;s.render.image_settings.file_format='PNG';s.render.fps=6
    s.view_settings.view_transform='Standard';s.frame_start=1;s.frame_end=36
    ca=bpy.data.cameras.new(name+' camera');cam=bpy.data.objects.new(ca.name,ca);s.collection.objects.link(cam);s.camera=cam
    ca.type='ORTHO';ca.clip_start=.0001;ca.clip_end=20
    return s
def aim(s,eye,target,vertical):
    c=s.camera;c.location=xyz(eye);c.rotation_euler=(xyz(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=vertical*1200/700/1000
def stl(s,path,name,mat):
    bpy.context.window.scene=s;bpy.ops.wm.stl_import(filepath=str(ROOT/path),forward_axis='Y',up_axis='Z')
    ob=bpy.context.object;ob.name=name;ob.data.transform(B);ob.data.materials.append(mat);ob['CAD_source']=path
    return ob
def asset(s,name,tag=None):
    ob=stl(s,cfg['assets'][name]['path'],tag or name,blue)
    ob.data.materials.append(amber)
    for f in ob.data.polygons:
        x=f.center.x*1000;y=f.center.z*1000
        if x*x+max(0,abs(y)-17.375)**2<58.175**2-.01:f.material_index=1
    return ob
def scan(s,src,transform,name):
    bpy.context.window.scene=s;bpy.ops.wm.obj_import(filepath=str(ROOT/src),forward_axis='Y',up_axis='Z')
    obs=list(bpy.context.selected_objects)
    for ob in obs:ob.matrix_world=B@Matrix(transform);ob.name=name;ob['source']=src;ob['original_transform_unchanged']=True
    return obs
def labels(s,points):
    bpy.context.view_layer.update();result=[]
    for text,p in points:
        q=world_to_camera_view(s,s.camera,xyz(p));result.append({'text':text,'pixel':[q.x*1200,(1-q.y)*700]})
    return result
bpy.ops.wm.read_factory_settings(use_empty=True)
blue=material('Custom backing',(.08,.47,.61));amber=material('Added interior tabs / land',(.96,.59,.15));silver=material('Factory exterior reference',(.50,.52,.53));purple=material('Factory inner plate reference',(.60,.47,.65))
scenes={};objects={};labelpoints={}
s=scene('TR02 | longer tabs, fixed outline');scenes['design']=s
old=asset(s,'previous_tabs','Old 7 mm tab example');new=asset(s,'longer_tabs','New longer tabs with 18 x 10 slots')
old.location=xyz((-128,0,0));new.location=xyz((128,0,0));objects['design']=[old,new]
labelpoints['design']=[('Earlier tabs',(-128,115,0)),('Longer tabs + adjustment slots',(128,115,0))]

s=scene('TR02 | original captured installation');scenes['primary']=s
reg=json.loads((ROOT/'data/derived/registration.json').read_text())
primary_objects=scan(s,'data/extracted/shower-hole-valve-polycam/10_14_2026.obj',reg['raw_to_installed_mm'],'PRIMARY original capture')
ob=asset(s,'inward_2','Longer tabs with 2 mm inward support in prior working pose')
pose=cfg['plate_pose'];Q=pose['row_rotation'];theta=math.atan2(Q[0][1],Q[0][0]);ob.rotation_euler[1]=-theta;ob.location=xyz((*pose['translation_mm'],1))
objects['primary']=[ob];labelpoints['primary']=[(k,tuple(p)) for k,p in cfg['original_fit_points_mm'].items()]

s=scene('TR02 | original scan without overlays');scenes['primary_bare']=s
for source in primary_objects:
    cp=source.copy();s.collection.objects.link(cp)
objects['primary_bare']=[];labelpoints['primary_bare']=labelpoints['primary']
for key,point in [('rod_A',(53,63,14)),('rod_B',(-47,19,14))]:
    s=scene('TR02 | '+key+' close view');scenes[key]=s
    for source in primary_objects+[objects['primary'][0]]:
        cp=source.copy();s.collection.objects.link(cp)
    objects[key]=[];labelpoints[key]=[]

s=scene('TR02 | actual inner plate attached');scenes['attached']=s
ass=json.loads((ROOT/'deliverables/current/fabrication/fit-trial/attached_scan_assessment.json').read_text())
scan(s,'data/extracted/polycam-inner-plate-attached/10_15_2026.obj',ass['raw_to_local_diagnostic_mm'],'ATTACHED original capture')
objects['attached']=[];labelpoints['attached']=[(k,tuple(p)) for k,p in cfg['attached_local_points_mm'].items()]

s=scene('TR02 | factory handles enter from front');scenes['factory']=s
plate=asset(s,'inward_2','2 mm inward support study');objects['factory']=[plate]
inner='deliverables/current/fabrication/FT02/reference/R006_FACTORY_INNER_REFERENCE.stl'
if (ROOT/inner).exists():
    ob=stl(s,inner,'Factory inner plate: measured outline, approximate local form',purple);ob.location=xyz((0,-.23,7.5));objects['factory'].append(ob)
fab=json.loads((ROOT/'data/derived/fabrication_F005/analysis.json').read_text())
for item in fab['manufacturer_components']:
    if item['model']!='T14489-4' or item['index']==0:continue
    ob=stl(s,item['stl'],f'Official Kohler exterior {item["index"]}',silver);ob.location=xyz((0,0,1.5));ob['scope']='Official exterior only; hidden mating details unknown'
    objects['factory'].append(ob)
labelpoints['factory']=[('Custom backing at wall',(75,0,1)),('Factory inner plate',(48,-10,14)),('Handles attach from front',(0,40,92))]

s=scene('TR02 | added inward support');scenes['narrow']=s
base=asset(s,'longer_tabs','Original opening with longer tabs');n1=asset(s,'inward_1','1 mm added inward support');n2=asset(s,'inward_2','2 mm added inward support')
for ob,x in [(base,-240),(n1,0),(n2,240)]:ob.location=xyz((x,0,0))
objects['narrow']=[base,n1,n2]
labelpoints['narrow']=[('Original opening',(-240,118,0)),('+1 mm inward',(0,118,0)),('+2 mm inward',(240,118,0))]

formpath='deliverables/current/fabrication/FT02/REPAIR_FORM_TRIAL/RF01_MAIN_REMOVABLE_FORM_PETG.stl'
s=scene('RF01 | actual temporary form front and rear');scenes['formtool']=s
formfront=stl(s,formpath,'RF01 one-piece tool front view',blue)
formback=stl(s,formpath,'RF01 same one-piece tool rear view',blue)
for formob in [formfront,formback]:
    formob.data.materials.append(amber)
    for face in formob.data.polygons:
        if face.center.y>0:face.material_index=1
formfront.location=xyz((-132,0,0));formback.location=xyz((132,0,0));formback.rotation_euler.z=math.pi
objects['formtool']=[formfront,formback]
labelpoints['formtool']=[('Shower-facing side',(-132,133,0)),('Wall-facing side + collar',(132,133,0))]

s=scene('RF01 | exploded placement and withdrawal');scenes['formplace']=s
for source in primary_objects:
    cp=source.copy();s.collection.objects.link(cp)
formmoving=stl(s,formpath,'RF01 temporary tool - illustrative motion',blue)
formmoving.data.materials.append(amber)
for face in formmoving.data.polygons:
    if face.center.y>0:face.material_index=1
formmoving.rotation_euler[1]=-theta
formmoving['scope']='Source tool CAD in prior approximate working pose. Full panel seating and brace reaction are not established.'
objects['formplace']=[formmoving];labelpoints['formplace']=[]

def state(name,i):
    s=scenes[name];bpy.context.window.scene=s;s.frame_set(i);u=(i-1)/35
    if name=='design':aim(s,(70*(1-u),45*(1-u),650),(0,0,0),295)
    elif name in ['primary','primary_bare']:
        aim(s,(60-60*u,60,500),(4,40,12),252)
    elif name=='attached':aim(s,(-55+55*u,60,500),(1,40,10),252)
    elif name.startswith('rod_'):
        x,y,z=(53,63,14) if name=='rod_A' else (-47,19,14)
        aim(s,(x+22*(1-u),y+15*(1-u),z+100),(x,y,z),45)
    elif name=='factory':aim(s,(270-100*u,65,215),(0,0,40),250)
    elif name=='formtool':aim(s,(40*(1-u),270-60*u,600),(0,0,0),335)
    elif name=='formplace':
        offset=80*(1-u/.35) if u<.35 else (0 if u<.60 else 80*(u-.60)/.40)
        formmoving.location=xyz((*pose['translation_mm'],offset))
        aim(s,(300,75,340),(4,40,25),320)
    else:aim(s,(0,0,700),(0,0,0),465)
    for ob in objects[name]:
        ob.keyframe_insert('location',frame=i);ob.keyframe_insert('rotation_euler',frame=i)
    s.camera.keyframe_insert('location',frame=i);s.camera.keyframe_insert('rotation_euler',frame=i);s.camera.data.keyframe_insert('ortho_scale',frame=i)
    return labels(s,labelpoints[name])

for name,s in scenes.items():
    folder=BUILD/'renders'/name;folder.mkdir(parents=True,exist_ok=True)
    for i in range(1,37):state(name,i)
    if only and name not in only:continue
    for i in ([1,36] if preview else range(1,37)):
        labs=state(name,i);(folder/f'{i:03d}.json').write_text(json.dumps(labs))
        s.render.filepath=str(folder/f'{i:03d}.png');bpy.ops.render.render(write_still=True)
    print('Completed camera clip '+name,flush=True)
notes=bpy.data.texts.new('READ FIRST - TR02 narrated study')
notes.write('Adding tabs does NOT shift the foam or backing. Longer inward tabs and limited aperture insets are separate studies.\n'
 'Two independent source captures retain their recorded transforms in separate scenes. No global registration is claimed.\n'
 'Factory handle exterior comes from Kohler CAD; inner formed details remain approximate and hidden connections are not certified.\n'
 'RF01 uses the existing actual one-piece tool STL. It is optional, temporary, and fully removed. Its placement animation does not establish full face seating, support, release, or waterproofing.\n'
 'Read analysis.json and the narrated video. These are explanatory, not new released order files.\n')
bpy.context.window.scene=scenes['design'];state('design',36)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.color_type='TEXTURE'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'TR02_tabs_scans_and_handles.blend'),compress=True)
print('Saved separate study with both source captures.',flush=True)
