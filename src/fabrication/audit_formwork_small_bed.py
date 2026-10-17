"""Fresh RF04 read-back and adversarial handoff checks; no CAD-builder imports."""
from pathlib import Path
import json, zipfile, hashlib, subprocess, xml.etree.ElementTree as ET
import numpy as np
import cadquery as cq
import trimesh
from shapely.geometry import Polygon
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'deliverables/current/fabrication/FT02/formwork-small-bed'
PACK = OUT / 'SEND_TO_PRINTER'
OLD = ROOT / 'deliverables/current/fabrication/FT02/formwork-print'
NS = {'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def section(mesh, z):
    cut = mesh.section(plane_origin=(0,0,z), plane_normal=(0,0,1))
    assert cut is not None
    loops = [Polygon(a[:,:2]) for a in cut.discrete]
    result = Polygon()
    for p in loops:
        result = result.symmetric_difference(p)
    return result, loops

parts=[]
solids=[]
for folder,stem,stepname,d,centers in [
    ('ORIGINAL_RF03','PRINT_INSTEAD_RF03_D24_RELIEVED','RF03_D24_RELIEVED_mm',240,[[70.375,142.70],[169.165,96.25]]),
    ('SMALL_RF04','RF04_SMALL_192_55_D24_RELIEVED_mm','RF04_SMALL_192_55_D24_RELIEVED_mm',192.55,[[46.65,118.975],[145.44,72.525]])]:
    stl=PACK/folder/(stem+'.stl');mf=PACK/folder/(stem+'.3mf');step=PACK/folder/(stepname+'.step')
    mesh=trimesh.load(stl,force='mesh')
    assert mesh.is_volume and len(mesh.split())==1
    assert np.allclose(mesh.bounds,[[0,0,0],[d,d,32]],atol=.02)
    solid=cq.importers.importStep(str(step)).val();box=solid.BoundingBox();solids.append(solid)
    assert solid.isValid() and len(solid.Solids())==1
    assert np.allclose([box.xlen,box.ylen,box.zlen],[d,d,32],atol=.001)
    volume_error=abs(solid.Volume()-mesh.volume)/solid.Volume()
    assert volume_error<.001
    with zipfile.ZipFile(mf) as z:
        assert z.testzip() is None
        assert set(z.namelist())=={'[Content_Types].xml','_rels/.rels','3D/3dmodel.model'}
        doc=ET.fromstring(z.read('3D/3dmodel.model'))
        assert doc.attrib['unit']=='millimeter'
        objects=doc.findall('m:resources/m:object',NS);items=doc.findall('m:build/m:item',NS)
        assert len(objects)==len(items)==1 and items[0].get('objectid')==objects[0].get('id')
    other=trimesh.load(mf,force='mesh')
    assert other.is_volume and len(other.split())==1
    assert np.allclose(other.bounds,mesh.bounds,atol=1e-5)
    assert abs(other.volume-mesh.volume)<.02
    _,loops=section(mesh,1);slots=[]
    for p in loops:
        b=np.array(p.bounds)
        if np.allclose(b[2:]-b[:2],[12,8],atol=.03):
            slots.append(((b[2:]+b[:2])/2).tolist())
    slots.sort(key=lambda a:a[0])
    assert len(slots)==2 and np.allclose(slots,centers,atol=.03)
    # Same support criterion as RF03, now checked from the new delivered STL.
    prev,_=section(mesh,.1);max_unsupported=0
    for z in np.arange(.3,32,.2):
        current,_=section(mesh,float(z))
        max_unsupported=max(max_unsupported,current.difference(prev.buffer(.03)).area)
        prev=current
    assert max_unsupported<.01
    parts.append({'variant':folder,'size_mm':[d,d,32],'valid_STEP_solids':1,
        'STL_closed_oriented_components':1,'STEP_STL_volume_difference_fraction':volume_error,
        '3MF_explicit_mm_and_one_geometry_object':True,'independent_3MF_import':'PASS',
        'slot_centers_print_xy_mm':slots,'slot_size_mm':[12,8],
        'max_unsupported_layer_area_mm2_with_0_03mm_lateral_allowance':max_unsupported})

old,new=solids
aligned=new.translate((23.725,23.725,0))
extra=aligned.cut(old).Volume();assert extra<.001
delta=old.cut(aligned);assert delta.BoundingBox().zmax<8.0001
core=cq.Workplane('XY',origin=(120,120,-1)).circle(85).extrude(34).val()
core_difference=old.intersect(core).cut(aligned.intersect(core)).Volume()+aligned.intersect(core).cut(old.intersect(core)).Volume()
assert core_difference<.001
collar=cq.Workplane('XY',origin=(120,120,8)).box(300,300,25,centered=(True,True,False)).val()
collar_difference=old.intersect(collar).cut(aligned.intersect(collar)).Volume()+aligned.intersect(collar).cut(old.intersect(collar)).Volume()
assert collar_difference<.001
# The circular cutoff is exact; verify no other removal inside it.
cutoff=cq.Workplane('XY',origin=(120,120,-1)).circle(96.275).extrude(34).val()
crop_difference=old.intersect(cutoff).cut(aligned).Volume()+aligned.cut(old.intersect(cutoff)).Volume()
assert crop_difference<.001
preserved=[]
for p in sorted(OLD.rglob('*')):
    if p.is_file() and p.suffix.lower() in {'.stl','.3mf','.step','.zip'}:
        rel=str(p.relative_to(ROOT))
        blob=subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT)
        assert hashlib.sha256(blob).hexdigest()==sha(p)
        preserved.append({'path':rel,'sha256':sha(p)})
