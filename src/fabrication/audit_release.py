"""Fresh read-back/analytic audit of actual outgoing FT02 bytes, separate from builders."""
from pathlib import Path
import json,math,hashlib,sys,zipfile,re
import cadquery as cq
import ezdxf
import trimesh
import numpy as np
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b,eps=1e-5):assert abs(a-b)<eps,(a,b)
def audit():
 d=read('canon/fit_trial_design.json');out=ROOT/d['output_directory'];r=read(d['output_directory']+'/design_report.json');assert r['design']==d
 results=[]
 for part in r['parts']:
  p=out/part['files']['step'];s=cq.importers.importStep(str(p)).val();b=s.BoundingBox();od=part['diameter_mm'];t=part['thickness_mm']
  assert s.isValid() and len(s.Solids())==1
  assert 'SI_UNIT(.MILLI.,.METRE.)' in p.read_text().replace(' ','')
  for v,target in [(b.xmin,-od/2),(b.xmax,od/2),(b.ymin,-od/2),(b.ymax,od/2),(b.zmin,0),(b.zmax,t)]:close(v,target)
  top=cq.Workplane('XY').newObject([s]).faces('>Z').wires().vals();assert len(top)==2
  sizes=sorted([[q.BoundingBox().xlen,q.BoundingBox().ylen] for q in top],key=lambda a:a[0]);width,height=sizes[0]
  if part['kind']=='MAIN':
   w,h=d['main']['aperture_width_mm'],d['main']['aperture_height_mm'];area=math.pi*(od/2)**2-(math.pi*(w/2)**2+w*(h-w));close(width,w);close(height,h)
  else:
   dia=d['diverter']['aperture_diameter_mm'];area=math.pi/4*(od**2-dia**2);close(width,dia);close(height,dia)
  close(s.Volume(),area*t,.02)
  dp=out/part['files']['dxf'];doc=ezdxf.readfile(dp);assert doc.units==ezdxf.units.MM
  ds=cq.importers.importDXF(str(dp)).wires().toPending().extrude(t).val();assert ds.isValid() and len(ds.Solids())==1;close(ds.Volume(),s.Volume(),.03)
  mesh=trimesh.load(out/part['files']['stl'],force='mesh');assert mesh.is_watertight and len(mesh.split())==1;assert np.max(np.abs(mesh.extents-[od,od,t]))<.06
  assert abs(mesh.volume-s.Volume())/s.Volume()<.001
  for k,rel in part['files'].items():assert sha(out/rel)==part['sha256'][k]
  results.append({'id':part['id'],'valid_solids':1,'loops':2,'aperture_bounds_mm':[width,height],'analytic_volume_mm3':area*t,'export_volume_mm3':s.Volume(),'status':'PASS'})
 packages=[]
 for route,stock in [('METAL_FIT_TRIAL',d['stocks'][0]),('CLEAR_FIT_TRIAL',d['stocks'][1])]:
  dest=out/route;expected=[p for p in r['parts'] if p['stock']==stock['id']]
  assert len(list(dest.glob('*.step')))==2 and len(list(dest.glob('*.dxf')))==2 and len(list(dest.glob('*.stl')))==2
  for p in expected:
   assert (dest/(p['id']+'.step')).read_bytes()==(out/p['files']['step']).read_bytes()
   dx=dest/(p['id']+('_PONOKO_K020_CUT' if route.startswith('CLEAR') else '')+'.dxf')
   doc=ezdxf.readfile(dx);assert doc.units==ezdxf.units.MM
   q=cq.importers.importDXF(str(dx)).wires().toPending().extrude(1);assert len(q.val().Solids())==1
   wires=q.faces('>Z').wires().vals();assert len(wires)==2
   dims=sorted([(w.BoundingBox().xlen,w.BoundingBox().ylen) for w in wires])
   k=d['vendor_variant']['clear_kerf_mm'] if route.startswith('CLEAR') else 0
   close(dims[-1][0],p['diameter_mm']+k)
   target=[d['main']['aperture_width_mm']-k,d['main']['aperture_height_mm']-k] if p['kind']=='MAIN' else [d['diverter']['aperture_diameter_mm']-k]*2
   for a,b in zip(dims[0],target):close(a,b)
  hashes=json.loads((dest/'SHA256.json').read_text())
  for f,h in hashes.items():assert sha(dest/f)==h
  with zipfile.ZipFile(out/(d['revision']+'_'+route+'.zip')) as z:
   assert len([n for n in z.namelist() if n.endswith('.step')])==2
   assert not any(x in n.lower() for n in z.namelist() for x in ['wall','factory','scan','fallback','t3000','t1600'])
   for f in dest.iterdir():assert z.read(route+'/'+f.name)==f.read_bytes()
  packages.append({'route':route,'parts':2,'sha256':sha(out/(d['revision']+'_'+route+'.zip')),'status':'PASS'})
 # Independently derive the accepted frame; raw 3D tip observations remain separate.
 m=read('canon/measurements.json');values={x['id']:x['value_mm'] for x in m['measurements'] if 'value_mm' in x and x.get('status') not in ['superseded','rejected']}
 layout=read(d['output_directory']+'/engineering/locator_evaluation.json')['layout']
 a=[119.17-5.66/2,61.40-5.66/2];b=[16.38-5.66/2,108.85-5.66/2]
 assert a[0]>b[0] and a[1]<b[1]
 for k,expected in [('A',a),('B',b)]:
  for x,y in zip(layout['center_from_left_top_mm'][k],expected):close(x,y)
 close(layout['center_distance_mm'],math.dist(a,b))
 # Exercise rejected tab pipeline independently of selected plain release.
 from src.fabrication.fit_trial import make_main
 loc=read(d['output_directory']+'/engineering/locator_evaluation.json')['transforms']['mounting_centers_in_cover_frame_mm']
 tab=make_main(d,1.52,locators=loc);ts=tab.val();assert ts.isValid() and len(ts.Solids())==1
 assert len(tab.faces('>Z').wires().vals())==4
 tmp=ROOT/'build/FT02/tab_pipeline_check.step';cq.exporters.export(ts,str(tmp));tb=cq.importers.importStep(str(tmp)).val();close(tb.Volume(),ts.Volume(),.02)
 frm=read(d['output_directory']+'/engineering/form_assessment.json');fs=cq.importers.importStep(str(out/'REPAIR_FORM_TRIAL/RF01_MAIN_REMOVABLE_FORM_PETG.step')).val();assert fs.isValid() and len(fs.Solids())==1
 assert 'full_face_diagnostic' in frm
 for rel,h in frm['source_sha256'].items():assert sha(ROOT/rel)==h,(rel,'stale form')
 bc=read(d['output_directory']+'/blender_check.json');assert bc['saved_reopened'] and bc['scenes']==3 and bc['source_vertex_count']==333573
 assert set(bc['custom_dimensions_verified'])=={p['id'] for p in r['parts'] if p['stock']==d['stocks'][0]['id']}
 assert bc['script_sha256']==sha(ROOT/'src/blender/fit_trial.py')
 pdfs=list(out.glob('*.pdf'))+list((out/'METAL_FIT_TRIAL').glob('*.pdf'))+list((out/'CLEAR_FIT_TRIAL').glob('*.pdf'))
 pages={p.name if p.parent==out else str(p.relative_to(out)):len(PdfReader(p).pages) for p in pdfs}
 assert pages['ORDER_AND_NEXT_STEP.pdf']==1 and 2<=pages['PLUMBER_START_HERE.pdf']<=3
 for p in out.glob('*.html'):
  for rel in re.findall(r'(?:href|src)="([^"#]+)',p.read_text()):
   if rel.startswith(('http','mailto:','/')):continue
   assert (p.parent/rel).exists(),(p.name,rel)
 result={'revision':d['revision'],'measurement_revision':m['revision'],'status':'PASS','scope':'Executed fresh file read-back, analytic and package consistency audit; not physical verification. Human-facing PDF/browser review is separately recorded in visual_review.json.','parts':results,'packages':packages,'R006_orientation':'PASS A upper-right/B lower-left; no reflection; raw 3D tip distances unused as planar layout','tab_pipeline':'PASS: 1 connected valid solid, 4 closed top loops, STEP round trip; this geometry is rejected and absent from order packages','form':'One connected STEP; collar-path scope and full-face seating limitation recorded; field placement/material suitability unperformed','blender':'Saved/reopened 3 scenes; CAD dimensions and preserved attached source verified','pdf_page_counts':pages,'physical_fit':'NOT PERFORMED','permanent_use':'NOT ESTABLISHED','source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'canon/fit_trial_design.json',ROOT/'canon/measurements.json',Path(__file__),out/'design_report.json']}}
 (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');(ROOT/'docs/validation/fit_trial_FT02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','parts':len(results),'packages':len(packages),'pdf_pages':sum(pages.values())}))
if __name__=='__main__':audit()
