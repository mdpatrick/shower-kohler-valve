"""Render a separate CAD/capture explanation; never edit the primary scene."""
from pathlib import Path
import json,math,sys,time
import bpy
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'build/FT02/tab_explainer'
OUT=ROOT/'deliverables/current/fabrication/FT02/tab-explainer'
cfg=json.loads((BUILD/'scene.json').read_text())
d=json.loads((ROOT/'canon/fit_trial_design.json').read_text())
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
preview='preview' in args
fps=cfg['fps'];last=cfg['frames']
B=Matrix(((.001,0,0,0),(0,0,-.001,0),(0,.001,0,0),(0,0,0,1)))
def xyz(p):return Vector((p[0]/1000,-p[2]/1000,p[1]/1000))
def material(name,rgb):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);return m
def imported_stl(name):
 bpy.ops.wm.stl_import(filepath=str(ROOT/cfg['assets'][name]['path']),forward_axis='Y',up_axis='Z')
 ob=bpy.context.object;ob.name=name;ob.data.transform(B)
 ob['CAD_source']=cfg['assets'][name]['path'];return ob
def smooth(t):return max(0,min(1,t))**2*(3-2*max(0,min(1,t)))
def lerp(a,b,t):return tuple(x+(y-x)*smooth(t) for x,y in zip(a,b))
def aim(eye,target,span):
 cam.location=xyz(eye);cam.rotation_euler=(xyz(target)-cam.location).to_track_quat('-Z','Y').to_euler()
 # span denotes vertical field of view; Blender fits the larger horizontal dimension.
 cam.data.ortho_scale=span/1000*(1024/640)
def aim_section(eye,target,span):
 # Keep depth upright in this isolated cutaway; main views keep wall-up upright.
 cam.location=xyz(eye)
 back=(cam.location-xyz(target)).normalized();right=xyz((0,0,1)).cross(back).normalized()
 up=back.cross(right).normalized()
 cam.rotation_euler=Matrix((right,up,back)).transposed().to_euler()
 cam.data.ortho_scale=span/1000*(1024/640)
def save_label(text, point, loc, color=None):
 bpy.context.view_layer.update()
 v=world_to_camera_view(scene,cam,xyz(point))
 labels.append({'text':text,'pixel':[v.x*1024,(1-v.y)*640],'label_pixel':loc,'color':color or [220,233,237]})
def save_dimension(text,start,end,loc):
 bpy.context.view_layer.update()
 points=[world_to_camera_view(scene,cam,xyz(p)) for p in [start,end]]
 labels.append({'text':text,'dimension_pixels':[[p.x*1024,(1-p.y)*640] for p in points],
                'label_pixel':loc,'color':[255,211,123]})

bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.name='FT02 tabs | explanatory animation'
scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS'
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='TEXTURE'
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH';scene.display.shading.curvature_ridge_factor=1.35
scene.display.shading.show_object_outline=False
scene.display.shading.background_type='WORLD'
scene.world=bpy.data.worlds.new('Neutral studio');scene.world.color=(.11,.14,.17)
scene.display.render_aa='8'
scene.render.resolution_x=1024;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.fps=fps
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.view_settings.view_transform='Standard'
blue=material('Custom plate',(.10,.50,.68));amber=material('Hypothetical bolt tabs',(.96,.57,.14))
purple=material('Nominal foam section',(.52,.31,.69));red=material('Overlap callout, not added geometry',(.95,.12,.07))
gray=material('Captured geometry',(.55,.57,.58))
reg=json.loads((ROOT/'data/derived/registration.json').read_text())
bpy.ops.wm.obj_import(filepath=str(ROOT/'data/extracted/shower-hole-valve-polycam/10_14_2026.obj'),forward_axis='Y',up_axis='Z')
scan_objects=list(bpy.context.selected_objects)
for ob in scan_objects:
 ob.matrix_world=B@Matrix(reg['raw_to_installed_mm']);ob.name='Original captured wall and valve'
 ob['source']='data/extracted/shower-hole-valve-polycam/10_14_2026.obj';ob['source_modified']=False

plain=imported_stl('plain');plain.data.materials.append(blue)
tabbed=imported_stl('tabbed_candidate');tabbed.data.materials.append(blue);tabbed.data.materials.append(amber)
# Classify actual CAD faces inside the nominal capsule. The holes remain actual boolean cuts.
half=d['main']['straight_side_length_mm']/2;radius=d['main']['aperture_width_mm']/2
for face in tabbed.data.polygons:
 x=face.center.x*1000;y=face.center.z*1000
 inside=x*x+max(0,abs(y)-half)**2 < radius*radius+1e-4
 face.material_index=1 if inside else 0
pose=cfg['plate_transform'];center=pose['translation_mm'];q=pose['row_rotation'];angle=math.atan2(q[0][1],q[0][0])
for ob in [plain,tabbed]:ob.rotation_euler[1]=-angle

