"""TR03/RF02 actual CAD-only inspection scenes and isolated rendered views."""
from pathlib import Path
import bpy, json, math
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'deliverables/current/fabrication/FT02/tab-refinement'
cfg=json.loads((ROOT/'canon/tab_refinement_study.json').read_text())
B=Matrix(((.001,0,0,0),(0,0,-.001,0),(0,.001,0,0),(0,0,0,1)))
def xyz(p):return Vector((p[0]/1000,-p[2]/1000,p[1]/1000))
def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
def scene(name):
    s=bpy.data.scenes.new(name);bpy.context.window.scene=s
    s.unit_settings.system='METRIC';s.unit_settings.length_unit='MILLIMETERS'
    s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL'
    s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH'
    s.display.shading.curvature_ridge_factor=1.1;s.display.shading.show_object_outline=False
    s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new(name+' world');s.world.color=(.87,.91,.93)
    s.display.render_aa='16';s.render.resolution_x=1440;s.render.resolution_y=1000;s.render.resolution_percentage=100
    s.render.threads_mode='FIXED';s.render.threads=4;s.render.image_settings.file_format='PNG'
    s.view_settings.view_transform='Standard'
    ca=bpy.data.cameras.new(name+' camera');cam=bpy.data.objects.new(ca.name,ca);s.collection.objects.link(cam);s.camera=cam
    ca.type='ORTHO';ca.clip_start=.0001;ca.clip_end=10
    return s
def aim(s,eye,target,vertical):
    c=s.camera;c.location=xyz(eye);c.rotation_euler=(xyz(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=vertical*1.44/1000
def load(s,name,form=False):
    bpy.context.window.scene=s
    path=OUT/(name+'.stl');bpy.ops.wm.stl_import(filepath=str(path),forward_axis='Y',up_axis='Z')
    ob=bpy.context.object;ob.name=name;ob.data.transform(B);ob.data.materials.append(blue);ob.data.materials.append(amber);ob.data.materials.append(purple)
    ob['CAD_source']=str(path.relative_to(ROOT));ob['status']='DESIGN STUDY, NOT RELEASED'
    for f in ob.data.polygons:
        x,y,z=f.center.x*1000,f.center.z*1000,-f.center.y*1000
        if form and z<0:f.material_index=1
        if abs(x)<55 and 14<abs(y)<34 and (not form or z>8):f.material_index=2
    return ob
def render(s,name,eye,target=(0,0,0),size=270):
    aim(s,eye,target,size);s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
blue=material('Backing / front form face',(.16,.52,.64))
amber=material('Rear collar',(.88,.59,.20))
purple=material('Integral loose locating tabs',(.65,.38,.72))
scenes=[]
s=scene('TR03 | smaller flat locating tabs');scenes.append(s)
plate=load(s,'TR03_MAIN_220_T1520_SLOT12x8_STUDY_NOT_RELEASED')
render(s,'plate_front',(0,0,550),size=245)
render(s,'plate_oblique',(250,180,500),size=245)
for tag in ['D12','D24_RELIEVED']:
    s=scene('RF02 | '+tag+' temporary tabbed form');scenes.append(s)
    ob=load(s,'RF02_'+tag+'_TABBED_REMOVABLE_FORM_STUDY_NOT_RELEASED',True)
    render(s,'form_'+tag.lower()+'_front',(220,210,500),size=290)
    render(s,'form_'+tag.lower()+'_rear',(280,230,-500),size=290)
    render(s,'form_'+tag.lower()+'_side',(480,0,-180),size=280)
    aim(s,(280,230,-500),(0,0,0),290)
notes=bpy.data.texts.new('READ FIRST - TR03 RF02')
notes.write('Actual CadQuery export meshes; units converted exactly once. No wall or factory hardware in manufacturing solids.\n'
 '12 x 8 mm flat slots replace the earlier 18 x 10 mm study; nuts removed before placement.\n'
 'RF02 D12 is a 12 mm continuous temporary collar. D24_RELIEVED extends to 24 mm only outside two rear relief windows; its continuous molding depth remains 12 mm.\n'
 'Locating tabs lie on the front side at Z9.05..12.05 and carry no repair load. Independent bracing remains required.\n'
 'All form, liner and pad material is removed after suitable cure. Retained use is not established.\n'
 'Captured overlap checks, full-face seating limitations and source hashes are in analysis.json.\n'
 'Selected FT02 order files remain unchanged; these studies are not released.\n')
bpy.context.window.scene=scenes[-1]
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'TR03_RF02_parts_study.blend'),compress=True)
print('Saved three CAD-only scenes and eight isolated views.')
