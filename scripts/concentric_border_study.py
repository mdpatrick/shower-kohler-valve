"""Isolated CB01 concentric study. Read canon; never replace F005 or scan geometry."""
from pathlib import Path
import hashlib
import html
import json
import math

import cadquery as cq
import ezdxf
import trimesh

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables/current/fabrication/concentric-border-study'
STATUS = 'DRAFT_NOT_FOR_FABRICATION'


def read(path):
    return json.loads((ROOT / path).read_text())


def front_svg(variant, main, div, study):
    scale = 1.32
    def xy(p):
        return 210 + (p[0] - main[0]) * scale, 44 + (175 - p[1]) * scale
    def circle(p, radius, fill, stroke):
        x, y = xy(p)
        return f'<circle cx="{x:.4f}" cy="{y:.4f}" r="{radius*scale:.4f}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
    elements = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 600" role="img">',
                f'<title>{html.escape(variant["name"])} — concentric front elevation</title>',
                '<rect width="420" height="600" fill="#f4f1e9"/>',
                '<g font-family="Arial,sans-serif" fill="#18343c">',
                '<text x="20" y="25" font-size="14">FRONT ELEVATION · DRAFT</text>']
    for center, outer, cover, width, label in [
        (main, variant['main_diameter_mm'], study['main_cover_diameter_mm'], variant['main_border_mm'], 'Main'),
        (div, variant['diverter_diameter_mm'], study['diverter_cover_diameter_mm'], variant['diverter_border_mm'], 'Diverter'),
    ]:
        elements += [circle(center, outer/2, '#8cb6c2', '#235365'),
                     circle(center, cover/2, '#d4d8d8', '#5c6a6c')]
        x, y = xy(center)
        for angle in range(0, 360, 45):
            dx, dy = math.cos(math.radians(angle)), math.sin(math.radians(angle))
            a, b = cover*scale/2, outer*scale/2
            elements.append(f'<path d="M{x+a*dx:.3f},{y+a*dy:.3f} L{x+b*dx:.3f},{y+b*dy:.3f}" stroke="#235365" stroke-width="1.5"/>')
        elements += [f'<text x="{x}" y="{y-16}" text-anchor="middle" font-size="15">{label} Ø{outer:g} mm</text>',
                     f'<text x="{x}" y="{y+5}" text-anchor="middle" font-size="17" font-weight="bold">{width:.2f} mm border</text>',
                     f'<text x="{x}" y="{y+24}" text-anchor="middle" font-size="12">constant through 360°</text>']
    top_y = xy((div[0], div[1]+variant['diverter_diameter_mm']/2))[1]
    bottom_y = xy((main[0], main[1]-variant['main_diameter_mm']/2))[1]
    middle = (top_y+bottom_y)/2
    elements += [f'<path d="M214,{middle:.4f} H338" stroke="#18343c" fill="none"/>',
                 f'<text x="400" y="{middle-8:.4f}" text-anchor="end" font-size="13">Gap {variant["gap_mm"]:.2f} mm</text>',
                 '<text x="20" y="570" font-size="12">Outline study; hidden hardware omitted.</text>',
                 '<text x="20" y="588" font-size="12">Centers and diverter diameter remain provisional.</text>',
                 '</g></svg>']
    return '\n'.join(elements)


