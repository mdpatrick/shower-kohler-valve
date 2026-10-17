"""RF03 actual print-oriented CAD previews; no source scans or fabricated evidence."""
from pathlib import Path
import bpy, json
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'deliverables/current/fabrication/FT02/formwork-print'
PACK=OUT/'SEND_TO_PRINTER'
bpy.ops.wm.read_factory_settings(use_empty=True)
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
blue=mat('Face - unfilled PETG',(.20,.53,.63));gold=mat('Collar - same single material',(.86,.61,.24));violet=mat('Locating tabs - same single material',(.60,.38,.68));bedmat=mat('Build area illustration',(.75,.81,.84))
scenes=[]
for tag,name in [('D12','PRINT_ONE_RF03_D12'),('D24_RELIEVED','OPTIONAL_DEEPER/PRINT_INSTEAD_RF03_D24_RELIEVED')]:
 s=bpy.data.scenes.new('RF03 '+tag+' | print orientation');bpy.context.window.scene=s;scenes.append(s)
 s.unit_settings.system='METRIC';s.unit_settings.length_unit='MILLIMETERS'
 s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL'
 s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH';s.display.shading.show_object_outline=False
 s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new(tag+' world');s.world.color=(.92,.95,.96)
 s.display.render_aa='16';s.render.resolution_x=1440;s.render.resolution_y=1050;s.render.resolution_percentage=100;s.view_settings.view_transform='Standard'
 s.render.image_settings.file_format='PNG';s.render.threads_mode='FIXED';s.render.threads=4
 bpy.ops.wm.stl_import(filepath=str(PACK/(name+'.stl')),forward_axis='Y',up_axis='Z');ob=bpy.context.object;ob.name='RF03 '+tag+' | one connected CAD form'
 for v in ob.data.vertices:v.co*=.001
 ob.data.update();ob.data.materials.clear()
 for m in [blue,gold,violet]:ob.data.materials.append(m)
 for p in ob.data.polygons:
  x,y,z=p.center*1000
  if z>8.001:p.material_index=1
  elif abs(x-120)<55 and 14<abs(y-120)<34 and z<3.01:p.material_index=2
 ob['CAD_source']=name+'.stl';ob['single_material']='PETG; colors are explanatory only';ob['units']='source mm to Blender m once'
 ca=bpy.data.cameras.new(tag+' camera');camera=bpy.data.objects.new(ca.name,ca);s.collection.objects.link(camera);s.camera=camera;ca.type='ORTHO';ca.clip_start=.0001;ca.clip_end=10
 def render(suffix,eye,size=325):
  camera.location=Vector(eye)/1000;camera.rotation_euler=(Vector((.12,.12,.007))-camera.location).to_track_quat('-Z','Y').to_euler();ca.ortho_scale=size*1440/1050/1000
  s.render.filepath=str(OUT/(tag+'_'+suffix+'.png'));bpy.ops.render.render(write_still=True)
 render('print',(410,-280,430))
 render('top',(120,120,650),290)
 render('side',(460,-360,100),305)
 render('front',(410,-280,-430))
 render('print',(410,-280,430))
notes=bpy.data.texts.new('READ FIRST - RF03 PRINT')
notes.write('Two alternative single-material temporary forms. Print ONE, normally D12.\n'
 'Source models are in print coordinates. Flat front face lies on bed Z0; collar points up.\n'
 'D12: 240x240x20 mm. D24_RELIEVED: 240x240x32 mm; only first12 mm continuous.\n'
 'Colors identify surfaces only; no multi-color printing needed. No scans in this file.\n'
 '8 mm panel,2 mm collar wall,3 mm front tabs,12x8 mm slots. Independent padded bracing carries loads.\n'
 'Physical fit/flatness/release/repair-material suitability remain unverified.\n')
bpy.context.window.scene=scenes[0]
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'RF03_print_forms.blend'),compress=True)
print('RF03 CAD previews saved.')
