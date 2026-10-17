"""RF04 previews from the actual delivered CAD meshes, at matching scale."""
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'deliverables/current/fabrication/FT02/formwork-small-bed'
PACK = OUT / 'SEND_TO_PRINTER'
bpy.ops.wm.read_factory_settings(use_empty=True)

def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    return m

blue = material('Face - one PETG material', (.20, .53, .63))
gold = material('Collar - same PETG material', (.86, .61, .24))
violet = material('Tabs - same PETG material', (.60, .38, .68))
scenes = []

def scene(name, width=1400, height=1100):
    s = bpy.data.scenes.new(name)
    bpy.context.window.scene = s
    scenes.append(s)
    s.unit_settings.system = 'METRIC'
    s.unit_settings.length_unit = 'MILLIMETERS'
    s.render.engine = 'BLENDER_WORKBENCH'
    s.display.shading.light = 'STUDIO'
    s.display.shading.color_type = 'MATERIAL'
    s.display.shading.show_shadows = True
    s.display.shading.show_cavity = True
    s.display.shading.cavity_type = 'BOTH'
    s.display.shading.show_object_outline = False
    s.display.shading.background_type = 'WORLD'
    s.world = bpy.data.worlds.new(name + ' world')
    s.world.color = (.92, .95, .96)
    s.display.render_aa = '16'
    s.render.resolution_x, s.render.resolution_y = width, height
    s.render.resolution_percentage = 100
    s.view_settings.view_transform = 'Standard'
    s.render.image_settings.file_format = 'PNG'
    s.render.threads_mode = 'FIXED'
    s.render.threads = 4
    ca = bpy.data.cameras.new(name + ' camera')
    camera = bpy.data.objects.new(ca.name, ca)
    s.collection.objects.link(camera)
    s.camera = camera
    ca.type = 'ORTHO'
    ca.clip_start, ca.clip_end = .0001, 10
    return s

def part(path, center, xoffset=0):
    bpy.ops.wm.stl_import(filepath=str(path), forward_axis='Y', up_axis='Z')
    ob = bpy.context.object
    ob.name = path.stem + ' | delivered single CAD solid'
    for v in ob.data.vertices:
        v.co = (v.co - Vector((center, center, 0))) * .001
    ob.data.update()
    ob.location.x = xoffset / 1000
    for m in [blue, gold, violet]:
        ob.data.materials.append(m)
    for p in ob.data.polygons:
        x, y, z = p.center * 1000
        if z > 8.001:
            p.material_index = 1
        elif abs(x) < 55 and 14 < abs(y) < 34 and z < 3.01:
            p.material_index = 2
    ob['source_mm'] = str(path.relative_to(ROOT))
    ob['material'] = 'One PETG print. Colors explain features only.'
    return ob

def render(s, filename, eye, horizontal_mm, target=(0, 0, 8)):
    camera = s.camera
    camera.location = Vector(eye) / 1000
    camera.rotation_euler = (Vector(target) / 1000 - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = horizontal_mm / 1000
    s.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)

old = PACK / 'ORIGINAL_RF03/PRINT_INSTEAD_RF03_D24_RELIEVED.stl'
small = PACK / 'SMALL_RF04/RF04_SMALL_192_55_D24_RELIEVED_mm.stl'
for name, path, center in [('original', old, 120), ('small', small, 96.275)]:
    s = scene(name)
    part(path, center)
    render(s, name + '_print.png', (285, -400, 430), 340)
    render(s, name + '_top.png', (0, 0, 600), 315)
    render(s, name + '_print.png', (285, -400, 430), 340)
s = scene('Original and smaller face | same scale', 1800, 900)
part(old, 120, -145)
part(small, 96.275, 145)
render(s, 'comparison.png', (0, -550, 620), 590)
notes = bpy.data.texts.new('READ FIRST - RF04 small bed')
notes.write('Original RF03 D24 relieved form: 240 x 240 x 32 mm.\n'
            'RF04 small circular face: 192.55 x 192.55 x 32 mm.\n'
            'Both have identical rear collars, reliefs and 12 x 8 mm slots.\n'
            'Blue face, gold collar and purple tabs are explanatory colors, one PETG print.\n'
            'Temporary form only; all parts removed. Physical seating, support and release unverified.\n')
bpy.context.window.scene = scenes[-1]
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'RF04_original_and_small_forms.blend'), compress=True)
print('Saved RF04 CAD views and comparison Blender file.')
