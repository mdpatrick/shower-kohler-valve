"""Small AP01 inspection workspace: exact new CAD, cropped evidence, nominal trim.

No background application state is touched. This file contains no fabricated rear
construction and does not modify the full original scan or previous Blender files.
"""
from pathlib import Path
import bpy
import hashlib
import json
import math
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'deliverables/current/fabrication/aperture-access'
A=json.loads((OUT/'analysis.json').read_text())
R=json.loads((ROOT/'data/derived/resolved.json').read_text())
C=R['inner_center_mm']
B=Matrix(((.001,0,0,0),(0,0,-.001,0),(0,.001,0,0),(0,0,0,1)))
bpy.ops.wm.read_factory_settings(use_empty=True)


def xyz(p):
    return Vector((p[0]/1000,-p[2]/1000,p[1]/1000))


def material(name,color,metallic=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metallic;p.inputs['Roughness'].default_value=.45
    return m


steel=material('Custom CAD | teal diagnostic',(0.13,.45,.52),.35)
gray=material('Captured surface | no inferred rear',(.43,.46,.48))
gold=material('Foam footprint only | edge flush',(.72,.40,.1))
purple=material('Projected factory-opening footprint',(.43,.20,.64))
silver=material('Official exterior | nominal',(.65,.68,.71),.55)
ink=material('Labels',(.025,.06,.075))
tip=material('Scan U point',(.75,.24,.10))


def setup(scene):
    bpy.context.window.scene=scene
    scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS'
    scene.render.engine='BLENDER_WORKBENCH'
    scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
    scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=True
    scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD'
    scene.render.threads_mode='FIXED';scene.render.threads=6
    scene.render.resolution_x=1200;scene.render.resolution_y=1250;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard'
    world=bpy.data.worlds.new(scene.name+' World');world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.86,.9,.92,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.6;world.color=(.86,.9,.92);scene.world=world
    for pos,power in [((150,250,380),55),((-220,40,240),30)]:
        d=bpy.data.lights.new('Softbox','AREA');o=bpy.data.objects.new('Softbox',d);scene.collection.objects.link(o)
        o.location=xyz(pos);o.rotation_euler=(xyz((*C,0))-o.location).to_track_quat('-Z','Y').to_euler()
        d.energy=power;d.shape='DISK';d.size=.3


def stl(path,name,mat,position=(0,0,0)):
    bpy.ops.wm.stl_import(filepath=str(path),forward_axis='Y',up_axis='Z')
    o=bpy.context.object;o.name=name;o.data.transform(B);o.location=xyz(position)
    o.data.materials.clear();o.data.materials.append(mat)
    o['source']=str(path.relative_to(ROOT));o['source_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    return o


def curve(name,points,mat,width=.4):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=width/1000;cu.bevel_resolution=2
    s=cu.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*xyz(co),1)
    obj=bpy.data.objects.new(name,cu);bpy.context.scene.collection.objects.link(obj);obj.data.materials.append(mat)
    return obj


def label(text,pos,size=4):
    cu=bpy.data.curves.new(text,'FONT');cu.body=text;cu.size=size/1000
    obj=bpy.data.objects.new(text,cu);bpy.context.scene.collection.objects.link(obj)
    obj.location=xyz(pos);obj.rotation_euler=(math.pi/2,0,0);obj.data.materials.append(ink)
    return obj


def camera(scene,name,loc,target,span):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);scene.collection.objects.link(o)
    o.location=xyz(loc);o.rotation_euler=(xyz(target)-o.location).to_track_quat('-Z','Y').to_euler()
    d.type='ORTHO';d.ortho_scale=span/1000;d.clip_start=.001;d.clip_end=20;scene.camera=o
    return o


front=bpy.context.scene;front.name='AP01 | upright access and captured hardware';setup(front)
part=next(p for p in A['CAD'] if p['outer_diameter_mm']==220 and p['thickness_mm']==1.524)
o=stl(OUT/part['files']['stl'],'AP01 C1 | exact CAD 220 x 1.524',steel,(*C,1))
o['CAD_frame']='local X right Y up Z out; rear face Z0; installed (center X,Y, Z1)'
o['not_selected']=True
o['STEP_sha256']=part['sha256']['step']
source=stl(ROOT/'build/aperture_access/captured_forward_display.stl','Primary scan | forward display crop, unchanged coordinates',gray)
source['limits']='Subset of original faces by bounding region, not a complete volume. Full scan stays in REAR01/R005 workspace.'
for op,label_text in zip(R['inner_control_openings'],['L | lower opening diameter assumed','U | measured inner opening diameter 48.46']):
    cx=C[0]+op['center_local_mm'][0];cy=C[1]+op['center_local_mm'][1];rad=op['diameter_mm']/2
    points=[(cx+rad*math.cos(i*2*math.pi/160),cy+rad*math.sin(i*2*math.pi/160),58) for i in range(161)]
    o=curve(label_text,points,purple,.45);o['projection_overlay_only']=True
    label(label_text[:1],(cx+3,cy+3,60),5)
