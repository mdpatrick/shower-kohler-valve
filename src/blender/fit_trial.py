"""FT01: observed attached scan, proposed paired appearance and exploded order."""
from pathlib import Path
import json,math,hashlib,sys
import bpy
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2]
CONFIG=json.loads((ROOT/'canon/fit_trial_design.json').read_text())
OUT=ROOT/CONFIG.get('output_directory','deliverables/current/fabrication/fit-trial')
R=json.loads((ROOT/'data/derived/resolved.json').read_text())
A=json.loads((OUT/'design_report.json').read_text())
sys.path.insert(0,str(ROOT))
from src.fabrication.fit_trial_spec import values,expand
D=A['design'];V=values(D,R,A);foam_spec=D['foam']
assert D==json.loads((ROOT/'canon/fit_trial_design.json').read_text()), 'Rebuild analysis first'
F=json.loads((ROOT/'data/derived/fabrication_F005/analysis.json').read_text())
B=Matrix(((.001,0,0,0),(0,0,-.001,0),(0,.001,0,0),(0,0,0,1)))
bpy.ops.wm.read_factory_settings(use_empty=True)
def xyz(p):return Vector((p[0]/1000,-p[2]/1000,p[1]/1000))
def mat(name,col,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True
    p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*col,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.34 if metal else .75
    return m
steel=mat('Proposed brushed stainless; approximate finish',(.44,.49,.51),.85)
nickel=mat('Kohler BN approximation',(.47,.43,.36),.85)
foam=mat('Factory foam; approximate free section',(.10,.11,.12))
def setup(s,name):
    s.name=name;s.unit_settings.system='METRIC';s.unit_settings.length_unit='MILLIMETERS'
    s.render.engine='CYCLES';s.cycles.samples=20;s.cycles.use_denoising=True;s.cycles.device='CPU'
    s.render.threads_mode='FIXED';s.render.threads=2
    s.render.resolution_x=1000;s.render.resolution_y=1150;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
    s.world=bpy.data.worlds.new(name+' world');s.world.use_nodes=True
    s.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.25,.28,1)
    s.world.node_tree.nodes['Background'].inputs[1].default_value=.4
def camera(s,loc,target,span):
    c=bpy.data.cameras.new(s.name+' camera');o=bpy.data.objects.new(c.name,c);s.collection.objects.link(o)
    o.location=xyz(loc);o.rotation_euler=(xyz(target)-o.location).to_track_quat('-Z','Y').to_euler()
    c.type='ORTHO';c.ortho_scale=span/1000;c.clip_start=.001;c.clip_end=10;s.camera=o
    return o
