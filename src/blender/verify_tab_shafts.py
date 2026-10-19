"""Reopen the saved compact inspection file in a fresh Blender process."""
from pathlib import Path
import bpy,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'deliverables/current/analysis/tab-shafts-FS02';p=OUT/'shaft_inspection_FS02.blend'
bpy.ops.wm.open_mainfile(filepath=str(p))
rows=[]
for s in bpy.data.scenes:
 meshes=[o for o in s.objects if o.type=='MESH']
 if not meshes:continue
 assert s.unit_settings.system=='METRIC' and s.unit_settings.scale_length==1
 assert s.camera and s.camera.data.type=='ORTHO'
 rows.append({'scene':s.name,'mesh_objects':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes)})
assert len(rows)==6 and sum(x['mesh_objects'] for x in rows)==7
external=[i for i in bpy.data.images if i.source in {'FILE','SEQUENCE','MOVIE'} and not i.packed_file]
assert not external
r={'status':'PASS_FRESH_BLENDER_READBACK','scene_count':len(rows),'scenes':rows,'external_images_required':False,'image_blocks':[{'name':i.name,'source':i.source} for i in bpy.data.images],'file_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'physical_claims':'None'}
(OUT/'blender_readback.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