def main():
    paths = ['canon/concentric_border_requirement.json', 'canon/fabrication_designs.json', 'data/derived/resolved.json']
    hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    requirement, original, resolved = [read(p) for p in paths]
    study = requirement['study']
    assert original['design_revision'] == study['source_design_revision']
    assert resolved['revision'] == study['source_evidence_revision']
    centers = {'MAIN': resolved['trim_center_mm'], 'DIV': resolved['diverter_tip_mm'][:2]}
    separation = math.dist(centers['MAIN'], centers['DIV'])
    features = [f for f in resolved['features'] if f.get('include_in_coverage')]
    divtrace = [((p[0]-900)*620/1800, 40+(900-p[1])*620/1800)
                for p in original['diverter_damage_trace']['pixels_outline']]
    (OUT/'cad').mkdir(parents=True, exist_ok=True)
    (OUT/'views').mkdir(parents=True, exist_ok=True)
    result = {'id':'CB01', 'status':STATUS, 'requirement':requirement['id'],
              'source_sha256':hashes, 'centers_installed_mm':centers,
              'center_status':'Inferred R005 cover centers, not accepted physical registration',
              'center_separation_mm':separation, 'variants':[], 'CAD_checks':[],
              'physical_fit':'NOT PERFORMED', 'manufacturing_release':'NOT GIVEN',
              'limits':study['limits'], 'source_scan_modified':False,
              'F005_geometry_or_render_files_modified':False}
    for config in study['variants']:
        v = dict(config)
        v['main_border_mm'] = (v['main_diameter_mm']-study['main_cover_diameter_mm'])/2
        v['diverter_border_mm'] = (v['diverter_diameter_mm']-study['diverter_cover_diameter_mm'])/2
        v['gap_mm'] = separation-(v['main_diameter_mm']+v['diverter_diameter_mm'])/2
        v['main_coverage'] = [dict(feature=f['id'], after_trace_allowance_mm=v['main_diameter_mm']/2-
                                  max(math.dist(centers['MAIN'], p) for p in f['contour_mm'])-
                                  f.get('trace_allowance_mm_at_R001',1.5)) for f in features]
        v['minimum_main_margin_mm'] = min(x['after_trace_allowance_mm'] for x in v['main_coverage'])
        v['minimum_diverter_margin_mm'] = v['diverter_diameter_mm']/2-max(math.dist(centers['DIV'],p) for p in divtrace)-2
        assert v['gap_mm'] > 0 and v['minimum_main_margin_mm'] > 0 and v['minimum_diverter_margin_mm'] > 0
        v['all_reported_margins_are_projected_only'] = True
        v['meets_previous_exploratory_main_10mm_land_target'] = v['minimum_main_margin_mm'] >= 10
        v['files'] = []
        for kind, diameter in [('MAIN',v['main_diameter_mm']), ('DIV',v['diverter_diameter_mm'])]:
            t = study['thickness_mm']
            solid = cq.Workplane('XY').circle(diameter/2).extrude(t)
            if kind == 'MAIN':
                c = centers[kind]
                points = [(p[0]-c[0],p[1]-c[1]) for p in original['aperture']['base_convex_polygon_installed_mm']]
                cutter = cq.Workplane('XY').polyline(points).close().offset2D(original['aperture']['outward_radius_mm']).extrude(t+2).translate((0,0,-1))
                for local, installed in zip(points, original['aperture']['base_convex_polygon_installed_mm']):
                    assert math.dist((local[0]+c[0],local[1]+c[1]),installed)<1e-10
            else:
                cutter = cq.Workplane('XY').circle(40).extrude(t+2).translate((0,0,-1))
            solid = solid.cut(cutter)
            shape = solid.val()
            assert shape.isValid() and len(shape.Solids()) == 1
            stem = f'{kind}-{v["id"]}_CB01_SS060_{STATUS}'
            step, stl, dxf = [OUT/'cad'/(stem+'.'+ext) for ext in ['step','stl','dxf']]
            cq.exporters.export(solid,str(step))
            cq.exporters.export(solid,str(stl),tolerance=.025,angularTolerance=.05)
            top = solid.faces('>Z').wires().translate((0,0,-t))
            cq.exporters.export(top,str(dxf),exportType='DXF')
            doc = ezdxf.readfile(dxf); doc.units=ezdxf.units.MM; doc.saveas(dxf)
            roundtrip = cq.importers.importStep(str(step)).val()
            dxf_solid = cq.importers.importDXF(str(dxf)).wires().toPending().extrude(t).val()
            mesh = trimesh.load(stl,force='mesh')
            assert roundtrip.isValid() and abs(roundtrip.Volume()-shape.Volume())<.01
            assert dxf_solid.isValid() and abs(dxf_solid.Volume()-shape.Volume())<.02
            assert mesh.is_watertight and len(top.vals()) == 2
            bb = roundtrip.BoundingBox()
            assert max(abs(bb.xlen-diameter),abs(bb.ylen-diameter),abs(bb.zlen-t))<1e-5
            outer = max(top.vals(), key=lambda wire:wire.Length())
            assert len(outer.Edges()) == 1 and outer.Edges()[0].geomType() == 'CIRCLE'
            assert abs(outer.Edges()[0].radius()-diameter/2)<1e-7
            assert abs(bb.xmin+diameter/2)<1e-6 and abs(bb.ymin+diameter/2)<1e-6
            result['CAD_checks'].append({'part':f'{kind}-{v["id"]}', 'solid_valid':True,
                'STEP_roundtrip':'PASS','DXF_roundtrip':'PASS','STL_watertight':True,
                'closed_contours':2,'outer_circle_center_local_mm':[0,0],
                'intentional_center_offset_from_cover_mm':[0,0], 'ideal_border_variation_mm':0,
                'center_to_use_installed_mm':centers[kind], 'thickness_mm':t})
            v['files'].append({'part':kind, **{p.suffix[1:]:str(p.relative_to(OUT)) for p in [step,stl,dxf]}})
        (OUT/'views'/f'{v["id"]}_front.svg').write_text(front_svg(v, centers['MAIN'], centers['DIV'],study))
        result['variants'].append(v)
    for p, sha in hashes.items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == sha, 'Input changed during study'
    (OUT/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    cards = []
    rows = []
    for v in result['variants']:
        links = ' '.join(f'<span>{f["part"]}: '+ ' / '.join(f'<a href="{f[ext]}">{ext.upper()}</a>' for ext in ['step','stl','dxf'])+'</span>' for f in v['files'])
        cards.append(f'<article><h2>{v["id"]} · {html.escape(v["name"])}</h2><img src="views/{v["id"]}_front.svg" alt="{html.escape(v["name"])} — concentric front elevation"><p>{links}</p></article>')
        rows.append(f'<tr><td>{v["id"]}</td><td>{v["main_diameter_mm"]:g} / {v["diverter_diameter_mm"]:g}</td><td>{v["main_border_mm"]:.2f} / {v["diverter_border_mm"]:.2f}</td><td>{v["gap_mm"]:.2f}</td><td>{v["minimum_main_margin_mm"]:.2f} / {v["minimum_diverter_margin_mm"]:.2f}</td></tr>')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Concentric escutcheon comparison · CB01 draft</title><style>body{margin:0;background:#eef3f3;color:#18343c;font:17px/1.5 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:28px}h1{font-size:36px;line-height:1.15}.flag{border-left:5px solid #a85131;background:#fff2e8;padding:15px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}article{background:white;padding:16px;border-radius:8px}h2{font-size:22px}img{width:100%;display:block}a{color:#00647a}span{display:block;margin:8px 0}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;background:white}td,th{padding:12px;text-align:left;border-bottom:1px solid #ccd7d9}th{background:#d8e7eb}small{font-size:14px}@media(max-width:720px){.grid{grid-template-columns:1fr}main{padding:18px}table{min-width:700px}}</style><main><h1>A constant border around each cover</h1><p>The visible edge now follows a circle centered on its own Kohler cover. There is zero intentional offset. These two independent draft studies preserve the prior insertion aperture in installed coordinates.</p><p class="flag"><b>DRAFT — NOT FOR FABRICATION.</b> F005's offset and rectangular appearances are rejected by the user requirement. These alternatives are unselected. Cover centers are still inferred; the main cover is measured at Ø184.15 mm and the diverter is nominal Ø98.425 mm. Actual cover registration and a repeatable centering method are required.</p><div class="grid">'''+''.join(cards)+'''</div><h2>Comparison in millimeters</h2><div class="scroll"><table><tr><th>Study</th><th>Outer diameters<br>Main / diverter</th><th>Uniform borders<br>Main / diverter</th><th>Plate gap</th><th>Minimum projected damage margin<br>Main / diverter</th></tr>'''+''.join(rows)+'''</table></div><p>Damage margins already subtract the existing 1.5 mm main and 2 mm diverter tracing allowances. They do not bound scan scale or actual placement error, or prove continuous sound support. Both smaller main plates fall below the previous exploratory 10 mm sound-land target. That tradeoff needs a qualified seal/support detail before selecting a size.</p><p>Moving the previous Ø230 mm main to the cover center while retaining the Ø120 mm diverter leaves only 0.24 mm projected separation. Reducing the diameters creates room without an unequal border. No valves, studs, wall mesh or factory parts were moved.</p><p>CAD is one SS060 thickness trial (1.524 mm), with local origin at each outer circle center and the rear face at Z=0. STEP, STL and DXF exports passed software round-trip checks; those checks do not demonstrate physical fit. The front drawings show outlines and cover envelopes, not hidden assembly details. F005 render/CAD files remain unchanged as historical evidence.</p><p><a href="analysis.json">Computed dimensions and executed checks</a> · <a href="../F005/index.html">Previous F005 review (appearance rejected)</a></p></main></html>'''
    (OUT/'index.html').write_text(page)
    print(json.dumps({'output':str(OUT), 'checks':len(result['CAD_checks']),
                      'variants':[{k:v[k] for k in ['id','gap_mm','main_border_mm','diverter_border_mm','minimum_main_margin_mm','minimum_diverter_margin_mm']} for v in result['variants']]},indent=2))


if __name__ == '__main__':
    main()