def lights(s):
    for pos,power,size in [((250,380,500),4,.42),((-280,20,300),2,.40),((0,-280,400),2,.45)]:
        l=bpy.data.lights.new('Soft light','AREA');o=bpy.data.objects.new('Soft light',l);s.collection.objects.link(o)
        l.energy=power;l.shape='DISK';l.size=size;o.location=xyz(pos)
        o.rotation_euler=(xyz((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
def stl(s,path,name,pos,material):
    bpy.context.window.scene=s
    bpy.ops.wm.stl_import(filepath=str(path),forward_axis='Y',up_axis='Z');o=bpy.context.object
    o.name=name;o.data.transform(B);o.location=xyz(pos);o.data.materials.append(material)
    o['source']=str(path.relative_to(ROOT));return o

pair=bpy.context.scene;setup(pair,D['revision']+' | proposed appearance')
with bpy.data.libraries.load(str(ROOT/'deliverables/current/fabrication/F005/paired_escutcheons_F005_DRAFT.blend'),link=False) as (available,data):
    data.collections=['F005 Appearance wall only']
wall=data.collections[0];pair.collection.children.link(wall)
pair['limits']='Appearance only. Captured hardware omitted from a separate wall derivative. No successful assembly or seal is asserted.'
custom=[];official=[]
centers={'MAIN':R['trim_center_mm'],'DIV':R['diverter_tip_mm'][:2]}
angle=math.radians(R['trim_in_plane_rotation_deg'])
inner_center=centers['MAIN']
if A.get('current_placement'):
    tf=A['current_placement'];pose=tf['cover_to_installed_xy_up'];centers['MAIN']=pose['translation_mm']
    q=pose['row_rotation'];angle=math.atan2(q[0][1],q[0][0])
    it=tf['inner_outline_to_cover_xy_up']['translation_mm'];inner_center=[it[0]*q[0][i]+it[1]*q[1][i]+centers['MAIN'][i] for i in range(2)]
for kind in ['MAIN','DIV']:
    p=next(p for p in A['parts'] if p['kind']==kind and p['stock']==V['stock'])
    o=stl(pair,OUT/p['files']['stl'],p['id'],(*centers[kind],1),steel)
    if kind=='MAIN':o.rotation_euler[1]=-angle
    o['CAD_dimensions_mm']=[p['diameter_mm'],p['diameter_mm'],p['thickness_mm']]
    o['bedding_1mm_is_illustration_only']=True;custom.append(o)
for p in F['manufacturer_components']:
    main=p['model']=='T14489-4';c=centers['MAIN' if main else 'DIV']
    o=stl(pair,ROOT/p['stl'],f'Kohler official exterior {p["model"]} {p["index"]}',(*c,1+V['thickness']),nickel)
    if main:o.rotation_euler[1]=-angle
    for f in o.data.polygons:f.use_smooth=True
    o['limits']='Manufacturer exterior form only. Hidden mating geometry and BN color not certified.'
    official.append((o,p,main))
lights(pair);cam=camera(pair,(0,-35,850),(0,-35,0),410)
pair.render.filepath=str(OUT/'paired_front.png');bpy.ops.render.render(write_still=True)
cam.location=xyz((220,30,750));cam.rotation_euler=(xyz((0,-35,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.455
pair.render.filepath=str(OUT/'paired_oblique.png');bpy.ops.render.render(write_still=True)
cam.location=xyz((0,-35,850));cam.rotation_euler=(xyz((0,-35,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.410

exp=bpy.data.scenes.new(D['revision']+' | exploded order');bpy.context.window.scene=exp;setup(exp,exp.name)
exp.collection.children.link(wall)
for o in custom:
    cp=o.copy();exp.collection.objects.link(cp);cp.name='Exploded '+o.name;cp.location.y-=.035
for o,p,main in official:
    cp=o.copy();exp.collection.objects.link(cp);cp.name='Exploded '+o.name
    idx=p['index'];offset=(125 if idx==0 else 175 if idx in [3,4] else 215) if main else (90 if idx==0 else 145 if idx==1 else 180)
    cp.location.y-=offset/1000;cp['display_offset_mm']=offset
innerpart=next(p for p in F['parts'] if p['id']=='REF-INNER')
innerpath=OUT/'reference/R006_FACTORY_INNER_REFERENCE.stl' if (OUT/'reference/R006_FACTORY_INNER_REFERENCE.stl').exists() else ROOT/'deliverables/current/fabrication/F005'/innerpart['stl']
ip=stl(exp,innerpath,'Factory inner plate reference; local form approximate',(*inner_center,85),steel)
ip.rotation_euler[1]=-angle
ip['limits']='Measured overall envelope, local form and lower opening approximate; use observed scan scene for actual current assembly.'
# Edge-flush foam footprint, correct to latest user description; hidden shape remains a scenario.
cu=bpy.data.curves.new('Edge-flush factory foam footprint','CURVE');cu.dimensions='2D';cu.fill_mode='BOTH';cu.extrude=V['foam_depth']/2000
fw,fh,fr,band=V['inner_w'],V['inner_h'],foam_spec['outer_corner_radius_mm'],V['foam_width']
for w,h,r,reverse in [(fw,fh,fr,False),(fw-2*band,fh-2*band,fr-band,True)]:
    points=[]
    for x,y,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for j in range(33):
            a=math.radians(start+j*90/32);points.append((x+r*math.cos(a),y+r*math.sin(a)))
    if reverse:points.reverse()
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for v,p in zip(sp.points,points):v.co=(p[0]/1000,p[1]/1000,0,1)
    sp.use_cyclic_u=True
o=bpy.data.objects.new('Foam attached to factory inner plate; separated for diagram',cu);exp.collection.objects.link(o)
o.rotation_euler[0]=math.pi/2;o.location=xyz((*inner_center,65));o.rotation_euler[1]=-angle;cu.materials.append(foam)
o['limits']=f'Approximate {band:g}x{V["foam_depth"]:g} section; outer R{fr:g} is assumed. Not foam in wall cavity.'
lights(exp);camera(exp,(520,160,800),(0,-25,90),520)
exp['limits']='Exploded offsets show order only. Foam belongs to inner plate, not wall cavity. Inner local formed geometry is approximate.'
exp.render.filepath=str(OUT/'exploded.png');bpy.ops.render.render(write_still=True)

obs=bpy.data.scenes.new('OBSERVED | inner plate attached');bpy.context.window.scene=obs
setup(obs,obs.name);obs.render.engine='BLENDER_WORKBENCH';obs.display.shading.color_type='TEXTURE'
obs.display.shading.light='STUDIO';obs.display.shading.show_shadows=False
asspath=OUT/'attached_scan_assessment.json'
if not asspath.exists():asspath=ROOT/'deliverables/current/fabrication/fit-trial/attached_scan_assessment.json'
ass=json.loads(asspath.read_text());T=Matrix(ass['raw_to_local_diagnostic_mm'])
bpy.ops.wm.obj_import(filepath=str(ROOT/'data/extracted/polycam-inner-plate-attached/10_15_2026.obj'),forward_axis='Y',up_axis='Z')
scan=bpy.context.object;scan.name='SCAN-INNER-ATTACHED | preserved original geometry'
scan.matrix_world=B@T;scan['source_sha256']=ass['source_sha256'];scan['frame']='Separate wall-normal local diagnostic, 80mm scale calibration; not primary scan registration'
camera(obs,(0,40,800),(0,40,0),230)
obs['limits']='Actual attached state, no forced alignment. Hubs and reflective metal are distorted. Hidden engagement and water performance unknown.'
notes=bpy.data.texts.new('START HERE - '+D['revision'])
notes.write(expand('[[revision]] quote and dry-fit package. Permanent installation not released.\n'
 'Scenes: proposed appearance on primary travertine derivative; exploded order; actual new attached scan.\n'
 'Custom parts derive from validated CAD. Main [[main_od]] / diverter [[div_od]]; vertical capsule [[aperture_w:.2f]] x [[aperture_h:.2f]] R[[aperture_r]]; thickness [[thickness:.3f]] mm.\n'
 'The full handles attach from the front. No integral bolt tabs; leave placement adjustable.\n'
 'Foam is attached to the factory inner plate and meets its edge. Exploded foam is diagrammatic, never cavity fill.\n'
 'Observed stems sit high within captured hubs. Physical handle engagement must be checked before tightening or sealing.\n'
 'No scene demonstrates a completed water seal. Read the evergreen handoff alongside this file.\n',V))
bpy.context.window.scene=pair
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.clip_start=.001
bpy.ops.file.pack_all()
dest=OUT/('escutcheon_fit_trial_'+D['revision']+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(dest))
bpy.ops.wm.open_mainfile(filepath=str(dest))
assert len(bpy.data.scenes)==3
assert len(bpy.data.objects['SCAN-INNER-ATTACHED | preserved original geometry'].data.vertices)==333573
checks=[]
for p in A['parts']:
    if p['stock']!=V['stock'] or p['kind']=='DIV-FALLBACK':continue
    o=bpy.data.objects[p['id']];bounds=[max(v.co[k] for v in o.data.vertices)-min(v.co[k] for v in o.data.vertices) for k in range(3)]
    assert max(abs(a-b) for a,b in zip(bounds,[p['diameter_mm']/1000,p['thickness_mm']/1000,p['diameter_mm']/1000]))<.00006
    checks.append(p['id'])
(OUT/'blender_check.json').write_text(json.dumps({'saved_reopened':True,'scenes':3,'custom_dimensions_verified':checks,'source_vertex_count':333573,'original_scan_sha256':ass['source_sha256'],'physical_fit':'UNPERFORMED','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
print(D['revision']+' three-scene Blender file saved/reopened and dimensions verified.')
