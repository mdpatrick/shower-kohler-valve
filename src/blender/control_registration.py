"""Lightweight ALIGN02 scene states. Do not load or change the GUI workspace."""
from pathlib import Path
import json
import math
import hashlib
import bpy
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'deliverables/current/fabrication/control-registration'
R=json.loads((ROOT/'data/derived/resolved.json').read_text())
A=json.loads((OUT/'registration_trial.json').read_text())
B=Matrix(((.001,0,0,0),(0,0,-.001,0),(0,.001,0,0),(0,0,0,1)))
CAD=ROOT/'deliverables/current/fabrication/aperture-access/cad/MAIN-C1-SS060_AP01_DRAFT_NOT_FOR_FABRICATION.stl'
bpy.ops.wm.read_factory_settings(use_empty=True)


def xyz(p):
    return Vector((p[0]/1000,-p[2]/1000,p[1]/1000))


def mat(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m


steel=mat('Custom CAD',(.16,.43,.48));gray=mat('Captured mesh',(.47,.49,.51))
purple=mat('Factory-opening reference',(.47,.22,.62));gold=mat('Removed foam footprint',(.72,.43,.14))
blue=mat('Estimated cap-center marker',(.03,.43,.67));ink=mat('Explanatory labels',(.04,.10,.12))


def curve(name,pts,material,width=.35):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=width/1000
    line=data.splines.new('POLY');line.points.add(len(pts)-1)
    for point,p in zip(line.points,pts):point.co=(*xyz(p),1)
    obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj);obj.data.materials.append(material)
    obj['diagram_overlay_only']=True;return obj


def text(body,p,size):
    data=bpy.data.curves.new(body,'FONT');data.body=body;data.size=size/1000
    obj=bpy.data.objects.new(body,data);bpy.context.scene.collection.objects.link(obj)
    obj.location=xyz(p);obj.rotation_euler=(math.pi/2,0,0);obj.data.materials.append(ink)


def stl(path,name,material):
    bpy.ops.wm.stl_import(filepath=str(path),forward_axis='Y',up_axis='Z')
    obj=bpy.context.object;obj.name=name;obj.data.transform(B);obj.data.materials.append(material)
    obj['source']=str(path.relative_to(ROOT));return obj


for i,case in enumerate(A['cases']):
    scene=bpy.context.scene if i==0 else bpy.data.scenes.new('temporary')
    bpy.context.window.scene=scene;scene.name='ALIGN02 | '+case['id']
    scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS'
    scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO'
    scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=False
    scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
    scene.display.shading.background_type='WORLD'
    scene.world=bpy.data.worlds.new(scene.name+' background');scene.world.color=(.86,.9,.92)
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.resolution_x=850;scene.render.resolution_y=950;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard'
    Q=case['rigid_row_rotation'];c=case['main_center_installed_mm'];t=case['rigid_translation_mm']
    pose=Matrix(((Q[0][0],Q[1][0],0,c[0]),(Q[0][1],Q[1][1],0,c[1]),(0,0,1,1),(0,0,0,1)))
    plate=stl(CAD,case['id']+' | unchanged AP01 C1 CAD',steel);plate.matrix_world=B@pose@B.inverted()
    plate['source_sha256']=hashlib.sha256(CAD.read_bytes()).hexdigest();plate['local_size_mm']=[220,220,1.524]
    scan=stl(ROOT/'build/aperture_access/captured_forward_display.stl',case['id']+' | source display crop',gray)
    s=case['scan_scale_trial'];scan.scale=(s,s,s)
    scan['trial_scale_only']=s;scan['original_source_unchanged']=True
    for name,hole,target,diam in zip(['L','U'],case['placed_reference_hole_centers_mm'],case['control_cap_targets_xy_mm'],[50,48.46]):
        cx,cy=hole
        circle=[(cx+diam/2*math.cos(j*2*math.pi/160),cy+diam/2*math.sin(j*2*math.pi/160),60) for j in range(161)]
        curve(name+' factory opening: '+('assumed Ø50' if name=='L' else 'measured Ø48.46'),circle,purple,.45)
        x,y=target
        curve(name+' estimated cap center X',[(x-1.8,y,62),(x+1.8,y,62)],blue,.4)
        curve(name+' estimated cap center Y',[(x,y-1.8,62),(x,y+1.8,62)],blue,.4)
        label_dy=14 if name=='U' else 5
        text(name+' cap estimate',(x-51,y+label_dy,62),3.6)
        curve(name+' marker leader',[(x-26,y+label_dy-3,62),(x-2,y+2,62)],ink,.18)
    for w,h,rad,name in [(130.35,165.1,40,'Foam outer / metal edge'),(118.35,153.1,34,'Foam inner edge: assumed uniform 6 mm')]:
        pts=[]
        for x,y,start in [(w/2-rad,h/2-rad,0),(-w/2+rad,h/2-rad,90),(-w/2+rad,-h/2+rad,180),(w/2-rad,-h/2+rad,270)]:
            for j in range(41):
                a=math.radians(start+j*90/40);local=(x+rad*math.cos(a),y+rad*math.sin(a))
                pts.append((local[0]*Q[0][0]+local[1]*Q[1][0]+c[0],local[0]*Q[0][1]+local[1]*Q[1][1]+c[1],59))
        pts.append(pts[0]);curve(name,pts,gold,.4)
    text('ALIGN02 | '+case['short_label'],(-115,170,64),4.8)
    text('Purple = factory openings. Blue + = estimated tip-cap centers.',(-115,-84,64),3.1)
    text('Lower opening is assumed. Overlays are projected, not installed.',(-115,-91,64),3.1)
    text('DRAFT: no verified shaft axes, handle engagement or sealing.',(-115,-98,64),3.1)
    cam=bpy.data.cameras.new(case['id']+' camera');obj=bpy.data.objects.new(case['id']+' camera',cam);scene.collection.objects.link(obj)
    obj.location=xyz((c[0],c[1],650));obj.rotation_euler=(xyz((*c,0))-obj.location).to_track_quat('-Z','Y').to_euler()
    cam.type='ORTHO';cam.ortho_scale=.290;cam.clip_start=.001;cam.clip_end=20;scene.camera=obj
    scene['status']='DRAFT_UNSELECTED';scene['scan_scale_trial']=s
    scene['state_limits']='Separate illustration. Scan untouched on disk; actual parts not scaled. Factory lower opening/registration and physical shaft axes unresolved.'

