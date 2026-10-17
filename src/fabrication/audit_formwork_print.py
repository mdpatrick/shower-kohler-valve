"""Fresh RF03 handoff audit from delivered files, separate from CAD builder."""
from pathlib import Path
import sys,json,zipfile,hashlib,xml.etree.ElementTree as ET
import numpy as np
import cadquery as cq
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'deliverables/current/fabrication/FT02/formwork-print';PACK=OUT/'SEND_TO_PRINTER'
NS={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def section(mesh,z):
 s=mesh.section(plane_origin=(0,0,z),plane_normal=(0,0,1));assert s is not None
 loops=[Polygon(a[:,:2]) for a in s.discrete];loops=sorted(loops,key=lambda x:x.area,reverse=True)
 result=Polygon()
 for p in loops:result=result.symmetric_difference(p)
 return result,loops
parts=[]
for name,height in [('D12',20),('D24_RELIEVED',32)]:
 stem='PRINT_ONE_RF03_D12' if name=='D12' else 'OPTIONAL_DEEPER/PRINT_INSTEAD_RF03_D24_RELIEVED'
 stl=PACK/(stem+'.stl');mf=PACK/(stem+'.3mf');step=PACK/'CAD_REFERENCE'/('RF03_'+name+'_mm.step')
 mesh=trimesh.load(stl,force='mesh');assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
 assert np.allclose(mesh.bounds,[[0,0,0],[240,240,height]],atol=.02)
 solid=cq.importers.importStep(str(step)).val();b=solid.BoundingBox()
 assert solid.isValid() and len(solid.Solids())==1
 assert np.allclose([b.xlen,b.ylen,b.zlen],[240,240,height],atol=.001)
 assert abs(solid.Volume()-mesh.volume)/solid.Volume()<.001
 with zipfile.ZipFile(mf) as z:
  assert z.testzip() is None and set(z.namelist())=={'[Content_Types].xml','_rels/.rels','3D/3dmodel.model'}
  root=ET.fromstring(z.read('3D/3dmodel.model'));assert root.attrib['unit']=='millimeter'
  objs=root.findall('m:resources/m:object',NS);items=root.findall('m:build/m:item',NS)
  assert len(objs)==len(items)==1 and items[0].get('objectid')==objs[0].get('id')
  v=np.array([[float(n.attrib[k]) for k in ['x','y','z']] for n in objs[0].findall('m:mesh/m:vertices/m:vertex',NS)])
  f=np.array([[int(n.attrib[k]) for k in ['v1','v2','v3']] for n in objs[0].findall('m:mesh/m:triangles/m:triangle',NS)])
  assert np.isfinite(v).all() and f.min()==0 and f.max()<len(v)
  other=trimesh.Trimesh(v,f)
  assert other.is_watertight and len(other.split())==1 and np.allclose(other.bounds,mesh.bounds,atol=1e-5)
  assert abs(other.volume-mesh.volume)<.02
 third_party=trimesh.load(mf,force='mesh')
 assert third_party.is_watertight and len(third_party.split())==1
 assert np.allclose(third_party.bounds,mesh.bounds,atol=1e-5) and abs(third_party.volume-mesh.volume)<.02
 _,loops=section(mesh,1.0);slots=[]
 for p in loops:
  a=np.array(p.bounds);wh=a[2:]-a[:2]
  if np.allclose(wh,[12,8],atol=.03):slots.append((a[:2]+a[2:])/2)
 assert len(slots)==2
 slots=sorted(slots,key=lambda x:x[0]);assert np.allclose(slots,[[70.375,142.70],[169.165,96.25]],atol=.03)
 # Layer support test from actual STL: each 0.2 mm layer may extend 0.03 mm
 # from the previous section. This includes 1-degree draft and mesh approximation.
 # It is a printable-geometry check, not a slicer or strength test.
 prev,_=section(mesh,.1);max_island=0;max_components=1
 for z in np.arange(.3,height,.2):
  current,_=section(mesh,float(z));hit=current.difference(prev.buffer(.03))
  max_island=max(max_island,hit.area);prev=current
 assert max_island<.01
 parts.append({'id':name,'size_mm':[240,240,height],'slot_dimensions_mm':[12,8],'slot_centers_print_xy_mm':[a.tolist() for a in slots],
  'STL_components':1,'STL_closed_oriented':True,'STEP_valid_solids':1,'3MF_mm_one_object_geometry_only':True,'3MF_independent_trimesh_import':'PASS',
  'max_unsupported_layer_area_mm2_with_0_03mm_lateral_allowance':max_island,'print_bed_z0':True,'slicer_execution':'NOT RUN - equipment unknown; file geometry checked only'})
manifest=json.loads((PACK/'MANIFEST.json').read_text())
for row in manifest['files']:assert sha(PACK/row['file'])==row['sha256']
with zipfile.ZipFile(OUT/'RF03_FRIEND_PRINT_PACKAGE.zip') as z:
 assert z.testzip() is None
 files=[x for x in z.namelist() if not x.endswith('/')]
 assert len(files)==len(manifest['files'])+1
 for row in manifest['files']:assert hashlib.sha256(z.read('RF03_FRIEND_PRINT/'+row['file'])).hexdigest()==row['sha256']
 assert all('..' not in Path(n).parts and not Path(n).is_absolute() for n in files)
 assert not any(n.lower().endswith(('.blend','.obj','.gcode','.3mf.gcode','.jpeg','.jpg')) for n in files)
pdf=PdfReader(PACK/'PRINT_GUIDE.pdf');assert len(pdf.pages)==3
for page in pdf.pages:assert len(page.extract_text())>900
text='\n'.join(p.extract_text() for p in pdf.pages)
for s in ['240 x 240 x 20','12 x 8','100%','250 x 250','$75']:
 assert s in text,s
capture=json.loads((OUT/'capture_checks.json').read_text());assert all(x['overlap_mm2']<.01 for x in capture['checks'])
geometry=json.loads((OUT/'geometry_checks.json').read_text());assert all(x['rear_collar_symmetric_difference_mm3']<.01 for x in geometry['parts'])
report={'revision':'RF03','status':'PASS_FOR_PRINT_HANDOFF_WITH_STATED_LIMITS','audit_type':'Fresh adversarial review and file read-back by same agent; no independent reviewer or physical certification claimed.',
 'parts':parts,'package_hashes':'PASS','package_contents':'Only isolated custom tools, their images, and print guide/settings/costs; no scans, home photos or machine commands.',
 'PDF_pages':3,'PDF_visual_review':'See docs/validation/RF03_print_2026-10-17.json after rendered-page inspection.',
 'engineering_review':[
  {'challenge':'Thinner panel is less stiff. Is weight reduction hiding a support requirement?','resolution':'8 mm is a supported-tool design choice, not minimum engineered thickness. Broad independent padded bracing remains required; no rod-nut clamping, pressure casting or tamping. Physical seating/deflection and release rehearsal required.'},
  {'challenge':'Moving the front tabs from Z9.05..12.05 to Z5.05..8.05 can change clearance.','resolution':'Recomputed actual captured seated slice and conditional nut-removed forward sweep: zero added-tab overlap. Unknown rod sections/scan errors remain unverified; no guarantee of physical clearance.'},
  {'challenge':'Does the lighter revision change the molding contour or deeper rear reliefs?','resolution':'STEP boolean symmetric difference of RF02/RF03 rear geometry below Z0.05 is below 0.01 mm3. Same collar surfaces and reliefs.'},
  {'challenge':'A nice printer may have a small bed.','resolution':'Explicit 250x250 usable area including brim; 240 mm actual diameter. Do not scale. Small bed requires separately designed split tool, not an automatic slicer cut.'},
  {'challenge':'Will thin tabs or collar require supports?','resolution':'Tabs start on the bed and end at 3 mm. Collar grows from the face, tapering by 1 degree. Delivered mesh layer-support test passes; friend must still inspect actual slicer preview.'},
  {'challenge':'Does print authorization imply repair/waterproofing approval?','resolution':'No: authorized temporary print and dry fit only. All form/film/pads removed; physical repair suitability, support, engagement and water sealing remain separate.'},
  {'challenge':'Is $75 a measured quote?','resolution':'No. Explicit whole-spool/wear/labor gift budget with one retry. Filament mass is geometry estimate; no slicer runtime or utility tariff measurement.'}
 ],'physical_fit':'NOT PERFORMED','permanent_use':'NOT APPROVED','zip_sha256':sha(OUT/'RF03_FRIEND_PRINT_PACKAGE.zip')}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'parts':parts,'ZIP_files':len(files),'PDF_pages':3},indent=2))
