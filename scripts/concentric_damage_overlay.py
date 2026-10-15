"""Read-only geometry inputs; add a registered damage-reveal page beside CB01.

Does not rebuild CAD, replace the package index, change primary-scan coordinates,
or modify the concurrently maintained concentric package / Blender generators.
"""
from pathlib import Path
import hashlib
import html
import json
import math
import shutil
import struct

import cadquery as cq
from shapely.geometry import Point, Polygon

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables/current/fabrication/concentric-border-study'
STATUS = 'DRAFT_NOT_FOR_FABRICATION'
TOP_IDS = ['CUT-01', 'CUT-02', 'CUT-03']


def load(path):
    return json.loads((ROOT/path).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def svg_path(geometry, xy):
    polygons = [geometry] if geometry.geom_type == 'Polygon' else list(getattr(geometry, 'geoms', []))
    commands = []
    for poly in polygons:
        if poly.geom_type != 'Polygon':
            continue
        for ring in [poly.exterior, *poly.interiors]:
            points = [xy(p) for p in ring.coords]
            commands.append('M'+' L'.join(f'{x:.4f},{y:.4f}' for x,y in points)+' Z')
    return ' '.join(commands)


def make_svg(variant, center, cover_diameter, features, metadata, top=False):
    pixels, span = metadata['pixels'], metadata['span_mm']
    cx, cy = metadata['center_installed_mm'][:2]
    scale = pixels/span
    def xy(point):
        return pixels/2+(point[0]-cx)*scale, pixels/2-(point[1]-cy)*scale
    def polar(radius, angle):
        a = math.radians(angle)
        return center[0]+radius*math.cos(a), center[1]+radius*math.sin(a)
    def path(poly):
        return svg_path(poly, xy)
    x, y = xy(center)
    radius = variant['main_diameter_mm']/2
    cover_radius = cover_diameter/2
    circle = Point(*center).buffer(radius, quad_segs=1024)
    cover = Point(*center).buffer(cover_radius, quad_segs=1024)
    annulus = circle.difference(cover)
    viewbox = '500 150 1250 470' if top else f'0 0 {pixels} {pixels}'
    labels = {
        'CUT-01':(-55, 158), 'CUT-02':(6, 154), 'CUT-03':(75, 148),
        'CUT-04':(-104, -1), 'CUT-05':(112, 10), 'CUT-06':(-5, -67), 'CUT-07':(112, -16),
    }
    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" role="img" aria-label="{variant["id"]}: registered damage under the exposed escutcheon border">',
                f'<title>{variant["id"]} — existing over-cuts beneath the concentric border</title>',
                '<desc>Original orthographic primary-scan render, retained registered damage traces, factory-cover edge and custom-plate edge. Dashed amber traces are uncertain marks.</desc>',
                '<style>.label{font:24px Arial,sans-serif;paint-order:stroke;stroke:#fff;stroke-width:6px;stroke-linejoin:round}.edge-label{font:bold 25px Arial,sans-serif;paint-order:stroke;stroke:#fff;stroke-width:6px}.trace{stroke-linejoin:round}.trace-label{font:bold 25px Arial,sans-serif;paint-order:stroke;stroke:#fff;stroke-width:6px}</style>',
                f'<image href="wall_detail_source.png" x="0" y="0" width="{pixels}" height="{pixels}"/>',
                f'<path class="plate-fill overlay" d="{path(annulus)}" fill="#187fa1" fill-opacity="0.24" fill-rule="evenodd"/>',
                f'<circle class="cover-shade overlay" cx="{x:.4f}" cy="{y:.4f}" r="{cover_radius*scale:.4f}" fill="#e7eeee" fill-opacity="0.20"/>']
    # Show the retained annotation; color distinguishes damage from uncertainty.
    for feature in features:
        poly = Polygon(feature['contour_mm'])
        opening = feature['id'] == 'OPEN-MAIN'
        uncertain = feature['status'] == 'unknown'
        color = '#555d63' if opening else '#a26500' if uncertain else '#b72720'
        dash = ' stroke-dasharray="13 8"' if opening or uncertain else ''
        allowance = poly.buffer(feature.get('trace_allowance_mm_at_R001',1.5),quad_segs=32)
        elements.append(f'<path class="allowance overlay" style="display:none" d="{path(allowance)}" fill="{color}" fill-opacity="0.20" fill-rule="evenodd"/>')
        elements.append(f'<path class="trace overlay" d="{path(poly)}" fill="{color}" fill-opacity="{0.04 if opening else 0.15}" stroke="{color}" stroke-width="{3 if opening else 4}"{dash}/>')
        # Emphasize only the portion outside the factory cover: the part beneath the exposed custom border.
        exposed = poly.difference(cover).intersection(circle)
        if not exposed.is_empty:
            elements.append(f'<path class="trace overlay" d="{path(exposed)}" fill="{color}" fill-opacity="0.58" stroke="{color}" stroke-width="3"{dash} fill-rule="evenodd"/>')
        if not opening:
            representative = poly.representative_point()
            ax, ay = xy((representative.x, representative.y))
            lx, ly = xy(labels[feature['id']])
            suffix = '?' if uncertain else ''
            elements.append(f'<g class="trace overlay"><path d="M{ax:.3f},{ay:.3f} L{lx:.3f},{ly+8:.3f}" stroke="white" stroke-width="7"/><path d="M{ax:.3f},{ay:.3f} L{lx:.3f},{ly+8:.3f}" stroke="{color}" stroke-width="2"/><text class="trace-label" x="{lx:.3f}" y="{ly:.3f}" fill="{color}" text-anchor="middle">{feature["id"]}{suffix}</text></g>')
    elements += [f'<circle class="edge overlay" cx="{x:.4f}" cy="{y:.4f}" r="{radius*scale:.4f}" fill="none" stroke="white" stroke-width="10"/>',
                 f'<circle class="edge overlay" cx="{x:.4f}" cy="{y:.4f}" r="{radius*scale:.4f}" fill="none" stroke="#006987" stroke-width="6"/>',
                 f'<circle class="edge overlay" cx="{x:.4f}" cy="{y:.4f}" r="{cover_radius*scale:.4f}" fill="none" stroke="white" stroke-width="10"/>',
                 f'<circle class="edge overlay" cx="{x:.4f}" cy="{y:.4f}" r="{cover_radius*scale:.4f}" fill="none" stroke="#b07800" stroke-width="5"/>']
    # Two segments on the same radius show how the limiting cut consumes the exposed border.
    worst = next(f for f in features if f['id']=='CUT-03')
    tip = max(worst['contour_mm'], key=lambda p:math.dist(center,p))
    radial = math.dist(center,tip)
    unit = [(tip[i]-center[i])/radial for i in range(2)]
    start, end = [[center[i]+unit[i]*r for i in range(2)] for r in [cover_radius,radius]]
    p0, p1, p2 = xy(start),xy(tip),xy(end)
    for left, right, color in [(p0,p1,'#b72720'),(p1,p2,'#006987')]:
        elements.append(f'<path class="dimension overlay" d="M{left[0]:.3f},{left[1]:.3f} L{right[0]:.3f},{right[1]:.3f}" stroke="white" stroke-width="11"/>')
        elements.append(f'<path class="dimension overlay" d="M{left[0]:.3f},{left[1]:.3f} L{right[0]:.3f},{right[1]:.3f}" stroke="{color}" stroke-width="6"/>')
    for p in [p0,p1,p2]:
        elements.append(f'<circle class="dimension overlay" cx="{p[0]:.3f}" cy="{p[1]:.3f}" r="5" fill="white" stroke="#18343c" stroke-width="2"/>')
    if not top:
        for label, r, angle, color, offset in [('Custom outer edge',radius,208,'#006987',(-105,-42)),
                                               ('Kohler cover edge',cover_radius,330,'#b07800',(92,-27))]:
            p=polar(r,angle); px,py=xy(p); lx,ly=xy(offset)
            elements.append(f'<g class="edge overlay"><path d="M{px:.3f},{py:.3f} L{lx:.3f},{ly-8:.3f}" stroke="{color}" stroke-width="3"/><text class="edge-label" x="{lx:.3f}" y="{ly:.3f}" fill="{color}" text-anchor="middle">{label}</text></g>')
    elements.append('</svg>')
    return '\n'.join(elements)