bpy.context.window.scene=bpy.data.scenes['ALIGN02 | CALIPER']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.clip_start=.001
note=bpy.data.texts.new('READ ALIGN02 FIRST')
note.write('Three explicit states: original provisional pose, rigid recentering, and a separate uniform scan-scale trial calibrated to the user 80 mm end-center reading.\n'
           'Original scan, accepted measurements and AP01 CAD are unchanged. Display crop is not the full source installation.\n'
           'Blue crosshairs are fitted cap-center estimates, not measured shaft axes. Purple circles are inner-plate opening references, not knob diameters.\n'
           'The lower opening position/diameter, tip Z, stud axes, engagement and physical support remain unresolved. Small fit residuals are not accuracy bounds.\n'
           'Gold is the projected foam footprint on the removed inner plate, not foam installed in the exposed cavity.\n'
           'See index.html and registration_trial.json alongside this file. All states are DRAFT / NOT FOR FABRICATION.\n')
bpy.context.scene.render.filepath=str(OUT/'registration_caliper_front.png');bpy.ops.render.render(write_still=True)
dest=OUT/'control_registration_ALIGN02_DRAFT.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));bpy.ops.wm.open_mainfile(filepath=str(dest))
assert len(bpy.data.scenes)==3 and bpy.context.scene.name=='ALIGN02 | CALIPER'
for case in A['cases']:
    obj=bpy.data.objects[case['id']+' | unchanged AP01 C1 CAD']
    assert abs(obj.location.x*1000-case['main_center_installed_mm'][0])<1e-4
    assert abs(obj.location.z*1000-case['main_center_installed_mm'][1])<1e-4
    assert abs(obj.location.y*1000+1)<1e-4
    for size,expected in zip([max(v.co[k] for v in obj.data.vertices)-min(v.co[k] for v in obj.data.vertices) for k in range(3)],[.220,.001524,.220]):
        assert abs(size-expected)<.00006
(OUT/'blender_validation.json').write_text(json.dumps(dict(status='PASS',saved_reopened=True,scenes=3,default='ALIGN02 | CALIPER',CAD_local_dimensions_and_placements_checked=True,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),placement_inputs_sha256=hashlib.sha256(json.dumps(A['cases'],sort_keys=True).encode()).hexdigest(),physical_fit='UNPERFORMED'),indent=2)+'\n')
print('ALIGN02 saved and reopened; three states and CAD placements verified.')
