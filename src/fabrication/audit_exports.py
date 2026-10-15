"""Read the released-format files in a fresh process; no geometry-builder import."""
from pathlib import Path
import argparse,hashlib,io,json,math,subprocess,zipfile
import numpy as np
import cadquery as cq
import ezdxf,trimesh
from shapely.geometry import Polygon
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'deliverables/current/fabrication/F005'
parser=argparse.ArgumentParser()
parser.add_argument('--evidence-baseline',type=Path,help='SHA-256 map captured after a deliberate measurement import, before generators run; otherwise compare HEAD.')
args=parser.parse_args()
d=json.loads((ROOT/'canon/fabrication_designs.json').read_text())
a=json.loads((OUT/'analysis.json').read_text())
results=[]
ap=Polygon(d['aperture']['base_convex_polygon_installed_mm']).buffer(d['aperture']['outward_radius_mm'],quad_segs=1024)
for part in d['parts']:
 w=h=part.get('diameter_mm')
 if part['shape']=='circle':outer=math.pi*(w/2)**2
 else:
  w,h=part['width_mm'],part['height_mm'];outer=w*h-(4-math.pi)*part['radius_mm']**2
 area=outer-(ap.area if part.get('aperture') else math.pi*(part['aperture_diameter_mm']/2)**2)
 for stock in d['stock_options']:
  stem=f"{part['id']}-{stock['id']}_F005_DRAFT_NOT_FOR_FABRICATION"
  s=cq.importers.importStep(str(OUT/'cad'/f'{stem}.step')).val();bb=s.BoundingBox();t=stock['thickness_mm']
  assert s.isValid() and len(s.Solids())==1
  assert np.allclose([bb.xlen,bb.ylen,bb.zlen],[w,h,t],atol=1e-5)
  assert np.allclose([bb.xmin,bb.ymin,bb.zmin],[-w/2,-h/2,0],atol=1e-5)
  error=abs(s.Volume()-area*t);assert error<.03,(stem,error)
  m=trimesh.load(OUT/'cad'/f'{stem}.stl',force='mesh')
  assert m.is_watertight and np.allclose(m.extents,[w,h,t],atol=.06)
  assert abs(abs(m.volume)-s.Volume())/s.Volume()<.001
  results.append({'part':stem,'STEP_exact_dimensions_and_analytic_volume':'PASS','STL_scale_closed_volume':'PASS','analytic_volume_error_mm3':error})
 f=OUT/'cad'/f"{part['id']}_F005_CUT_ONLY_DRAFT_NOT_FOR_FABRICATION.dxf";doc=ezdxf.readfile(f)
 assert doc.units==4 and not any(e.dxftype() in ['TEXT','MTEXT','DIMENSION','INSERT'] for e in doc.modelspace())
 wires=cq.importers.importDXF(str(f)).wires();assert len(wires.vals())==2 and all(w.IsClosed() for w in wires.vals())
 dx=wires.toPending().extrude(1).val();assert dx.isValid() and abs(dx.Volume()-area)<.03
packages=[]
for f in OUT.glob('quote_package_*.zip'):
 pair,stock=f.stem.split('_')[2:4]
 with zipfile.ZipFile(f) as z:
  names=z.namelist();assert len(names)==9 and z.testzip() is None
  assert len([n for n in names if n.endswith('.step')])==2
  for suffix in ['step','stl']:
   for part in ['MAIN','DIV']:
    name=f'{part}-{pair}-{stock}_F005_DRAFT_NOT_FOR_FABRICATION.{suffix}'
    assert z.read(name)==(OUT/'cad'/name).read_bytes()
  pdf=PdfReader(io.BytesIO(z.read('custom_part_drawing_sheets_F005_DRAFT.pdf')))
  assert len(pdf.pages)==4 and all(len(p.images)==0 for p in pdf.pages)
  for line in z.read('SHA256SUMS.txt').decode().splitlines():
   digest,name=line.split('  ',1);assert hashlib.sha256(z.read(name)).hexdigest()==digest
 packages.append({'file':f.name,'hashes_selected_pair_thickness_and_no_images':'PASS'})
unchanged={}
if args.evidence_baseline:
 for p,digest in json.loads(args.evidence_baseline.read_text()).items():
  assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest,p
  unchanged[p]=digest
else:
 for p in ['canon/measurements.json','canon/scan_annotations.json','data/derived/registration.json']:
  try:old=subprocess.check_output(['git','show','HEAD:'+p],cwd=ROOT,stderr=subprocess.DEVNULL)
  except subprocess.CalledProcessError:continue
  assert old==(ROOT/p).read_bytes(),p
  unchanged[p]=hashlib.sha256(old).hexdigest()
r={'status':'PASS - exported geometry only','evidence_revision':d['evidence_revision'],'method':'Fresh process reading STEP/STL/DXF/ZIP; analytic outer area minus independent polygon offset; does not reuse builder solids','parts':results,'DXF_two_closed_contours_mm':4,'packages':packages,'unchanged_evidence_sha256':unchanged,'evidence_comparison_basis':'post-import, pre-build snapshot' if args.evidence_baseline else 'HEAD','physical_fit':'UNRESOLVED','independent_human_or_agent_design_review':'NOT PERFORMED'}
(ROOT/'docs/validation/fabrication_F005_exports.json').write_text(json.dumps(r,indent=2)+'\n')
print('PASS:',len(results),'custom STEP/STL pairs; 4 DXFs; 6 package contents/hashes; accepted measurements unchanged')
