"""Fresh saved-file check for CAD-only TR03 / RF02 scenes."""
from pathlib import Path
import bpy,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'deliverables/current/fabrication/FT02/tab-refinement'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'TR03_RF02_parts_study.blend'))
r=json.loads((OUT/'analysis.json').read_text());expected={Path(p['files']['stl']).stem:p for p in r['parts']+r['forms']}
checks=[]
for scene in bpy.data.scenes:
    if not (scene.name.startswith('TR03 |') or scene.name.startswith('RF02 |')):continue
    assert scene.unit_settings.system=='METRIC'
    meshobs=[o for o in scene.objects if o.type=='MESH'];assert len(meshobs)==1
    o=meshobs[0];points=[v.co for v in o.data.vertices]
    # Stored geometry already had exactly one mm->m axis conversion.
    actual=[(max(p.x for p in points)-min(p.x for p in points))*1000,
            (max(p.z for p in points)-min(p.z for p in points))*1000,
            (max(p.y for p in points)-min(p.y for p in points))*1000]
    bb=expected[o.name]['bounds_mm'];dims=[bb[1][i]-bb[0][i] for i in range(3)]
    delta=max(abs(a-b) for a,b in zip(actual,dims));assert delta<.001,(o.name,actual,dims)
    checks.append({'scene':scene.name,'mesh':o.name,'dimensions_mm':actual,'max_difference_from_CAD_mm':delta,'mesh_count':1})
assert len(checks)==3
result={'status':'PASS','checks':checks,'blender_sha256':hashlib.sha256((OUT/'TR03_RF02_parts_study.blend').read_bytes()).hexdigest(),
        'scope':'Fresh saved-file read, scene/mesh counts and CAD dimensions. No physical or installation check.'}
(OUT/'blender_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