section=imported_stl('backing_section');section.data.materials.append(blue)
foam=imported_stl('foam_section');foam.data.materials.append(purple)
foam['status']=cfg['section_status']
# A small ring locates the reported source overlap, rather than inventing an interfering solid.
bounds=cfg['seated_overlap']['added_tab_conflict_bounds_mm'];hit=((bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2,2.9)
bpy.ops.mesh.primitive_torus_add(major_radius=.0032,minor_radius=.00025,major_segments=48,minor_segments=8,
                               location=xyz(hit),rotation=(math.pi/2,0,0))
marker=bpy.context.object;marker.name='Callout around scan overlap';marker.data.materials.append(red)

c=bpy.data.cameras.new('Explanation camera');cam=bpy.data.objects.new(c.name,c);scene.collection.objects.link(cam)
c.type='ORTHO';c.clip_start=.0001;c.clip_end=10;scene.camera=cam
scene.frame_start=1;scene.frame_end=last
labels=[]
for ob in [section,foam]:ob.hide_render=True
scan_visible=[o for o in scan_objects]

def state(frame):
 global labels
 labels=[];t=(frame-1)/fps;section_mode=22<=t<31
 for ob in scan_visible:ob.hide_render=section_mode
 section.hide_render=not section_mode;foam.hide_render=not section_mode
 plain.hide_render=t<31 or section_mode;tabbed.hide_render=t>=22
 marker.hide_render=not(17<=t<22)
 depth=60
 if t<5:
  aim(lerp((175,105,490),(-105,110,430),t/5),(4,40,25),310)
 elif t<9:
  aim(lerp((-105,110,430),(100,88,125),(t-5)/4),lerp((4,40,25),(54,63,24),(t-5)/4),310+(67-310)*smooth((t-5)/4))
  depth=60+(44-60)*smooth((t-5)/4)
 elif t<17:
  depth=44+(1-44)*smooth((t-9)/8)
  aim((100,88,125),(54,63,17),67)
 elif t<22:
  depth=1
  u=(t-17)/2
  aim(lerp((100,88,125),(38,83,63),u),lerp((54,63,17),hit,u),67+(27-67)*smooth(u))
  save_label('Scan overlap region',hit,(60,500),[255,110,90])
 elif t<31:
  shift=cfg['relative_shift_mm']*smooth((t-24.5)/4)
  section.location=xyz((-shift,0,0));foam.location=(0,0,0)
  aim_section((-54,-35,22),(-61,0,2.5),21)
  save_label('Foam attached to inner plate (plate hidden)',(-62.175,-7,7.52),(45,65),[211,161,237])
  save_label('Custom backing',(-65-shift,-7,.76),(45,500),[96,214,238])
  save_dimension('6 mm foam width',(-65.175,-7,7.52),(-59.175,-7,7.52),(650,100))
  if t<24.5:
   save_dimension('1 mm extra backing',(-59.175,-7,1.52),(-58.175,-7,1.52),(650,420))
  if t>=28.5:
   save_dimension('About 0.5 mm unsupported',(-59.679,-7,1.52),(-59.175,-7,1.52),(650,420))
 else:
  aim(lerp((130,90,440),(-85,105,450),(t-31)/5),(4,40,5),285)
  depth=1
  save_label('No added bolt tabs',(56,63,3),(640,105),[96,214,238])
 for ob in [plain,tabbed]:ob.location=xyz((*center,depth))
 for ob in [plain,tabbed,section,foam,marker,*scan_objects]:ob.hide_viewport=ob.hide_render
 bpy.context.view_layer.update()
 return labels

# Camera and part keyframes keep the saved study useful for direct Blender inspection.
for frame in range(1,last+1):
 scene.frame_set(frame);state(frame)
 for ob in [cam,plain,tabbed,section,foam,marker,*scan_objects]:
  for key in ['location','rotation_euler','hide_render','hide_viewport']:ob.keyframe_insert(key,frame=frame)
 cam.data.keyframe_insert('ortho_scale',frame=frame)
notes=bpy.data.texts.new('READ FIRST - explanatory tab animation')
notes.write('Separate FT02 visual explanation; not manufacturing geometry to order.\n'
 'The preserved original capture is not moved or straightened. Tab registration remains a working transform.\n'
 'The tab mesh comes from the R006 CadQuery boolean study. Captured-surface overlap is not physical proof.\n'
 'Foam close-up is a nominal local straight-edge section. 1.504 mm shift is hypothetical clearance, not measured motion.\n'
 'The selected manufacturing files remain unchanged and contain no tabs.\n')
scene.frame_set(46);state(46)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_perspective='CAMERA'
   area.spaces.active.shading.color_type='TEXTURE'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'FT02_tab_explanation.blend'),compress=True)
dest=BUILD/('preview' if preview else 'frames');dest.mkdir(parents=True,exist_ok=True)
(BUILD/'labels').mkdir(exist_ok=True)
frames=[46,121,181,301,346,451,511] if preview else range(1,last+1)
start=time.time()
for frame in frames:
 scene.frame_set(frame);labs=state(frame)
 (BUILD/'labels'/f'{frame:04d}.json').write_text(json.dumps(labs))
 scene.render.filepath=str(dest/f'{frame:04d}.png');bpy.ops.render.render(write_still=True)
 if frame%30==1:print(f'FRAME {frame}/{last} elapsed {time.time()-start:.1f}s',flush=True)
print('Rendered explanatory frames without changing manufacturing files.',flush=True)