for p,name in zip(R['studs_mm'],['SW','NE']):label(name,(p[0]+4,p[1]+4,60),4)
# Same assumed rounded-rectangle corner profile, with edge-flush foam footprint.
for w,h,rad,name in [(130.35,165.1,40,'metal / foam outer edge'),(118.35,153.1,34,'foam nominal inner edge')]:
    pts=[]
    for cx,cy,start in [(w/2-rad,h/2-rad,0),(-w/2+rad,h/2-rad,90),(-w/2+rad,-h/2+rad,180),(w/2-rad,-h/2+rad,270)]:
        for i in range(41):
            a=math.radians(start+i*90/40)
            pts.append((C[0]+cx+rad*math.cos(a),C[1]+cy+rad*math.sin(a),57))
    pts.append(pts[0]);o=curve('Projected '+name,pts,gold,.45);o['projection_overlay_only']=True
label('AP01 | Upright opening / original captured hardware',(-120,171,60),5)
label('Purple: opening footprints. Gold: edge-flush foam footprint.',(-120,-85,60),3.5)
label('Overlays are projected; foam and inner plate are currently removed.',(-120,-92,60),3.5)
label('DRAFT: physical handle engagement and sealing remain unverified.',(-120,-99,60),3.5)
camera(front,'Front access map',(*C,650),(*C,0),285)
front['purpose']='Planar access study. Overlay Z offsets are diagram-only, never installed positions.'
front.render.filepath=str(OUT/'blender_access_front.png');bpy.ops.render.render(write_still=True)

nom=bpy.data.scenes.new('AP01 | nominal exterior and fixed scan tips');setup(nom)
stl(OUT/part['files']['stl'],'AP01 C1 | exact custom backing',steel,(*C,1))
for idx in range(7):
    path=ROOT/f'data/derived/fabrication_F005/KOHLER-T14489-4-{idx}.stl'
    obj=stl(path,'Official T14489-4 exterior '+str(idx),silver,(*C,2.524))
    obj['limitation']='Nominal exterior only. Hidden mating details, inner plate, gasket and adapters not represented.'
for p,name in zip(R['controls_mm'],['L','U']):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.001,location=xyz(p))
    ob=bpy.context.object;ob.name='Original scan '+name+' tip';ob.data.materials.append(tip)
    ob['point_installed_mm']=p
nom['purpose']='Inspect front-installed handle envelopes and depth. Not a validated assembled fit.'
nom['fixed_scan_points']='U/L positions unchanged. No manufacturer mesh movement is proof of attachment.'
nom['omitted_required_components']='Factory inner plate/foam, adapters, nuts and exact mating surfaces. Omission is display-only.'
camera(nom,'Oblique upper interface',(360,170,400),(0,40,35),290)

# Keep all four CAD alternatives available separately without moving their master coordinates.
alts=bpy.data.scenes.new('AP01 | four separate CAD alternatives');setup(alts)
for i,p in enumerate(A['CAD']):
    o=stl(OUT/p['files']['stl'],p['id'],steel,((i%2)*260,(i//2)*260,0))
    o['display_layout_offset_only']=True;o['STEP_sha256']=p['sha256']['step']
    label(f'OD {p["outer_diameter_mm"]:g} / t {p["thickness_mm"]:g}',((i%2)*260-105,(i//2)*260+118,5),7)
camera(alts,'CAD alternatives',(130,130,950),(130,130,0),560)

bpy.context.window.scene=front
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.clip_start=.001
readme=bpy.data.texts.new('READ AP01 FIRST')
readme.write('AP01 upright access study. Recommended next dry-fit candidate, not a released design.\n'
             'Front scene: exact CAD and cropped original scan, with elevated diagram overlays.\n'
             'Exterior scene: official nominal handles and unchanged scan tip points; hidden interfaces omitted.\n'
             'Foam is attached to the removed inner plate and meets its edge, per user. No installed foam is modeled.\n'
             'Wood contact is user-confirmed; conditional wood relief is preferred, dimensions unresolved.\n'
             'Open index.html / analysis.json in this folder for source limits, full-size templates and checks.\n')
dest=OUT/'aperture_access_AP01_DRAFT.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
bpy.ops.wm.open_mainfile(filepath=str(dest))
expected={'AP01 | upright access and captured hardware','AP01 | nominal exterior and fixed scan tips','AP01 | four separate CAD alternatives'}
assert expected.issubset(bpy.data.scenes.keys())
for p in A['CAD']:
    ob=bpy.data.objects[p['id']]
    assert ob['STEP_sha256']==p['sha256']['step']
    assert max(abs(a-b) for a,b in zip(ob.dimensions,[p['outer_diameter_mm']/1000,p['thickness_mm']/1000,p['outer_diameter_mm']/1000]))<.00006
(OUT/'blender_validation.json').write_text(json.dumps(dict(status='PASS',saved_reopened=True,scenes=sorted(expected),
    CAD_dimensions_checked=4,source_sha256=hashlib.sha256((ROOT/'src/blender/aperture_access.py').read_bytes()).hexdigest(),
    limitations='Nominal exterior and diagram overlays do not prove physical engagement. No full source scan modified.'),indent=2)+'\n')
print('AP01 Blender saved, reopened and all four CAD part dimensions checked.')
