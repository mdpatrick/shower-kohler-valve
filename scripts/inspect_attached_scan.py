"""Reproducible raw, textured inspection of the attached-inner-plate capture."""
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/attached_scan'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(ROOT/'data/extracted/polycam-inner-plate-attached/10_15_2026.obj'),
                      forward_axis='Y', up_axis='Z')
s = bpy.context.scene
s.render.engine='BLENDER_WORKBENCH'
s.display.shading.light='STUDIO'
s.display.shading.color_type='TEXTURE'
s.display.shading.show_shadows=False
s.display.shading.background_type='WORLD'
s.world=bpy.data.worlds.new('Background');s.world.color=(.84,.87,.89)
s.render.resolution_x=1500;s.render.resolution_y=1500;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.view_settings.view_transform='Standard'
cam=bpy.data.cameras.new('Raw inspection');o=bpy.data.objects.new('Raw inspection',cam)
s.collection.objects.link(o);s.camera=o;cam.type='ORTHO';cam.ortho_scale=3.2
for axis in ['front','back']:
    target=Vector((0,1.52,0));o.location=target+Vector((0,0,8 if axis=='front' else -8))
    o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(OUT/f'raw_{axis}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'raw_inspection.blend'))
