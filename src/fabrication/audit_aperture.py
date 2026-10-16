"""Fresh read-back audit of AP01 exports, references and prototype template scale."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import subprocess
from urllib.parse import urlparse,unquote
import cadquery as cq
import ezdxf
from ezdxf import bbox
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'deliverables/current/fabrication/aperture-access'
REAR='deliverables/current/blender/installation_REAR01_DRAFT.blend'
RECEIPT='docs/validation/aperture_AP01_2026-10-15.json'


def check_preserved_files(root, rear_before_sha256=None):
    """Protect immutable evidence and the generated rear input at different scopes.

    A rebuilt .blend need not serialize identically to the historical commit.
    The launcher captures its hash after preparing REAR01 but before running
    AP01. A standalone audit reuses that successful check's saved baseline;
    legacy snapshots without it must still match the original committed file.
    """
    retained=['canon/measurements.json','canon/transforms.json','canon/fabrication_designs.json',
              'data/evidence/kohler-T14489-4.obj']
    preserved={}
    for name in retained:
        old=subprocess.check_output(['git','show','8911e34:'+name],cwd=root)
        preserved[name]=hashlib.sha256(old).hexdigest()==hashlib.sha256((root/name).read_bytes()).hexdigest()
    assert all(preserved.values()), 'Immutable AP01 evidence changed: '+str(preserved)
    scope='Unchanged between REAR01 preparation and the end of AP01 preparation'
    if rear_before_sha256 is None:
        receipt=root/RECEIPT
        saved=json.loads(receipt.read_text()) if receipt.exists() else {}
        prior=saved.get('generated_rear_preservation')
        if prior is not None:
            assert saved.get('status')=='PASS' and prior.get('status')=='PASS', 'No successful AP01 preservation receipt'
            rear_before_sha256=prior['sha256']
            scope='Matches the generated rear input retained by the last successful AP01 preparation'
        else:
            old=subprocess.check_output(['git','show','8911e34:'+REAR],cwd=root)
            rear_before_sha256=hashlib.sha256(old).hexdigest()
            scope='Legacy snapshot matches historical commit 8911e34; no rebuild baseline recorded'
    assert re.fullmatch(r'[0-9a-f]{64}',rear_before_sha256), 'Invalid rear preservation baseline'
    actual=hashlib.sha256((root/REAR).read_bytes()).hexdigest()
    assert actual==rear_before_sha256, 'Generated rear input changed outside its preparation stage'
    return preserved,dict(status='PASS',path=REAR,sha256=actual,scope=scope,
        limitation='File preservation only. REAR01 separately checks source mesh geometry, UVs and placement. No physical registration or fit is implied.')


def run(rear_before_sha256=None):
    a=json.loads((OUT/'analysis.json').read_text())
    for name,expected in a['input_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected, name
    parts=[]
    for p in a['CAD']:
        for ext,name in p['files'].items():
            assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==p['sha256'][ext]
        s=cq.importers.importStep(str(OUT/p['files']['step'])).val()
        bb=s.BoundingBox();d=p['outer_diameter_mm'];t=p['thickness_mm']
        assert max(abs(x-y) for x,y in zip([bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax],[-d/2,d/2,-d/2,d/2,0,t]))<1e-5
        face=max(s.Faces(),key=lambda f:f.Center().z)
        wires=face.Wires();assert len(wires)==2
        inner=min(wires,key=lambda w:w.BoundingBox().xlen)
        b=inner.BoundingBox()
        assert abs(b.xlen-116.35)<1e-5 and abs(b.ylen-151.10)<1e-5
        assert abs((b.xmin+b.xmax)/2)<1e-5 and abs((b.ymin+b.ymax)/2)<1e-5
        expected=(math.pi*(d/2)**2-(116.35*151.1-(4-math.pi)*33**2))*t
        assert abs(s.Volume()-expected)<.001
        if 'dxf' in p['files']:
            doc=ezdxf.readfile(OUT/p['files']['dxf']);m=list(doc.modelspace())
            assert doc.units==4 and len(m)==9
            types=[e.dxftype() for e in m]
            assert types.count('CIRCLE')==1 and types.count('ARC')==4 and types.count('LINE')==4
            outer=next(e for e in m if e.dxftype()=='CIRCLE')
            assert abs(outer.dxf.radius-d/2)<1e-6
            assert all(abs(e.dxf.radius-33)<1e-6 for e in m if e.dxftype()=='ARC')
            innerbox=bbox.extents([e for e in m if e.dxftype()!='CIRCLE'])
            assert abs(innerbox.size.x-116.35)<1e-6 and abs(innerbox.size.y-151.1)<1e-6
        parts.append({'id':p['id'],'CAD_bounds_local_center_and_aperture':'PASS','analytic_volume':'PASS','clean_DXF':bool('dxf' in p['files'])})
    reader=PdfReader(OUT/'aperture_access_AP01_DRAFT.pdf');assert len(reader.pages)==4
    for i,page in enumerate(reader.pages):
        assert 'DRAFT' in page.extract_text()
        if i>=2:
            assert abs(float(page.mediabox.width)-297*72/25.4)<.01
            assert abs(float(page.mediabox.height)-420*72/25.4)<.01
            # A3 template applies exact mm-to-point transform to its profile paths.
            content=page.get_contents().get_data().decode('latin1')
            assert '2.834646 0 0 2.834646' in content
            assert '100 mm X' in page.extract_text() and '100 mm Y' in page.extract_text()
    missing=[]
    for page in [OUT/'index.html',ROOT/'deliverables/current/review/rear/index.html']:
        for href in re.findall(r'(?:src|href)="([^"]+)"',page.read_text()):
            u=urlparse(href)
            if u.scheme or not u.path:continue
            local=ROOT/'deliverables/current'/unquote(u.path).lstrip('/') if u.path.startswith('/') else page.parent/unquote(u.path)
            if not local.exists():missing.append(href)
    assert not missing,missing
    preserved,rear_preservation=check_preserved_files(ROOT,rear_before_sha256)
    result=dict(id='AP01-READBACK-AUDIT',date='2026-10-15',status='PASS',parts=parts,
                pdf_pages=4,A3_template_scale='Exact 72/25.4 transform and two calibration bars verified',
                local_links='PASS',preserved_baseline=preserved,generated_rear_preservation=rear_preservation,
                visual_review='Not performed by this automated script; see docs/validation/aperture_AP01_visual_review_2026-10-15.json for the separate dated inspection.',
                unresolved=['Actual corner and foam minimum-width geometry','Captured-surface mask excludes stone and unobserved geometry',
                            'Actual adapter/hub outside profiles and spline/thread engagement','Added bedding and compressed foam depths',
                            'Physical control-axis/cover registration','Lower reference opening diameter','Backing support and retention',
                            'Final sealing, material/finish, fabrication tolerance and user release'],
                adversarial_conclusion='No geometric export error found. AP01 improves connection access but does not justify manufacturing or asserting that handles attach. The 1 mm foam-side remainder is smaller than unbounded registration/shape uncertainty and is not a demonstrated tolerance.')
    path=ROOT/'docs/validation/aperture_AP01_2026-10-15.json';path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'parts':len(parts),'pdf_pages':4,'preserved':all(preserved.values()),'physical_fit':'UNPERFORMED'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--rear-before-sha256',help='Hash captured by the launcher before AP01 runs, after REAR01 preparation')
    run(parser.parse_args().rear_before_sha256)
