"""Fresh independent re-import checks for the CB01 manufacturer-facing outputs."""
from pathlib import Path
import hashlib
import json
import math
import re
import tempfile
import zipfile
from urllib.parse import urlparse,unquote
import cadquery as cq
import ezdxf
import trimesh
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'deliverables/current/fabrication/concentric-border-study'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    manifest=json.loads((OUT/'package_manifest.json').read_text())
    req=read('canon/concentric_border_requirement.json')['study']
    old=read('deliverables/current/fabrication/F005/analysis.json')
    olddesign=read('canon/fabrication_designs.json')
    checks=[]
    for p in manifest['parts']:
        for ext in ['step','stl','dxf']:assert sha(OUT/p[ext])==p['sha256'][ext]
        s=cq.importers.importStep(str(OUT/p['step'])).val()
        assert s.isValid() and len(s.Solids())==1
        bb=s.BoundingBox();t=p['thickness_mm'];diam=p['diameter_mm']
        assert max(abs(bb.xlen-diam),abs(bb.ylen-diam),abs(bb.zlen-t),abs(bb.xmin+diam/2),abs(bb.ymin+diam/2),abs(bb.zmin))<1e-5
        profile=cq.importers.importDXF(str(OUT/p['dxf']))
        wires=profile.wires().vals();assert len(wires)==2
        outer=max(wires,key=lambda w:w.Length());inner=min(wires,key=lambda w:w.Length())
        assert len(outer.Edges())==1 and outer.Edges()[0].geomType()=='CIRCLE'
        assert abs(outer.Edges()[0].radius()-diam/2)<1e-7
        solid2=profile.wires().toPending().extrude(t).val()
        assert s.cut(solid2).Volume()<.03 and solid2.cut(s).Volume()<.03
        doc=ezdxf.readfile(OUT/p['dxf']);assert doc.units==ezdxf.units.MM
        assert all(e.dxftype() not in ['TEXT','MTEXT','DIMENSION','INSERT'] for e in doc.modelspace())
        mesh=trimesh.load(OUT/p['stl'],force='mesh')
        assert mesh.is_watertight and len(mesh.split())==1
        assert abs(mesh.volume-s.Volume())/s.Volume()<.0005
        assert max(abs(a-b) for a,b in zip(mesh.extents,[diam,diam,t]))<.06
        # Check installed aperture equality to the old, insertion-tested F005 cut path.
        if p['kind']=='MAIN':
            original=next(x for x in old['parts'] if x['id']=='MAIN-A-SS060')
            old_s=cq.Workplane(obj=cq.importers.importStep(str(ROOT/'deliverables/current/fabrication/F005'/original['step'])).val())
            old_inner=min(old_s.faces('>Z').wires().vals(),key=lambda w:w.Length())
            old_center=next(x['center_mm'] for x in olddesign['parts'] if x['id']=='MAIN-A')
            old_face=cq.Face.makeFromWires(old_inner).translate((*old_center,-1.524))
            new_face=cq.Face.makeFromWires(inner).translate((*p['center_installed_mm'],0))
            assert old_face.cut(new_face).Area()<.03 and new_face.cut(old_face).Area()<.03
        else:
            assert len(inner.Edges())==1 and abs(inner.Edges()[0].radius()-40)<1e-7
        checks.append({'id':p['id'],'solid_mesh_profile_units':'PASS','installed_aperture_preserved':'PASS'})
    assert len(checks)==12
    package_checks=[]
    with tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
        for path in sorted(OUT.glob('quote_*.zip')):
            with zipfile.ZipFile(path) as z:
                names=z.namelist();assert len(names)==9
                assert sum(n.endswith('.step') for n in names)==2
                assert sum(n.endswith('.stl') for n in names)==2
                assert sum(n.endswith('.dxf') for n in names)==2
                hashes=json.loads(z.read('SHA256.json'))
                assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in hashes.items())
                assert not any(n.endswith(('.png','.jpg','.obj','.blend')) for n in names)
                pdf=Path(temp)/'selected.pdf';pdf.write_bytes(z.read('selected_pair_drawings_DRAFT.pdf'))
                reader=PdfReader(pdf);assert len(reader.pages)==3
                assert not any(pg.images for pg in reader.pages)
                for name in names:
                    if name.endswith(('.step','.stl','.dxf')):
                        matching=next(p for p in manifest['parts'] if Path(p[name.rsplit('.',1)[1]]).name==name)
                        assert z.read(name)==(OUT/matching[name.rsplit('.',1)[1]]).read_bytes()
            package_checks.append({'file':path.name,'hashes_contents_privacy':'PASS'})
    assert len(package_checks)==6
    assert sha(OUT/'views/wall_detail_source.png')==sha(ROOT/'data/evidence/scan_quality/wall_detail_registered.png')
    missing=[]
    for name in ['index.html','damage.html']:
        text=(OUT/name).read_text()
        for href in re.findall(r'(?:href|src)=["\']([^"\']+)',text):
            parsed=urlparse(href)
            if parsed.scheme or not parsed.path:continue
            if not (OUT/unquote(parsed.path)).exists():missing.append(href)
    assert not missing,missing
    assert 'damage.html' in (OUT/'index.html').read_text()
    pdfs={p.name:{'pages':len(PdfReader(p).pages),'sha256':sha(p)} for p in OUT.glob('*.pdf')}
    result={'status':'PASS - software exports and packaging only','part_checks':checks,'package_checks':package_checks,
            'pdfs':pdfs,'damage_source_bytes_preserved':True,'broken_local_links':missing,
            'source_and_measurements':'No raw observation or scan changed by this audit',
            'locator_trial':'Separate diagnostic CAD excluded from all quote ZIPs; conflicts and physical gates remain open',
            'physical_fit':'NOT PERFORMED','manufacturing_release':'NOT GIVEN'}
    (ROOT/'docs/validation/concentric_exports_2026-10-15.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