def main():
    input_paths = ['canon/damage_visibility_requirement.json', 'canon/concentric_border_requirement.json',
                   'data/derived/resolved.json', 'data/evidence/scan_quality/wall_detail_registered.json',
                   'data/evidence/scan_quality/wall_detail_registered.png',
                   'deliverables/current/fabrication/concentric-border-study/analysis.json']
    initial = {p:sha(ROOT/p) for p in input_paths}
    requirement = load(input_paths[0]); design = load(input_paths[1])['study']
    resolved = load(input_paths[2]); meta = load(input_paths[3]); analysis = load(input_paths[-1])
    assert resolved['revision'] == design['source_evidence_revision']
    center = analysis['centers_installed_mm']['MAIN']
    features = [f for f in resolved['features'] if f.get('include_in_coverage')]
    source = ROOT/input_paths[4]
    raw = source.read_bytes(); width,height = struct.unpack('>II',raw[16:24])
    assert raw[:8] == b'\x89PNG\r\n\x1a\n' and width == height == meta['pixels']
    # Independently prove that the displayed coordinate map reproduces the original tracing pixel contacts.
    pixel_errors=[]
    for f in features:
        for p,observed in zip(f['contour_mm'],f['annotation_pixels']):
            mapped=(meta['pixels']/2+(p[0]-meta['center_installed_mm'][0])*meta['pixels']/meta['span_mm'],
                    meta['pixels']/2-(p[1]-meta['center_installed_mm'][1])*meta['pixels']/meta['span_mm'])
            pixel_errors.append(math.dist(mapped,observed))
    assert max(pixel_errors) < 1e-7
    (OUT/'views').mkdir(exist_ok=True,parents=True)
    destination=OUT/'views/wall_detail_source.png'
    if not destination.exists() or sha(destination)!=sha(source):
        shutil.copyfile(source,destination)
    assert sha(destination)==sha(source)
    result={'id':'CB01-DAMAGE','status':STATUS,'requirement':requirement['id'],
            'source_sha256':initial,'image_metadata':meta,'original_render_bytes_preserved':True,
            'max_source_annotation_reprojection_error_pixels':max(pixel_errors),
            'cover_center_installed_mm':center,'cover_registration_status':'Inferred, not physically verified',
            'cover_diameter_mm':design['main_cover_diameter_mm'],'variants':[],
            'uncertain_features':['CUT-02','CUT-07'],
            'physical_fit':'NOT PERFORMED','support_and_seal_design':'UNRESOLVED',
            'limits':'XY projection of prior scan-derived traces; 1.5 mm trace allowance does not bound scale/placement error. Revealed damage does not describe an opaque assembled appearance or establish sound supporting stone.'}
    views={}; rows=[]
    for variant in analysis['variants']:
        main_cad=next(f for f in variant['files'] if f['part']=='MAIN')
        shape=cq.importers.importStep(str(OUT/main_cad['step'])).val(); bb=shape.BoundingBox()
        assert shape.isValid()
        assert abs(bb.xlen-variant['main_diameter_mm'])<1e-6 and abs(bb.ylen-bb.xlen)<1e-6
        assert abs((bb.xmin+bb.xmax)/2)<1e-6 and abs((bb.ymin+bb.ymax)/2)<1e-6
        cover=Point(*center).buffer(design['main_cover_diameter_mm']/2,quad_segs=2048)
        outer=Point(*center).buffer(variant['main_diameter_mm']/2,quad_segs=2048)
        info={'id':variant['id'],'name':variant['name'],'outer_diameter_mm':variant['main_diameter_mm'],
              'visible_border_mm':variant['main_border_mm'],'CAD_source':main_cad['step'],
              'CAD_sha256':sha(OUT/main_cad['step']),'features':[]}
        for f in features:
            poly=Polygon(f['contour_mm']); tip=max(f['contour_mm'],key=lambda p:math.dist(center,p))
            r=math.dist(center,tip); past=max(0,r-design['main_cover_diameter_mm']/2)
            raw_margin=variant['main_diameter_mm']/2-r
            budget=raw_margin-f.get('trace_allowance_mm_at_R001',1.5)
            assert raw_margin>0 and outer.covers(poly)
            record={'id':f['id'],'name':f['name'],'source_status':f['status'],
                    'trace_contour_installed_mm':f['contour_mm'],
                    'limiting_point_installed_mm':tip,
                    'max_extension_beyond_cover_mm':past,
                    'remaining_to_outer_edge_mm':raw_margin,
                    'trace_allowance_mm':f.get('trace_allowance_mm_at_R001',1.5),
                    'remaining_after_trace_allowance_mm':budget,
                    'area_under_exposed_border_mm2':poly.difference(cover).intersection(outer).area,
                    'trace_fully_covered_in_model':True}
            info['features'].append(record)
            if f['id'] in TOP_IDS:
                rows.append(f'<tr><td>{variant["id"]}</td><td>{f["id"]}{" (uncertain mark)" if f["status"]=="unknown" else ""}</td><td>{past:.2f}</td><td>{raw_margin:.2f}</td><td>{budget:.2f}</td></tr>')
        result['variants'].append(info)
        for top in [False,True]:
            kind='top_gouges' if top else 'damage_overlay'
            svg=make_svg(variant,center,design['main_cover_diameter_mm'],features,meta,top)
            (OUT/'views'/f'{variant["id"]}_{kind}.svg').write_text(svg)
            views[(variant['id'],top)]=svg.replace('href="wall_detail_source.png"','href="views/wall_detail_source.png"')
    for p,original in initial.items():
        assert sha(ROOT/p)==original, f'Concurrent input change: {p}'
    result['executed_checks']=['Original source PNG byte hash unchanged','Every trace vertex maps back to its annotation pixel',
                                'Current STEP outer-circle dimensions and local origin checked',
                                'All eight retained feature traces covered by both circles in the model',
                                'Current per-feature margins agree with prior CB01 analysis',
                                'Input fingerprints unchanged during generation']
    for v,old in zip(result['variants'],analysis['variants']):
        old_margins={f['feature']:f['after_trace_allowance_mm'] for f in old['main_coverage']}
        for f in v['features']:
            assert abs(f['remaining_after_trace_allowance_mm']-old_margins[f['id']])<1e-8
    (OUT/'damage_mapping.json').write_text(json.dumps(result,indent=2)+'\n')
    full_cards=[]; top_cards=[]
    for v in result['variants']:
        worst=next(f for f in v['features'] if f['id']=='CUT-03')
        full_cards.append(f'<article><h2>{v["id"]} · {v["visible_border_mm"]:.1f} mm main border</h2>{views[(v["id"],False)]}<p><a href="views/{v["id"]}_damage_overlay.svg">Open full-resolution overlay</a></p></article>')
        top_cards.append(f'<article><h3>{v["id"]} · Top gouges</h3>{views[(v["id"],True)]}<p><b>Top-right CUT-03:</b> its farthest point reaches {worst["max_extension_beyond_cover_mm"]:.2f} mm beyond the cover edge; {worst["remaining_to_outer_edge_mm"]:.2f} mm remains to the custom outer edge. After the 1.5 mm trace allowance: <b>{worst["remaining_after_trace_allowance_mm"]:.2f} mm</b>.</p><a href="views/{v["id"]}_top_gouges.svg">Open top close-up</a></article>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Where the top gouges sit beneath the escutcheon · CB01 draft</title><style>
*{box-sizing:border-box}body{margin:0;background:#eef3f3;color:#18343c;font:17px/1.5 system-ui,sans-serif}main{max-width:1440px;margin:auto;padding:24px}h1{font-size:clamp(28px,3.4vw,43px);line-height:1.15;max-width:1050px}h2{font-size:24px}h3{font-size:21px}.lead{font-size:20px;max-width:1100px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}article{padding:16px;background:white;border:1px solid #ced9db;border-radius:8px}article svg{width:100%;display:block;height:auto}.controls{display:flex;flex-wrap:wrap;gap:12px 24px;align-items:center;padding:16px;background:#fff;border:1px solid #cbd9dc;position:sticky;top:0;z-index:3;box-shadow:0 2px 8px #24465218}.controls label{white-space:nowrap}input{accent-color:#006987}input[type=range]{width:140px;vertical-align:middle}button{font:inherit;border:1px solid #728e98;border-radius:5px;background:#edf5f6;padding:6px 12px;color:#18343c}a{color:#006987}.legend{display:flex;flex-wrap:wrap;gap:12px 28px;margin:16px 0}.swatch{display:inline-block;width:25px;border-top:4px solid;vertical-align:middle;margin-right:6px}.amber{border-color:#a26500;border-top-style:dashed}.blue{border-color:#006987}.gold{border-color:#b07800}.red{border-color:#b72720}.flag{padding:14px 18px;border-left:5px solid #a35c24;background:#fff4e8}.scroll{overflow:auto}table{border-collapse:collapse;background:white;width:100%}th,td{text-align:left;padding:12px;border-bottom:1px solid #d0dcde}th{background:#d9e8eb}.note{font-size:14px}section{scroll-margin-top:120px;margin-top:26px}body.hide-traces .trace{display:none}body.hide-dimensions .dimension{display:none}body.photo-only .overlay{display:none!important}@media(max-width:760px){.grid{grid-template-columns:1fr}main{padding:14px}.controls{position:static}table{min-width:650px}}
</style><main><p><a href="index.html">← Concentric plate comparison</a> · <a href="#top-gouges">Top-gouge close-ups</a> · <a href="#dimensions">Dimensions</a></p><h1>Where the tile gouges sit under the visible border</h1><p class="lead">The blue band is the custom escutcheon visible around the Kohler cover. The red damage traces inside that band would be hidden by the actual metal. Here the band is transparent so you can see exactly which part covers each gouge.</p><div class="controls"><label>Blue-band opacity <input id="opacity" type="range" min="0" max="85" value="24" aria-label="Blue band opacity"> <output id="opacity-value">24%</output></label><label><input id="traces" type="checkbox" checked> Damage traces</label><label><input id="allowance" type="checkbox"> 1.5 mm tracing allowance</label><label><input id="dimensions" type="checkbox" checked> Limiting-cut dimension line</label><button id="photo" type="button" aria-pressed="false">Show scan only</button></div><div class="legend"><span><i class="swatch blue"></i>Custom plate outer edge</span><span><i class="swatch gold"></i>Factory cover edge</span><span><i class="swatch red"></i>Retained damage trace</span><span><i class="swatch amber"></i>Uncertain mark</span></div><div class="grid">'''+''.join(full_cards)+'''</div><section id="top-gouges"><h2>The upper gouges, enlarged</h2><p>CUT-01 is the top-left chipped edge. CUT-02 is the thin horizontal mark whose identity remains uncertain. CUT-03 is the top-right extension and the limiting outer-coverage trace for both concentric options. At CUT-03, the red segment runs from the cover edge to the farthest traced point. The blue segment continues from that point to the custom outer edge; the red distance does not mean every point along it is damaged.</p><div class="grid">'''+''.join(top_cards)+'''</div></section><section id="dimensions"><h2>How much of the exposed border covers each top trace?</h2><div class="scroll"><table><tr><th>Option</th><th>Trace</th><th>Farthest point beyond cover edge (mm)</th><th>Remaining to custom outer edge (mm)</th><th>Remaining after 1.5 mm trace allowance (mm)</th></tr>'''+''.join(rows)+'''</table></div><p class="flag"><b>Coverage, not verified sealing support.</b> The remaining distances are projected geometric margins, not proof that the stone underneath is sound or flat. The allowance addresses trace selection only; physical scan scale, exact cover placement, groove depth, gasket landing and the sealing detail remain unresolved. Neither option meets the earlier exploratory 10 mm main sound-land target.</p><p>The underlying image is the original orthographic render of the primary wall/valve scan, copied byte-for-byte. The outlines use the existing registered feature coordinates and reproduce their original annotation pixel positions. No marks have been painted into the image and no captured hardware has been moved. CUT-02 and CUT-07 remain uncertain. This is a reveal drawing, not a prediction that gouges will be visible through the finished opaque plate.</p><p><b>DRAFT — NOT FOR FABRICATION.</b> Main cover Ø184.15 mm is user-measured; its center remains inferred. The custom circles come from the current checked CAD. <a href="damage_mapping.json">Per-feature dimensions, provenance and executed checks</a>.</p></section></main><script>
const opacity=document.getElementById('opacity'),out=document.getElementById('opacity-value');
opacity.addEventListener('input',()=>{out.value=opacity.value+'%';document.querySelectorAll('.plate-fill').forEach(p=>p.setAttribute('fill-opacity',Number(opacity.value)/100));});
document.getElementById('traces').addEventListener('change',e=>document.body.classList.toggle('hide-traces',!e.target.checked));
document.getElementById('allowance').addEventListener('change',e=>document.querySelectorAll('.allowance').forEach(p=>p.style.display=e.target.checked?'':'none'));
document.getElementById('dimensions').addEventListener('change',e=>document.body.classList.toggle('hide-dimensions',!e.target.checked));
document.getElementById('photo').addEventListener('click',e=>{const on=document.body.classList.toggle('photo-only');e.target.setAttribute('aria-pressed',String(on));e.target.textContent=on?'Restore overlay':'Show scan only';});
</script></html>'''
    (OUT/'damage.html').write_text(page)
    print(json.dumps({'page':str(OUT/'damage.html'),'max_reprojection_error_px':max(pixel_errors),
        'top_right':[{'variant':v['id'],**{k:f[k] for k in ['max_extension_beyond_cover_mm','remaining_to_outer_edge_mm','remaining_after_trace_allowance_mm']}} for v in result['variants'] for f in v['features'] if f['id']=='CUT-03']},indent=2))


if __name__=='__main__':
    main()
