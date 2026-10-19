"""Fresh numerical/provenance audit of FS01; not physical-fit certification."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.ingest import sha
OUT=ROOT/'deliverables/current/analysis/formwork-scan-FS01'

def run():
 r=json.loads((OUT/'analysis.json').read_text());cfg=json.loads((ROOT/'canon/formwork_scan_assessment_FS01.json').read_text());checks=[]
 for p,h in r['sources_sha256'].items():assert sha(ROOT/p)==h,'Stale source: '+p
 checks.append('All recorded input/source hashes match current files')
 inputs=json.loads((ROOT/'canon/inputs.json').read_text())['inputs'];new=next(p for p in inputs if p['id']=='SCAN-FORMWORK')
 assert sha(ROOT/new['repository_path'])==new['sha256']==cfg['archive_sha256']
 assert (ROOT/new['repository_path']).stat().st_size==new['size_bytes']
 checks.append('Original formwork ZIP hash and byte size match preserved manifest')
 t=np.array(r['raw_to_form_diagnostic_mm']);s=r['uniform_mm_per_raw_unit']
 assert np.allclose(np.linalg.svd(t[:3,:3])[1],s,rtol=1e-12) and np.linalg.det(t[:3,:3])>0
 checks.append('Transform has one uniform scale and proper rotation; no anisotropic correction/reflection')
 for row in r['comparison']:
  a,b=row['pair'].split('-');p,q=[np.array(r['tip_points_form_frame_mm'][k]) for k in [a,b]]
  value=float(np.sqrt(sum((p-q)**2)))
  assert abs(value-row['with_formwork_mm'])<1e-10
  assert abs(row['formwork_minus_caliper_mm']-(value-row['caliper_3d_mm']))<1e-10
 checks.append('All six new 3D distances independently recomputed from saved coordinates')
 old=json.loads((ROOT/'deliverables/current/fabrication/FT02/tab-rethink/analysis.json').read_text())
 for row in r['comparison']:
  a,b=row['pair'].split('-');p,q=[np.array(old['original_fit_points_mm'][k])*old['original_diagnostic_scale_factor'] for k in [a,b]]
  assert abs(np.linalg.norm(p-q)-row['without_inner_plate_mm'])<1e-9
  p,q=[np.array(old['attached_local_points_mm'][k]) for k in [a,b]]
  assert abs(np.linalg.norm(p-q)-row['with_inner_plate_mm'])<1e-9
 checks.append('Earlier comparison distances independently recomputed; 80 mm calibration dependence retained')
 assert abs(r['coplanar_plate_bores']['separation_mm']-np.linalg.norm(np.array([116.34,58.57])-[13.55,106.02]))<1e-10
 checks.append('R006 coplanar bore separation recomputed, separate from projecting-tip distances')
 protected=['canon/measurements.json','canon/formwork_print_RF03.json','canon/formwork_small_bed_RF04.json','canon/fit_trial_design.json','canon/transforms.json','deliverables/current/analysis/registration.json']
 for p in protected:
  head=subprocess.check_output(['git','show','HEAD:'+p],cwd=ROOT)
  assert hashlib.sha256(head).hexdigest()==sha(ROOT/p),'Unexpected canon change: '+p
 checks.append('Accepted calipers and FT02/RF03/RF04 design canon match HEAD unchanged')
 m=trimesh.load(ROOT/cfg['selected_reference'],force='mesh')
 assert m.is_watertight and len(m.split())==1 and np.allclose(m.extents,[240,240,32],atol=.02)
 checks.append('Source STL reads back as one watertight 240 x 240 x 32 mm form')
 alternate=r['comparison'][0]['with_formwork_mm']*192.55/240
 assert 63<alternate<65
 checks.append('192.55 mm scale hypothesis gives about 63.9 mm U-L; 240 mm family agrees with independent 80 mm caliper')
 text=(OUT/'index.html').read_text();missing=[]
 for url in re.findall(r'(?:src|href)="([^"]+)"',text):
  if url.startswith(('http','#','data:')) or url=='audit.json':continue
  if not (OUT/url).resolve().exists():missing.append(url)
 assert not missing,missing
 checks.append('All report image/download references resolve locally')
 assert not r['decision']['tight_fixed_locator_ready'] and r['decision']['owner_measurements_requested']==[]
 assert r['calibration']['calipers_used_for_new_scale'] is False
 checks.append('No tighter CAD release, added owner measurement or false independent old-scale claim')
 audit={'revision':'FS01','date':'2026-10-19','status':'PASS_NUMERICAL_AND_PROVENANCE_AUDIT_ONLY','executed':checks,
 'adversarial_findings':[
 'A 2 mm cap band on A includes its enlarged nut. Use 1.5 mm even though the larger band agrees better with calipers.',
 'The 240 mm outer circle sets scale; it cannot also validate scale.',
 'Opening and outer-rim centers disagree by about 2 mm. Neither supplies a submillimeter slot location.',
 'Visible rods scan too thin versus the identified nominal stud, and complete slot walls are missing. Raw mesh collision would overstate clearance.',
 'Deeper blended rim sections lower the scale further. Published sensitivity is not a physical accuracy interval.',
 'Static placement does not establish repeatability, seating, an unforced insertion sweep or water performance.'],
 'physical_checks_executed':[],'fabrication_readiness':'Existing files unchanged; no tighter form released',
 'source_STL_extents_mm':m.extents.tolist(),'alternate_192_55_scale_U_L_mm':alternate,
 'analysis_sha256':sha(OUT/'analysis.json'),'report_sha256':sha(OUT/'index.html')}
 (OUT/'audit.json').write_text(json.dumps(audit,indent=2)+'\n');print('FS01 audit passed:',len(checks),'checks; physical fit not certified.')
if __name__=='__main__':run()
