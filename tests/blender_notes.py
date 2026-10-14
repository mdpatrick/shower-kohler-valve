"""Prove annotation import remains visible despite Blender's duplicate-name suffix."""
from pathlib import Path
import bpy,sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/blender'))
from user_notes import restore_user_notes
out=ROOT/'build/annotation_test';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
source=bpy.data.collections.new('USER_NOTES');bpy.context.scene.collection.children.link(source)
marker=bpy.data.objects.new('ANNOTATION_PRESERVATION_TEST',None);source.objects.link(marker);marker.location=(.12,.23,.34)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'user_notes.blend'))
bpy.ops.wm.read_factory_settings(use_empty=True)
parent=bpy.data.collections.new('USER_NOTES');bpy.context.scene.collection.children.link(parent)
restored=restore_user_notes(out/'user_notes.blend',parent)
assert len(restored)==1 and restored[0].name!='USER_NOTES'
for c in bpy.context.view_layer.layer_collection.children:c.exclude=c.name!='USER_NOTES'
bpy.context.view_layer.update();marker=bpy.data.objects['ANNOTATION_PRESERVATION_TEST']
assert marker.visible_get() and all(abs(a-b)<1e-6 for a,b in zip(marker.location,[.12,.23,.34]))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'restored.blend'))
bpy.ops.wm.open_mainfile(filepath=str(out/'restored.blend'))
assert bpy.data.objects['ANNOTATION_PRESERVATION_TEST'].visible_get()
(ROOT/'docs/validation/annotation_check.json').write_text(json.dumps({'status':'PASS','scope':'dedicated USER_NOTES collection imported, visible, saved and reopened','synthetic_fixture_only':True,'production_notes_changed':False},indent=2)+'\n')
