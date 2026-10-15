"""Compare preserved wall/valve geometry in saved R004 and F005 workspaces."""
from pathlib import Path
import bpy,hashlib,json,array
ROOT=Path(__file__).resolve().parents[2]
def source_snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));result={}
 # Evaluate the observed layer before querying world matrices. Excluded objects
 # can return an unevaluated identity after a different scene is reopened.
 original=bpy.data.scenes.get('F005 | paired escutcheons') or next(iter(bpy.data.scenes))
 bpy.context.window.scene=original
 bpy.context.window.view_layer=original.view_layers.get('Observed unchanged') or original.view_layers['Observed']
 bpy.context.view_layer.update()
 for name in ['00A_SOURCE_WALL_FULL','01_OBSERVED_WALL']:
  c=bpy.data.collections[name]
  for obj in c.objects:
   if obj.type!='MESH':continue
   h=hashlib.sha256();v=array.array('f',[0])* (len(obj.data.vertices)*3);obj.data.vertices.foreach_get('co',v);h.update(v.tobytes())
   ix=array.array('i',[0])*len(obj.data.loops);obj.data.loops.foreach_get('vertex_index',ix);h.update(ix.tobytes())
   for uv in obj.data.uv_layers:
    a=array.array('f',[0])*(len(uv.data)*2);uv.data.foreach_get('uv',a);h.update(a.tobytes())
   result[name+'/'+obj.name]={'vertices':len(obj.data.vertices),'faces':len(obj.data.polygons),'mesh_uv_hash':h.hexdigest(),'matrix_world':[list(row) for row in obj.matrix_world],'matrix_basis':[list(row) for row in obj.matrix_basis],'location':list(obj.location),'rotation':list(obj.rotation_euler),'scale':list(obj.scale),'parent':obj.parent.name if obj.parent else None}
 return result
before=source_snapshot(ROOT/'deliverables/current/blender/installation_R004_DRAFT.blend')
after=source_snapshot(ROOT/'deliverables/current/fabrication/F005/paired_escutcheons_F005_DRAFT.blend')
if before!=after:
 (ROOT/'build/f005_blender_source_difference.json').write_text(json.dumps({'before':before,'after':after},indent=2)+'\n')
assert before==after,'Observed source changed'
out={'status':'PASS','method':'Reopen both saved files, compare exact float coordinates, topology indices, UVs and world matrices of full source and observed proxy','source_objects':after,'physical_fit':'UNRESOLVED'}
(ROOT/'docs/validation/fabrication_F005_blender_source.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS: full source and observed proxy have unchanged geometry, UVs and transforms')