for src,dst in [(OLD/'SEND_TO_PRINTER/OPTIONAL_DEEPER/PRINT_INSTEAD_RF03_D24_RELIEVED.stl',PACK/'ORIGINAL_RF03/PRINT_INSTEAD_RF03_D24_RELIEVED.stl'),
                (OLD/'SEND_TO_PRINTER/OPTIONAL_DEEPER/PRINT_INSTEAD_RF03_D24_RELIEVED.3mf',PACK/'ORIGINAL_RF03/PRINT_INSTEAD_RF03_D24_RELIEVED.3mf'),
                (OLD/'SEND_TO_PRINTER/CAD_REFERENCE/RF03_D24_RELIEVED_mm.step',PACK/'ORIGINAL_RF03/RF03_D24_RELIEVED_mm.step')]:
    assert sha(src)==sha(dst)
manifest=json.loads((PACK/'MANIFEST.json').read_text())
for row in manifest['files']:
    assert sha(PACK/row['file'])==row['sha256']
zip_path=OUT/'RF04_ORIGINAL_AND_SMALL_BED_PRINT_PACKAGE.zip'
with zipfile.ZipFile(zip_path) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(manifest['files'])+1
    for row in manifest['files']:
        assert hashlib.sha256(z.read('RF04_PRINT_OPTIONS/'+row['file'])).hexdigest()==row['sha256']
    assert all('..' not in Path(n).parts and not Path(n).is_absolute() for n in z.namelist())
    assert not any(n.lower().endswith(('.gcode','.obj','.blend','.jpg','.jpeg')) for n in z.namelist())
pdf=PdfReader(PACK/'PRINT_GUIDE.pdf');assert len(pdf.pages)==2
text='\n'.join(p.extract_text() for p in pdf.pages)
for word in ['192.55 x 192.55 x 32','203 x 203','240 x 240 x 32','250 x 250','12 x 8','100%','independently','Remove']:
    assert word.lower() in text.lower(),word
report={'revision':'RF04','status':'PASS_FOR_TEMPORARY_PRINT_HANDOFF_WITH_STATED_LIMITS',
    'review_method':'Fresh adversarial review by same agent from delivered files; not an independent external review or physical certification.',
    'parts':parts,'core_symmetric_difference_mm3':core_difference,'collar_symmetric_difference_mm3':collar_difference,
    'difference_from_exact_circular_crop_mm3':crop_difference,'new_material_outside_original_mm3':extra,
    'removed_material_max_print_z_mm':delta.BoundingBox().zmax,'originals_unchanged_against_Git_HEAD':preserved,
    'ZIP_integrity_and_hashes':'PASS','ZIP_sha256':sha(zip_path),'PDF_pages':2,
    'PDF_visual_review':'See docs/validation/RF04_small_bed_2026-10-17.json',
    'challenges':[
        {'question':'Did half-size unintentionally shrink collar or slots?','finding':'No. Only outer material removed; exact circular crop and central/rear geometry boolean checks pass. Scale stays 100%.'},
        {'question':'Do nuts and slots now carry the repair load?','finding':'No. Original loose slots only locate. Independent padded support and dry rehearsal remain required.'},
        {'question':'Does the smaller face still guide the whole repair?','finding':'Not established. It guides less face area; outside edge use sound tile reference/straightedge or additional form. No unsupported filler bridging.'},
        {'question':'Can any small bed print it?','finding':'No. Need 203 x 203 usable area with brim; a nominal bed dimension alone does not prove usable clearance.'},
        {'question':'Do inherited scan checks prove smaller form seats?','finding':'No. No new scan reconciliation claimed. Core geometry is unchanged but full contact, retention and release still need actual trial.'},
        {'question':'Is 24 mm a continuous repair boundary?','finding':'No. Rear reliefs remain; first 12 mm continuous only.'}],
    'slicer_execution':'NOT RUN - printer unknown','physical_fit':'NOT PERFORMED','permanent_use':'NOT APPROVED'}
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'PDF_pages':2,'original_files_preserved':len(preserved),'parts':parts},indent=2))
