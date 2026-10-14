"""Check saved scene state placement against the CAD manifest; never saves the scene."""
from pathlib import Path
import bpy, json, struct

ROOT=Path(__file__).resolve().parents[1]
cad=json.loads((ROOT/'deliverables/current/cad/cad_manifest.json').read_text())
path=ROOT/f"deliverables/current/blender/installation_{cad['revision']}_DRAFT.blend"
bpy.ops.wm.open_mainfile(filepath=str(path))
tested=[]
for p in cad['parts']:
    o=bpy.data.objects[p['id']]
    def installed(obj):
        x,y,z=obj.location
        return [x*1000,z*1000,-y*1000]
    assert all(abs(x-y)<.001 for x,y in zip(installed(o),p['location_mm'])),p['id']
    if p['collection'] in ('02_INNER_AND_GASKET','03_OUTER_TRIM'):
        factory=bpy.data.objects['FACTORY_REFERENCE__'+p['id']]
        assert all(abs(x-y)<.001 for x,y in zip(installed(factory),p['factory_location_mm'])),p['id']
        assert factory.data==o.data
        tested.append(p['id'])
layer=bpy.context.scene.view_layers['Factory_reference']
assert layer.layer_collection.children['04_CUSTOM_CANDIDATE'].exclude
assert layer.layer_collection.children['05_PROPOSED_MATERIALS'].exclude
assert not layer.layer_collection.children['03B_DIVERTER_REFERENCE'].exclude
assert not layer.layer_collection.children['01_OBSERVED_WALL'].exclude
glb=(ROOT/'deliverables/current/review/installation_DRAFT.glb').read_bytes()
length,kind=struct.unpack_from('<II',glb,12)
assert kind==0x4e4f534a
doc=json.loads(glb[20:20+length])
assert not any(n.get('name','').startswith(('FACTORY_REFERENCE__','EXPLODED_ONLY__','SECTION_ONLY_')) for n in doc['nodes'])
report={'status':'PASS','revision':cad['revision'],'saved_scene_reopened':True,
        'checked_factory_parts':tested,'all_installed_part_positions_match_CAD':True,
        'factory_uses_shared_reference_meshes':True,'factory_view_hides_new_plate_and_seal':True,
        'factory_view_retains_wall_and_separate_diverter':True,'GLB_excludes_factory_exploded_section_copies':True,
        'physical_fit':'UNRESOLVED'}
(ROOT/'docs/validation/scene_state_check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
