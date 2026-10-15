"""Fresh FT01 read-back audit; does not import the CAD builder.

Analytic capsule distance checks are independent of its polygon containment test.
Physical fit, stiffness, seal compression and hidden engagement are not tested here.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import hashlib, json, math, sys, zipfile
import cadquery as cq
import ezdxf
import numpy as np
import trimesh
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'deliverables/current/fabrication/fit-trial'

def read(p):
    return json.loads(p.read_text())

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def audit():
    design = read(ROOT/'canon/fit_trial_design.json')
    report = read(OUT/'design_report.json')
    assert report['design'] == design
    w, h = design['main']['aperture_width_mm'], design['main']['aperture_height_mm']
    radius, straight = w/2, h-w
    assert abs(radius-design['main']['aperture_radius_mm']) < 1e-10
    results = []
    for item in report['parts']:
        od, t = item['diameter_mm'], item['thickness_mm']
        assert od == (design['main']['outer_diameter_mm'] if item['kind']=='MAIN' else
                      design['diverter']['outer_diameter_mm'] if item['kind']=='DIV' else
                      design['diverter']['fallback_outer_diameter_mm'])
        assert t == next(x['thickness_mm'] for x in design['stocks'] if x['id']==item['stock'])
        for fmt, rel in item['files'].items():
            assert sha(OUT/rel) == item['sha256'][fmt]
        solid = cq.importers.importStep(str(OUT/item['files']['step'])).val()
        b = solid.BoundingBox()
        assert solid.isValid() and len(solid.Solids()) == 1
        assert np.max(np.abs([b.xmin+od/2,b.xmax-od/2,b.ymin+od/2,b.ymax-od/2,b.zmin,b.zmax-t])) < 1e-5
        area_removed = math.pi*radius**2 + w*straight if item['kind']=='MAIN' else math.pi*(design['diverter']['aperture_diameter_mm']/2)**2
        expected_volume = (math.pi*(od/2)**2-area_removed)*t
        assert abs(solid.Volume()-expected_volume) < 1e-5
        top = cq.Workplane(obj=solid).faces('>Z').val()
        assert len(top.Wires()) == 2
        inner = min(top.Wires(),key=lambda wire:wire.BoundingBox().xlen)
        ib = inner.BoundingBox()
        expect = [w,h] if item['kind']=='MAIN' else [design['diverter']['aperture_diameter_mm']]*2
        assert np.max(np.abs([ib.xlen-expect[0],ib.ylen-expect[1],ib.center.x,ib.center.y])) < 1e-5
        doc = ezdxf.readfile(OUT/item['files']['dxf'])
        entities = list(doc.modelspace())
        assert doc.units == ezdxf.units.MM
        kinds = sorted(e.dxftype() for e in entities)
        assert kinds == (['ARC','ARC','CIRCLE','LINE','LINE'] if item['kind']=='MAIN' else ['CIRCLE','CIRCLE'])
        for e in entities:
            if e.dxftype() == 'ARC':
                assert abs(e.dxf.radius-radius) < 1e-7
                assert abs((e.dxf.end_angle-e.dxf.start_angle)%360-180) < 1e-7
                assert abs(e.dxf.center.x) < 1e-7 and abs(abs(e.dxf.center.y)-straight/2) < 1e-7
            elif e.dxftype() == 'LINE':
                assert abs((e.dxf.end-e.dxf.start).magnitude-straight) < 1e-7
        cut = cq.importers.importDXF(str(OUT/item['files']['dxf'])).wires().toPending().extrude(t).val()
        assert len(cut.Solids()) == 1 and abs(cut.Volume()-expected_volume)<1e-4
        mesh = trimesh.load(OUT/item['files']['stl'],force='mesh')
        assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split()) == 1
        assert abs(mesh.volume-expected_volume)/expected_volume < .0002
        assert np.max(np.abs(mesh.extents-[od,od,t])) < .06
        results.append({'part':item['id'],'status':'PASS','analytic_volume_mm3':expected_volume,
                        'STEP_volume_error_mm3':solid.Volume()-expected_volume,'DXF_entities':kinds,
                        'STL_relative_volume_error':abs(mesh.volume-expected_volume)/expected_volume})

    # Independent analytic distance to a capsule, evaluated on every clipped
    # polygon vertex. A capsule is convex, so contained vertices contain each face.
    sys.path.insert(0,str(ROOT))
    from src.analysis.registration_trial import clipped_capture
    pieces, meshpath = clipped_capture(read(ROOT/'data/derived/resolved.json'))
    xy = []
    for piece in pieces:
        for poly in getattr(piece,'geoms',[piece]):
            xy.extend(poly.exterior.coords)
    xy = np.asarray(xy)
    placements = read(ROOT/'deliverables/current/fabrication/control-registration/registration_trial.json')
    checks = []
    for case, prior in zip(placements['cases'],report['placement_scenarios']):
        Q = np.asarray(case['rigid_row_rotation'])
        assert np.allclose(Q.T@Q,np.eye(2),atol=1e-9)
        local = (xy*case['scan_scale_trial']-case['main_center_installed_mm'])@Q.T
        q = np.column_stack((local[:,0],np.maximum(abs(local[:,1])-straight/2,0)))
        distances = radius-np.linalg.norm(q,axis=1)
        clearance = float(distances.min())
        assert clearance > 0 and abs(clearance-prior['minimum_projected_hardware_clearance_mm']) < .001
        checks.append({'state':case['id'],'polygons':len(pieces),'vertices':len(xy),
                       'analytic_minimum_clearance_mm':clearance,'outside_vertices':int((distances<0).sum())})

    pdfs = {}
    for name, count in [('project_handoff_FT01.pdf',7),('shop_drawings_FT01.pdf',2),('full_size_templates_FT01.pdf',2)]:
        reader = PdfReader(OUT/name)
        assert len(reader.pages)==count
        text = '\n'.join(p.extract_text() or '' for p in reader.pages)
        assert 'FT01' in text and 'Permanent installation' in text
        if name!='project_handoff_FT01.pdf':
            for p in reader.pages:
                assert abs(float(p.mediabox.width)-420*72/25.4)<.001
                assert abs(float(p.mediabox.height)-297*72/25.4)<.001
        pdfs[name]={'pages':count,'sha256':sha(OUT/name)}
    for page in PdfReader(OUT/'full_size_templates_FT01.pdf').pages:
        bars=[];start=None
        for operands,op in page.get_contents().operations:
            if op==b'm':start=tuple(map(float,operands))
            elif op==b'l' and start:
                end=tuple(map(float,operands));dx,dy=end[0]-start[0],end[1]-start[1]
                if abs(math.hypot(dx,dy)-100*72/25.4)<.001:bars.append((dx,dy))
                start=end
        assert len(bars)==2 and any(abs(dx)<.001 for dx,dy in bars) and any(abs(dy)<.001 for dx,dy in bars)
    shop_text=''.join(p.extract_text() for p in PdfReader(OUT/'shop_drawings_FT01.pdf').pages)
    for expected in [f'R{radius:g}',f'OUTSIDE DIAMETER {design["main"]["outer_diameter_mm"]:.2f}',
                     f'OPENING WIDTH {w:.2f}',f'OPENING HEIGHT {h:.2f}',
                     f'THROUGH DIAMETER {design["diverter"]["aperture_diameter_mm"]:.2f}']:
        assert expected in shop_text, 'Stale shop label: '+expected
    paper_profiles=check_paper_profiles(OUT,design)

    packages = []
    for path in sorted(OUT.glob('*_quote.zip')):
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None and len(z.namelist()) == 9
            assert all(Path(n).suffix in ['.step','.stl','.dxf','.pdf','.json','.txt'] for n in z.namelist())
            assert not any('FALLBACK' in n for n in z.namelist())
            for name, digest in json.loads(z.read('SHA256.json')).items():
                assert hashlib.sha256(z.read(name)).hexdigest() == digest
                assert digest == sha(OUT/('cad/'+name if name.endswith(('.step','.stl','.dxf')) else name))
            packages.append({'file':path.name,'members':len(z.namelist()),'sha256':sha(path),'private_scan_or_photo_included':False})
    for rel,digest in report['sources_sha256'].items():
        assert sha(ROOT/rel)==digest, 'Stale source: '+rel
    blender = read(OUT/'blender_check.json')
    assert blender['saved_reopened'] and blender['scenes']==3 and blender['source_vertex_count']==333573
    assert blender['script_sha256']==sha(ROOT/'src/blender/fit_trial.py')

    class Links(HTMLParser):
        refs=[]
        def handle_starttag(self,tag,attrs):
            self.refs.extend(v for k,v in attrs if k in ['href','src'])
    links=Links();links.feed((OUT/'index.html').read_text())
    checked=0
    for ref in links.refs:
        u=urlsplit(ref)
        if u.scheme or not u.path:continue
        target=OUT/unquote(u.path)
        if target==OUT/'audit.json':continue
        assert target.is_file(), 'Broken local link: '+ref
        checked+=1
    output={'revision':'FT01','status':'PASS_SOFTWARE_CHECKS_ONLY','parts':results,'analytic_capture_checks':checks,
      'capture_scope':report['geometric_check_scope'],'pdfs':pdfs,'paper_two_axis_100mm_bars':'PASS',
      'paper_profile_dimensions':paper_profiles,
      'quote_packages':packages,'local_links_checked':checked,'Blender_saved_reopened':'PASS',
      'fresh_review_method':'Separate read-back script, independent analytic capsule area/distance; same agent, not a second reviewer.',
      'remaining_physical_risks':['Actual plate/control/adapter pose and axial engagement','Scan scale and surface error are not bounded',
          f'Only {report["nominal_foam_extra_land_mm"]:.2f} mm nominal extra foam land; actual band shape/contact unverified',f'Diverter {design["diverter"]["aperture_diameter_mm"]:g} mm aperture and rear seal/contact footprint',
          'Thin sheet support, deflection and retention','Gap between both actual installed covers/backings','Support, sealing, drain and cured water verification'],
      'physical_fit':'NOT PERFORMED','permanent_installation_release':False,
      'auditor_sha256':sha(Path(__file__)),'capture_mesh_sha256':sha(meshpath)}
    for path in [OUT/'audit.json',ROOT/'docs/validation/fit_trial_FT01.json']:
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(output,indent=2)+'\n')
    print('FT01 fresh audit PASS: 6 STEP/STL/DXF sets, 3 analytic clearance states, 11 PDF pages, 2 quote packages; physical checks remain open.')

def check_paper_profiles(directory,design):
    """Read actual PDF drawing paths, independently of printed dimension labels.

    These profiles are drawn in page coordinates, without scaling transforms.
    Axis extrema of ReportLab circular Beziers are endpoints; using every path
    control point is exact for these axis-aligned circles and capsules.
    """
    expected=[[(design['main']['outer_diameter_mm'],)*2,
               (design['main']['aperture_width_mm'],design['main']['aperture_height_mm'])],
              [(design['diverter']['outer_diameter_mm'],)*2,
               (design['diverter']['aperture_diameter_mm'],)*2]]
    found={}
    for filename in ['shop_drawings_FT01.pdf','full_size_templates_FT01.pdf']:
        result=[]
        for page,wanted in zip(PdfReader(directory/filename).pages,expected):
            paths=[];points=[];curves=0
            matrix=np.eye(3);stack=[]
            for operands,op in page.get_contents().operations:
                if op==b'q':stack.append(matrix.copy())
                elif op==b'Q':matrix=stack.pop()
                elif op==b'cm':
                    a,b,c,d,e,f=map(float,operands);matrix=matrix@np.array([[a,c,e],[b,d,f],[0,0,1]])
                elif op==b'n':points=[];curves=0
                elif op in (b'm',b'l',b'c'):
                    points.extend((matrix@np.array([x,y,1]))[:2] for x,y in zip(map(float,operands[::2]),map(float,operands[1::2])))
                    if op==b'c':curves+=1
                elif op in (b'S',b's',b'B',b'B*',b'b',b'b*',b'f',b'f*'):
                    if curves>=4:
                        xy=np.array(points);size=(xy.max(axis=0)-xy.min(axis=0))*25.4/72
                        paths.append(size)
                    points=[];curves=0
            for wh in wanted:
                assert any(np.max(np.abs(p-wh))<.002 for p in paths), f'Wrong PDF profile in {filename}: expected {wh}, got {paths}'
            result.append([list(x) for x in wanted])
        found[filename]=result
    return found

if __name__=='__main__':audit()
