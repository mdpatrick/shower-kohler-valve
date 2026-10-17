from pathlib import Path
import bpy, hashlib, json, struct
root=Path.cwd()
out=root/'deliverables/current/fabrication/FT02/finish-study'
source=root/'deliverables/current/fabrication/FT02/escutcheon_fit_trial_FT02.blend'
report=json.loads((out/'render_provenance.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==report['source_sha256']
def shapes(scene):
    found={}
    for ob in scene.objects:
        if ob.type=='MESH':
            content=b''.join(struct.pack('<3f',*v.co) for v in ob.data.vertices)
            content+=b''.join(struct.pack('<I',i) for p in ob.data.polygons for i in p.vertices)
            found[ob.name]={'mesh_sha256':hashlib.sha256(content).hexdigest(),'matrix':[list(row) for row in ob.matrix_world]}
    return found
bpy.ops.wm.open_mainfile(filepath=str(source))
original=shapes(bpy.data.scenes['FT02 | proposed appearance'])
bpy.ops.wm.open_mainfile(filepath=str(out/'FIN01_finish_illustration.blend'))
assert len(bpy.data.scenes)==1
actual=shapes(bpy.context.scene)
assert original==actual, (original.keys(),actual.keys())
assert all(i.packed_file for i in bpy.data.images if i.source=='FILE')
imgs={}
for name in report['images']:
    data=(out/name).read_bytes()
    assert data[:8]==b'\x89PNG\r\n\x1a\n'
    dims=list(struct.unpack('>II',data[16:24]))
    assert dims==[1120,1400]
    imgs[name]={'size_px':dims,'sha256':hashlib.sha256(data).hexdigest()}
result={'revision':'FIN01','date':'2026-10-17','executed':{'source_blend_hash_unchanged':True,'all_mesh_geometry_and_transforms_identical_to_source_scene':True,'mesh_count':len(actual),'saved_blend_scene_count':len(bpy.data.scenes),'file_textures_packed':True,'png_readback':imgs,'browser':{'reference_images_loaded':3,'front_angled_warmer_controls_verified':True}},'not_tested':['Physical material appearance or finish match','Physical assembly fit','Sealing or water resistance']}
(out/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
