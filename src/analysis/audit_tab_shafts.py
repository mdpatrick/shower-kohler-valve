"""Fresh read-back audit for FS02/RF05; does not run the geometry builder."""
from pathlib import Path
import sys,json,math,hashlib,zipfile
from html.parser import HTMLParser
import numpy as np
import cadquery as cq
import trimesh
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.fabrication.formwork_print import read_3mf_mesh
OUT=ROOT/'deliverables/current/analysis/tab-shafts-FS02';FORM=ROOT/'deliverables/current/fabrication/FT02/tight-form-RF05'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def volume(s):return sum(x.Volume() for x in s.Solids())
def run():
 r=json.loads((OUT/'analysis.json').read_text());cfg=json.loads((ROOT/'canon/tab_shaft_trial_FS02.json').read_text());g=json.loads((FORM/'geometry_checks.json').read_text())
 for path,expected in r['protected_sha256'].items():assert sha(ROOT/path)==expected,path
 for path,expected in r['source_sha256'].items():assert sha(ROOT/path)==expected,path
 assert r['risk']['predicted_failure_fraction'] is None
 assert r['risk']['owner_accepted_failure_fraction']==[.25,.30]
 # Geometric pass is deliberately narrow; all calculation cases exclude nut mesh.
 assert len(r['geometric_checks'])==6 and all(x['contained'] for x in r['geometric_checks'])
 assert max(x['minimum_geometric_clearance_mm'] for x in r['geometric_checks'])<.25
 assert all(x['evaluation_diameter_mm']==5 for x in r['geometric_checks'])
 for name in ['with_formwork','without_inner_plate']:
  for k in 'AB':
   q=r['shaft_fits'][k][name];lo,hi=cfg['shaft_fit'][name+'_z_mm'][k]
   assert min(b['z'] for b in q['bands'])>=lo and max(b['z'] for b in q['bands'])<=hi
   assert hi<=11 # Fitted input cannot reach enlarged ends visible farther forward.
 assert r['owner_measurements_requested']==[]
 # Independent CAD read-back; test void and surrounding material at exact values.
 a=np.array(cfg['trial']['A']['center_cover_xy_mm']);b=np.array(cfg['trial']['B']['center_cover_xy_mm']);angle=math.degrees(math.atan2(a[1]-b[1],a[0]-b[0]))
 parts=[];solids=[]
 for p in g['parts']:
  files={Path(f['path']).suffix:FORM/f['path'] for f in p['files']}
  for f in p['files']:assert sha(FORM/f['path'])==f['sha256']
  d=p['diameter_mm'];wp=cq.importers.importStep(str(files['.step'])).translate((-d/2,-d/2,-8.05)).rotate((0,0,0),(1,0,0),180);s=wp.val();solids.append(s)
  assert s.isValid() and len(s.Solids())==1
  bb=s.BoundingBox();assert np.allclose([bb.xlen,bb.ylen,bb.zlen],[d,d,32],atol=.00001)
  per=[]
  for k,c in [('A',a),('B',b)]:
   base=cq.Workplane('XY',origin=(*c,5.06))
   inside=(base.circle(3.25-.001) if k=='A' else base.slot2D(9-.002,6.5-.002,angle)).extrude(2.98).val()
   outer=(base.circle(3.30) if k=='A' else base.slot2D(9.10,6.60,angle)).extrude(2.98).val()
   inner_ring=(base.circle(3.26) if k=='A' else base.slot2D(9.02,6.52,angle)).extrude(2.98).val()
   ring=outer.cut(inner_ring)
   void_hit=volume(s.intersect(inside));ring_missing=volume(ring.cut(s))
   assert void_hit<1e-5 and ring_missing<1e-4,(k,void_hit,ring_missing)
   per.append({'rod':k,'nominal_hole_interior_intersecting_solid_mm3':void_hit,'nearby_ring_missing_mm3':ring_missing})
  # Only tab neighborhoods can differ from the same-size baseline.
  baseline=ROOT/'deliverables/current/fabrication/FT02/formwork-print/SEND_TO_PRINTER/CAD_REFERENCE/RF03_D24_RELIEVED_mm.step'
  old=cq.importers.importStep(str(baseline)).translate((-120,-120,-8.05)).rotate((0,0,0),(1,0,0),180).val()
  crop=cq.Workplane('XY',origin=(0,0,-30)).circle(d/2).extrude(50).val();old=old.intersect(crop)
  region=cq.Workplane('XY',origin=(49.165,23.75,5.049)).circle(11).extrude(3.002).val().fuse(cq.Workplane('XY',origin=(-49.625,-22.70,5.049)).circle(11).extrude(3.002).val())
  outside=volume(s.cut(old).cut(region))+volume(old.cut(s).cut(region));assert outside<1e-4
  m=trimesh.load(files['.stl'],force='mesh');mf=read_3mf_mesh(files['.3mf'])
  assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
  assert mf.is_watertight and len(mf.split())==1 and np.allclose(m.bounds,mf.bounds,atol=1e-5)
  assert abs(m.volume-s.Volume())/s.Volume()<.0001
  parts.append({'diameter_mm':d,'readback_dimensions_mm':[bb.xlen,bb.ylen,bb.zlen],'holes':per,'changes_outside_tab_neighborhoods_mm3':outside,'closed_connected_meshes':True})
 common=cq.Workplane('XY',origin=(0,0,-30)).circle(95).extrude(50).val();p=solids[0].intersect(common);q=solids[1].intersect(common);central_delta=volume(p.cut(q))+volume(q.cut(p));assert central_delta<1e-4
 zpath=FORM/'RF05_EXPERIMENTAL_TIGHT_FORMS_BOTH_SIZES.zip'
 with zipfile.ZipFile(zpath) as z:
  assert z.testzip() is None
  assert len([n for n in z.namelist() if n.endswith('.stl')])==2
  for n in z.namelist():assert z.read(n)==(FORM/n).read_bytes()
 # Local links/assets only; no public or MASV downloads are requested or tested.
 class Links(HTMLParser):
  def __init__(self):super().__init__();self.paths=[]
  def handle_starttag(self,tag,attrs):
   a=dict(attrs)
   if tag=='img':self.paths.append(a['src'])
   if tag=='a' and a.get('href','').startswith('../../fabrication/'):self.paths.append(a['href'].split('#')[0])
 ll=Links();ll.feed((OUT/'index.html').read_text());assert all((OUT/p).resolve().is_file() for p in ll.paths)
 result={'revision':'FS02/RF05','status':'PASS_SOFTWARE_AND_EXPORT_CHECKS_ONLY','parts':parts,'same_central_collar_between_sizes_mm3':central_delta,
         'baseline_sources_preserved':True,'nut_geometry_in_fit_calculations':False,'owner_measurements_requested':[],
         'files_inspected':len(ll.paths),'archive_integrity':True,'predicted_failure_probability':None,
         'adversarial_findings':['The upper 0.05 mm calculation gap is much smaller than unresolved scan and print error; it is not a physical clearance guarantee.',
            'A 20 mm axis continuation is a sensitivity input. The actual bare endpoint is hidden and the complete insertion sweep remains unverified.',
            'FS01 local R8 tab fits suggest a different captured form placement; do not force this into the original working pose or treat the tighter holes as a precision measurement.',
            'RF05 retains baseline collar and control access exactly. It cannot cure an existing seating or depth problem.',
            'This fresh read-back audit is not an independent physical or fabrication-readiness approval.'],
         'readiness':{'experimental_geometry_prepared':True,'full_insertion_verified':False,'physical_fit_verified':False,'permanent_installation_released':False,'water_test_passed':False},
         'zip_sha256':sha(zpath),'config_sha256':sha(ROOT/'canon/tab_shaft_trial_FS02.json')}
 (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':run()
