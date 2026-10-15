"""Complete CB01 stock trials, drawings, templates and private-free quote packages."""
from pathlib import Path
import argparse
import hashlib
import html
import inspect
import json
import math
import shutil
import zipfile

import cadquery as cq
import ezdxf
from ezdxf.path import make_path
import trimesh

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'deliverables/current/fabrication/concentric-border-study'
STATUS = 'DRAFT_NOT_FOR_FABRICATION'


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inputs():
    a = read(OUT.relative_to(ROOT) / 'analysis.json')
    req = read('canon/concentric_border_requirement.json')
    design = read('canon/fabrication_designs.json')
    assert req['study']['source_evidence_revision'] == read('canon/measurements.json')['revision']
    for path, digest in a['source_sha256'].items():
        assert sha(ROOT / path) == digest, 'Rebuild the base CB01 study: ' + path
    return a, req, design


def cad():
    a, req, design = inputs()
    prior_path=OUT/'package_manifest.json'
    prior_parts={p['id']:p for p in json.loads(prior_path.read_text())['parts']} if prior_path.exists() else {}
    parts = []
    for v in a['variants']:
        for kind in ['MAIN', 'DIV']:
            original = next(f for f in v['files'] if f['part'] == kind)
            source_dxf = OUT / original['dxf']
            for stock in design['stock_options']:
                t = stock['thickness_mm']
                solid = cq.importers.importDXF(str(source_dxf)).wires().toPending().extrude(t)
                shape = solid.val()
                stem = f'{kind}-{v["id"]}_CB01_{stock["id"]}_{STATUS}'
                files = {ext: OUT / 'cad' / (stem + '.' + ext) for ext in ['step', 'stl', 'dxf']}
                if stock['id'] != 'SS060':
                    old=prior_parts.get(f'{kind}-{v["id"]}-{stock["id"]}')
                    intact=old and all(path.exists() and sha(path)==old['sha256'][ext] for ext,path in files.items())
                    previous=cq.importers.importStep(str(files['step'])).val() if intact else None
                    same=previous is not None and shape.cut(previous).Volume()<.01 and previous.cut(shape).Volume()<.01
                    if not same:
                        cq.exporters.export(solid, str(files['step']))
                        cq.exporters.export(solid, str(files['stl']), tolerance=.025, angularTolerance=.05)
                    if not files['dxf'].exists() or sha(source_dxf)!=sha(files['dxf']):
                        shutil.copyfile(source_dxf, files['dxf'])
                roundtrip = cq.importers.importStep(str(files['step'])).val()
                mesh = trimesh.load(files['stl'], force='mesh')
                diameter = v['main_diameter_mm'] if kind == 'MAIN' else v['diverter_diameter_mm']
                assert shape.isValid() and roundtrip.isValid() and len(roundtrip.Solids()) == 1
                assert abs(shape.Volume() - roundtrip.Volume()) < .02
                assert mesh.is_watertight and len(mesh.split()) == 1
                assert abs(mesh.volume - shape.Volume()) / shape.Volume() < .0005
                bb = roundtrip.BoundingBox()
                assert max(abs(bb.xlen-diameter), abs(bb.ylen-diameter), abs(bb.zlen-t)) < 1e-5
                assert max(abs(bb.xmin+diameter/2), abs(bb.ymin+diameter/2), abs(bb.zmin)) < 1e-5
                for actual, expected in zip(mesh.extents, [diameter, diameter, t]):
                    assert abs(actual - expected) < .06
                doc = ezdxf.readfile(files['dxf'])
                assert doc.units == ezdxf.units.MM
                assert not any(e.dxftype() in ['TEXT', 'MTEXT', 'DIMENSION'] for e in doc.modelspace())
                assert len(solid.faces('>Z').wires().vals()) == 2
                parts.append({
                    'id': f'{kind}-{v["id"]}-{stock["id"]}', 'kind': kind,
                    'variant': v['id'], 'stock': stock['id'], 'material': stock['material'],
                    'diameter_mm': diameter, 'thickness_mm': t,
                    'center_installed_mm': a['centers_installed_mm'][kind],
                    'local_origin': 'Outer circle center; rear face Z=0; +Y toward upper control',
                    'volume_mm3': shape.Volume(),
                    **{ext: str(path.relative_to(OUT)) for ext, path in files.items()},
                    'sha256': {ext: sha(path) for ext, path in files.items()},
                    'checks': {'STEP_solid_roundtrip': 'PASS', 'STL_watertight_bounds_volume': 'PASS',
                               'DXF_mm_two_closed_contours': 'PASS', 'center_origin_and_thickness': 'PASS'},
                })
    manifest = {
        'study': 'CB01', 'status': STATUS, 'evidence_revision': 'R005',
        'parts': parts, 'stock_options': design['stock_options'],
        'source_sha256': {p: sha(ROOT / p) for p in [
            'canon/concentric_border_requirement.json', 'canon/fabrication_designs.json',
            'data/derived/resolved.json']},
        'cad_function_source_sha256':hashlib.sha256(inspect.getsource(cad).encode()).hexdigest(),
        'physical_fit': 'NOT PERFORMED', 'manufacturing_release': 'NOT GIVEN',
        'prototype_note': '3 mm is an existing stock trial, not thickness-matched to either metal option. See stock deltas in drawings.',
        'placement_sensitivity': [
            {'variant':v['id'],'assumed_radial_location_bound_per_cover_mm':e,
             'gap_lower_bound_mm':v['gap_mm']-2*e,
             'main_damage_margin_lower_bound_mm':v['minimum_main_margin_mm']-e,
             'separate_plate_to_cover_offset_e_border_peak_to_peak_mm':2*e}
            for v in a['variants'] for e in [0,.5,1,2,3]],
        'placement_sensitivity_basis': 'Illustrative bounds, not measured uncertainty. Gap uses worst-case independent center shifts toward each other. Damage margin includes the prior trace allowance and subtracts the main position bound. Scale and hidden support remain unbounded. Border variation concerns a different error: plate-to-cover offset.',
    }
    (OUT / 'package_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('CB01: 12 STEP/STL/DXF stock-part sets validated', flush=True)


def documents():
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A3, letter
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Paragraph, Table, TableStyle
    from reportlab.lib.styles import ParagraphStyle
    from pypdf import PdfReader, PdfWriter

    a, req, design = inputs()
    m = read(OUT.relative_to(ROOT) / 'package_manifest.json')
    bv = read(OUT.relative_to(ROOT) / 'blender_validation.json')
    assert bv['input_package_sha256'] == sha(OUT / 'package_manifest.json')
    centers = a['centers_installed_mm']
    MM = 72/25.4
    navy, teal, red = '#173b45', '#127b87', '#a33d24'
    style = ParagraphStyle('body', fontName='Helvetica', fontSize=9.5, leading=13.5, textColor=colors.HexColor(navy))
    small = ParagraphStyle('small', parent=style, fontSize=8, leading=11)

    def para(c, text, x, y, width, st=style):
        p = Paragraph(text, st)
        _, h = p.wrap(width, 2000)
        p.drawOn(c, x, y-h)
        return y-h-9

    def table(c, rows, x, y, widths):
        vals = [[Paragraph(str(v), small) for v in row] for row in rows]
        t = Table(vals, colWidths=widths)
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#dfedef')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'), ('GRID', (0,0), (-1,-1), .3, colors.HexColor('#9db2b5')),
            ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5)]))
        _, h = t.wrap(2000, 2000)
        t.drawOn(c, x, y-h)
        return y-h-10

    def image(c, path, x, y, w, h):
        im = ImageReader(str(path)); iw, ih = im.getSize(); scale = min(w/iw, h/ih)
        c.drawImage(im, x+(w-iw*scale)/2, y+(h-ih*scale)/2, iw*scale, ih*scale, mask='auto')

    def head(c, title, page, size=letter):
        w, h = size
        c.setFillColor(colors.HexColor(navy)); c.setFont('Helvetica-Bold', 18)
        c.drawString(34, h-43, title)
        c.setFont('Helvetica', 9); c.drawString(34, h-61, 'CB01 | R005 reference geometry | millimeters | 2026-10-15')
        c.setStrokeColor(colors.HexColor(teal)); c.line(34, h-72, w-34, h-72)
        c.setFillColor(colors.HexColor(red)); c.setFont('Helvetica-Bold', 9)
        c.drawString(34, 24, 'DRAFT - NOT FOR FABRICATION | Physical fit and release pending')
        c.setFillColor(colors.HexColor(navy)); c.drawRightString(w-34, 24, str(page))

    def profile(c, part, x, y, scale, cover=False, dimensions=False):
        dxf = ezdxf.readfile(OUT / part['dxf'])
        c.saveState(); c.translate(x, y); c.scale(scale, scale)
        c.setStrokeColor(colors.HexColor(teal)); c.setLineWidth(.6/scale)
        for ent in dxf.modelspace():
            if ent.dxftype() == 'CIRCLE':
                ce=ent.dxf.center; c.circle(ce.x, ce.y, ent.dxf.radius, stroke=1, fill=0)
            else:
                points = list(make_path(ent).flattening(.015))
                path=c.beginPath(); path.moveTo(points[0].x, points[0].y)
                for p in points[1:]: path.lineTo(p.x, p.y)
                c.drawPath(path)
        radius = part['diameter_mm']/2
        c.setStrokeColor(colors.HexColor('#839497')); c.setDash(3/scale, 3/scale)
        c.line(-radius-5, 0, radius+5, 0); c.line(0, -radius-5, 0, radius+5)
        if cover:
            cd = req['study']['main_cover_diameter_mm'] if part['kind']=='MAIN' else req['study']['diverter_cover_diameter_mm']
            c.circle(0, 0, cd/2)
        c.setDash()
        c.setFont('Helvetica', 9/scale)
        c.drawString(3, 3, 'A / B center')
        c.drawCentredString(0, radius+10, '+Y / UP')
        if dimensions:
            yy=-radius-13
            c.line(-radius, yy, radius, yy)
            c.line(-radius, yy-3, -radius, -radius-2)
            c.line(radius, yy-3, radius, -radius-2)
            c.drawCentredString(0, yy-9, f'DIAMETER {part["diameter_mm"]:g} mm')
        c.restoreState()

    def part_sheet(c, part, page, selected=None):
        head(c, part['id'].rsplit('-',1)[0] + ' | custom backing plate', page)
        y=para(c, 'DATUM A: rear flat face, Z=0. DATUM B: outer-circle center, X=Y=0. '
            '+X right and +Y up when viewed from the shower. The visible outline is concentric with the factory cover.',34,704,544)
        scale=min(340/part['diameter_mm'], 1.9)
        profile(c, part, 285, 450, scale, dimensions=True)
        if selected:
            y=table(c,[['Selected stock for this quote','Nominal thickness','Material'],
                       [selected['id'],selected['thickness_mm'],selected['material']]],34,235,[160,100,284])
        else:
            y=table(c,[['Stock trial','Thickness (mm)','Use / material']]+[
                [s['id'],s['thickness_mm'],s['material']] for s in design['stock_options']],34,235,[100,105,339])
        y=para(c, 'CUT GEOMETRY: STEP/DXF controls; do not scale this drawing. Two closed contours only. '
            + (('Main aperture uses the common coordinate schedule included with these drawings. No separate stud holes.' if selected
                else 'Main aperture uses the common coordinate schedule on sheet 6. No separate stud holes.') if part['kind']=='MAIN'
               else 'Central aperture is diameter 80 mm, concentric. This diverter clearance remains a trial.'),34,y,544,small)
        y=para(c, 'Finish concept: satin/brushed face, direction vertical; color match to Kohler BN is unverified. '
            'Deburr both faces; no sharp edges or burrs against foam/stone. Shop to confirm size, thickness, flatness and edge tolerances. '
            'No numerical manufacturing tolerance or seal compression has been released.',34,y,544,small)
        assert y > 35, ('part sheet overflow', y)
        c.showPage()

    blueprint=OUT/'concentric_blueprints_CB01_DRAFT.pdf'
    c=canvas.Canvas(str(blueprint), pagesize=letter)
    head(c,'Concentric escutcheon pair comparison',1)
    image(c,OUT/'views/C1_front.png',34,335,263,355)
    image(c,OUT/'views/C2_front.png',315,335,263,355)
    y=table(c,[['Pair','Main / diverter OD','Border widths','Gap','Worst main margin']]+[
        [v['id'],f"{v['main_diameter_mm']:g} / {v['diverter_diameter_mm']:g}",
         f"{v['main_border_mm']:.2f} / {v['diverter_border_mm']:.2f}",f"{v['gap_mm']:.2f}",f"{v['minimum_main_margin_mm']:.2f}"]
        for v in a['variants']],34,323,[45,135,125,70,169])
    y=para(c,'Both pairs use circular outlines with zero intentional offset from their own covers. C1 keeps more main coverage. '
        'C2 gives both covers the same 15 mm border. Main cover OD is measured; diverter cover OD and installed centers remain provisional.',34,y,544)
    y=para(c,'Margins are projected distances beyond traced damage, after existing trace allowances. They are not proven sound sealing land. '
        'Both options fall below the earlier exploratory 10 mm main-land target. Assembly images show a conditional appearance using official Kohler exterior meshes; actual stud/foam/depth fit is unresolved.',34,y,544)
    y=para(c,'Sensitivity example: if each actual cover center were within 1 mm of its model location, worst-case gaps would be '
        f"{a['variants'][0]['gap_mm']-2:.2f} mm (C1) and {a['variants'][1]['gap_mm']-2:.2f} mm (C2). "
        'That 1 mm bound has not been measured. A 2 mm bound would erase the C2 gap. Scan scale and support uncertainty remain additional.',34,y,544,small)
    assert y>35, ('comparison page overflow',y)
    c.showPage()
    baseparts=[next(p for p in m['parts'] if p['id']==f'{kind}-{vid}-SS060') for vid in ['C1','C2'] for kind in ['MAIN','DIV']]
    for page,part in enumerate(baseparts,2):part_sheet(c,part,page)
    head(c,'Common main aperture | coordinate schedule',6)
    y=para(c,'The two main plates use the same insertion aperture in installed coordinates. Below are the base polygon vertices relative '
        'to each concentric cover center; apply an OUTWARD 1.75 mm round offset. The supplied STEP/DXF contains the final offset contour. '
        'Rounded table values are reference only; files control. Traverse P01-P20 and close.',34,704,544)
    center=centers['MAIN']
    points=design['aperture']['base_convex_polygon_installed_mm']
    rows=[['Point','X (mm)','Y (mm)','Point','X (mm)','Y (mm)']]
    half=math.ceil(len(points)/2)
    for i in range(half):
        row=[]
        for j in [i,i+half]:
            row += [f'P{j+1:02}',f'{points[j][0]-center[0]:.3f}',f'{points[j][1]-center[1]:.3f}'] if j<len(points) else ['','','']
        rows.append(row)
    y=table(c,rows,34,y,[65,103,104,65,103,104])
    y=para(c,'Do not recenter this aperture within the custom outline independently. It is registered to captured hardware; the outer '
        'circle is registered to the inferred cover center. Later physical registration may change their relationship.',34,y,544)
    y=para(c,'The unchanged F005 aperture cleared all 51,929 checked forward-surface triangle projections. That test concerns the '
        'captured mesh only, not hidden surfaces or actual scale. The rear foam band remains untraced; the aperture may cross the real seal land.',34,y,544)
    y=para(c,'Drawing datums and cut path are not installation locators. Before release, use the real cover as a reference and verify '
        'equal exposure around its perimeter during a thickness-correct dry fit. If center offset is e, ideal circular border variation '
        'is 2e peak-to-peak. No allowable e has been selected.',34,y,544)
    c.showPage()
    head(c,'Exploded order | unchanged hardware concerns',7)
    image(c,OUT/'views/C1_exploded.png',34,265,365,425)
    y=704
    for text in ['<b>From the wall outward</b>', '1. Qualified support / seal detail - unresolved.',
                 '2. Custom backing plate.', '3. Existing factory foam and inner plate.',
                 '4. Factory nuts behind the cover.', '5. Decorative cover, adapters and handles.']:
        y=para(c,text,411,y,167)
    y=para(c,'Exploded positions are display offsets, not installed dimensions. The pink foam is a footprint hypothesis. '
        'F005 had stud-region clashes with its reference plates; none at the controls in those tested positions. '
        'That conditional result does not establish handle engagement or water sealing.',34,242,544)
    y=para(c,'The reported studs touching wood have not been traced to their rear ends. No cutting, drilling, valve relocation or '
        'hardware adjustment is selected. Separate accessible support screws are visible in the front photographs.',34,y,544)
    y=para(c,'Covers and handles use official Kohler exterior CAD for appearance; their hidden rear interfaces are not measurement authority. '
        'Original scan/proxy geometry, topology, UVs and transforms were preserved in the saved Blender file.',34,y,544)
    c.showPage()
    head(c,'Fit record needed before a metal release',8)
    y=para(c,'New caliper center readings are preserved as a separate reconciliation study. They have not silently moved the captured '
        'valve, studs, aperture or cover registration used in these files.',34,704,544)
    report=read('docs/physical_checks/installed_center_distances_2026-10-15.json')
    y=table(c,[['Tip-center pair','Reported mm']]+[[f"{o['feature_a']} to {o['feature_b']}",o['value_mm']] for o in report['observations']],34,y,[300,244])
    y=para(c,'U/L = upper/lower control; NE/SW = upper-right/lower-left trim stud. The user confirms 3D end-tip-center distances '
        'at unequal depths. These are not wall-plane hole spacings. See sheet 11 for depth correction; contact repeatability remains unknown.',34,y,544)
    for text in [
        '<b>1. Rear foam:</b> trace both edges on the full-size template; confirm continuous landing, condition and intended drainage.',
        '<b>2. Hardware:</b> measure stud diameter and axes at the intended plate plane; measure stud/control projection and the actual cover cavity/nut seats.',
        '<b>3. Placement:</b> check real cover centers, diverter OD, equal visible borders, worst gouges, inter-plate clearance and sound support.',
        '<b>4. Thickness:</b> PROTO3 is 1.476 mm thicker than SS060 and 0.175 mm thinner than SS125. A 3 mm prototype cannot prove the thin-metal stack; use the selected actual thickness for final dry fit.',
        '<b>5. Assembly:</b> verify factory plate seating, foam compression, handle engagement/travel, drainage, removal and tool access.',
        '<b>6. Release:</b> resolve the support/seal construction, material/finish and shop tolerances; obtain revision-specific approval. Then inspect the received parts and test for water entry after installation.'
    ]:y=para(c,text,34,y,544,small)
    assert y>35, ('fit page overflow',y)
    c.showPage()
    loc=read(OUT.relative_to(ROOT)/'stud_locator_analysis.json')
    head(c,'Upper-only locating tabs | diagnostic trial',9)
    image(c,OUT/'views/stud_locator_trial.png',34,390,544,295)
    y=para(c,'A concrete C1 upper-plate trial retains metal at the two fitted stud positions: an exploratory 7.5 mm round hole '
        'at NE and a 7.5 x 12 mm slot at SW, along the stud-pair line, in 14 mm wide tabs. '
        'These are design trials, not measurements or released hole sizes. The lower companion stays unchanged.',34,375,544)
    y=table(c,[['Test against unchanged captured surfaces','Projected intersection'],
        ['Integral-tab insertion sweep',f"{loc['integral_tabs_insertion_sweep']['projected_conflict_area_mm2']:.2f} mm2"],
        ['Final slab Z=1 to 2.524 mm',f"{loc['removable_tabs_seated_plane']['projected_conflict_area_mm2']:.2f} mm2"]],34,y,[385,159])
    y=para(c,'The trial holes do not clear the unchanged scanned stud regions. This compares fitted tip locations with captured '
        'surfaces and assumed normal axes; it does not prove the real tab idea is impossible. The small seated conflict also means '
        'removable bridges do not yet have a proven fit. Actual stud diameter, inclination and rear/cover space are decisive.',34,y,544)
    y=para(c,'Through-hole capture is the current diagnostic approach. Threaded engagement is not selected: thread identity, '
        'engagement length and assembly method are unknown. Nut/washer bearing and restraint remain unverified. '
        'Clearance and a slot allow movement; they do not by themselves guarantee a concentric decorative cover.',34,y,544,small)
    y=para(c,'The diagnostic STEP/STL is separate from all quote packages. No added attachment holes, stud cutting or factory-hole '
        'enlargement is selected. Compare the open-aperture template first, then reconcile the real stud axes before a locating prototype.',34,y,544,small)
    assert y>35, ('locator page overflow',y)
    c.showPage()
    head(c,'Top gouges beneath the visible border',10)
    resolved=read('data/derived/resolved.json')
    meta=read('data/evidence/scan_quality/wall_detail_registered.json')
    pixels=meta['pixels'];factor=pixels/meta['span_mm'];cx,cy=meta['center_installed_mm'][:2]
    def top_reveal(v,x,y,w,h):
        vx,vy,vw,vh=500,150,1250,470
        sc=min(w/vw,h/vh)
        def xy(pt):
            px=pixels/2+(pt[0]-cx)*factor;py=pixels/2-(pt[1]-cy)*factor
            return x+(px-vx)*sc,y+(vy+vh-py)*sc
        c.saveState();clip=c.beginPath();clip.rect(x,y,vw*sc,vh*sc);c.clipPath(clip,stroke=0)
        c.drawImage(str(ROOT/'data/evidence/scan_quality/wall_detail_registered.png'),x-vx*sc,y+(vy+vh-pixels)*sc,pixels*sc,pixels*sc)
        mx,my=xy(centers['MAIN']);outer=v['main_diameter_mm']/2*factor*sc;inner=req['study']['main_cover_diameter_mm']/2*factor*sc
        band=c.beginPath();band.circle(mx,my,outer);band.circle(mx,my,inner)
        c.saveState();c.setFillColor(colors.HexColor('#187fa1'));c.setFillAlpha(.24);c.drawPath(band,fill=1,stroke=0,fillMode=0);c.restoreState()
        labels={'CUT-01':(-55,158),'CUT-02':(6,154),'CUT-03':(75,148)}
        for f in resolved['features']:
            if f['id'] not in labels:continue
            pts=[xy(pt) for pt in f['contour_mm']]
            path=c.beginPath();path.moveTo(*pts[0])
            for pt in pts[1:]:path.lineTo(*pt)
            path.close();c.setStrokeColor(colors.HexColor('#a26500' if f['status']=='unknown' else '#b72720'));c.setLineWidth(1.3)
            c.setDash(4,3) if f['status']=='unknown' else c.setDash()
            c.drawPath(path);lx,ly=xy(labels[f['id']]);c.setFont('Helvetica-Bold',9)
            c.setFillColor(colors.white);c.rect(lx-22,ly-3,44,14,stroke=0,fill=1)
            c.setFillColor(colors.HexColor('#a26500' if f['status']=='unknown' else '#b72720'))
            c.drawCentredString(lx,ly,f['id']+('?' if f['status']=='unknown' else ''))
        c.setDash();c.setLineWidth(1.4);c.setStrokeColor(colors.HexColor('#006987'));c.circle(mx,my,outer)
        c.setStrokeColor(colors.HexColor('#b07800'));c.circle(mx,my,inner)
        c.restoreState()
    for v,y in zip(a['variants'],[465,190]):
        c.setFillColor(colors.HexColor(navy));c.setFont('Helvetica-Bold',12);c.drawString(34,y+218,v['id']+' - top damage reveal')
        top_reveal(v,34,y,544,205)
        net=v['minimum_main_margin_mm'];raw=net+1.5
        para(c,f'CUT-03: 9.02 mm beyond the factory-cover edge; {raw:.2f} mm to the custom outer edge '
            f'({net:.2f} mm after the 1.5 mm tracing allowance).',34,y-9,544,small)
    para(c,'Blue: exposed custom border. Gold: factory-cover edge. Red: retained cut traces. Dashed amber CUT-02 remains uncertain. '
        'These are registered evidence overlays on the original scan render, not a finished transparent plate. '
        'The browser damage view also includes the full opening and the uncertain CUT-07 mark. Margins do not prove sound support or sealing.',34,118,544,small)
    c.showPage()
    head(c,'Tip distances and the tile plane',11)
    recon=read('deliverables/current/analysis/center_reconciliation_DRAFT.json')
    y=para(c,'The six caliper readings are straight-line distances between the centers of projecting ends. Their different depths '
        'are part of each reading. Preserve these original numbers; compare them with 3D scan distances first.',34,704,544)
    c.setStrokeColor(colors.HexColor('#186d86'));c.setLineWidth(2)
    c.line(85,535,460,625)
    c.setDash(5,3);c.setStrokeColor(colors.HexColor('#577981'));c.line(85,535,460,535);c.line(460,535,460,625);c.setDash()
    c.setFillColor(colors.HexColor('#186d86'))
    for x,y in [(85,535),(460,625)]:c.circle(x,y,4,fill=1,stroke=0)
    c.setFont('Helvetica-Bold',11);c.drawString(50,516,'Tip A');c.drawString(470,625,'Tip B')
    c.drawCentredString(270,604,'Measured 3D tip distance')
    c.setFont('Helvetica',10);c.drawCentredString(270,516,'Projected separation within the tile plane')
    c.drawString(469,571,'Depth difference')
    c.drawCentredString(306,489,'d_XY = sqrt(d_3D squared - delta_Z squared)   |   schematic, not to scale')
    rows=[['Pair','Raw 3D','Scan delta Z','Conditional XY','Reduction']]
    for row in recon['comparison']:
        rows.append(['-'.join(row['endpoints']),f"{row['raw_caliper_mm']:.2f}",
                     f"{row['baseline_scan_absolute_delta_Z_mm']:.3f}",
                     f"{row['conditional_caliper_XY_using_baseline_scan_depth_mm']:.3f}",
                     f"{row['conditional_depth_correction_mm']:.3f}"])
    y=table(c,rows,34,465,[70,100,110,134,130])
    y=para(c,'All values above are mm. The converted values use unchanged baseline scan depths, so they are conditional illustrations, '
        'not accepted CAD dimensions. Even projected tip centers can differ from stud-axis locations at the plate plane when a stud is inclined.',34,y,544)
    y=para(c,'Allowing depth to vary, all six reported lengths fit a 3D four-tip arrangement exactly. Both mirror branches are retained '
        'as separate diagnostic estimates. The distances alone do not locate that arrangement relative to the wall; matching the same '
        'six inputs does not establish measurement accuracy. The earlier fixed-depth fit retains scan depths and is only a sensitivity trial.',34,y,544)
    y=para(c,'Keep four quantities separate: measurement/registration uncertainty, clearance needed to slide and seat the assembly, '
        'shop cutting/position tolerance, and the sealing/support land. Neither the depth correction nor a small fitting residual is '
        'a machining tolerance. No numerical tolerance has been released.',34,y,544)
    assert y>35, ('3D measurement page overflow',y)
    c.showPage();c.save()

    templates=OUT/'full_size_templates_CB01_DRAFT.pdf'
    c=canvas.Canvas(str(templates),pagesize=A3)
    for n,part in enumerate(baseparts,1):
        head(c,part['id'].rsplit('-',1)[0]+' | 1:1 planar template',n,A3)
        para(c,'PRINT AT 100% / ACTUAL SIZE. Disable fit-to-page. Verify BOTH 100 mm bars before use. '
            'Dashed circle = factory-cover reference; solid contours = custom plate. Lines are reference marks, not extra cut paths.',34,A3[1]-90,A3[0]-68)
        profile(c,part,A3[0]/2,245*MM,MM,cover=True)
        c.setStrokeColor(colors.HexColor(navy));c.setLineWidth(.7)
        for x1,y1,x2,y2 in [(35,65,135,65),(17,180,17,280)]:
            c.line(x1*MM,y1*MM,x2*MM,y2*MM)
            if y1==y2:
                c.line(x1*MM,(y1-2)*MM,x1*MM,(y1+2)*MM);c.line(x2*MM,(y2-2)*MM,x2*MM,(y2+2)*MM)
            else:
                c.line((x1-2)*MM,y1*MM,(x1+2)*MM,y1*MM);c.line((x2-2)*MM,y2*MM,(x2+2)*MM,y2*MM)
        c.setFillColor(colors.HexColor(navy));c.setFont('Helvetica',10)
        c.drawString(35*MM,60*MM,'100 mm horizontal check')
        c.saveState();c.translate(12*MM,180*MM);c.rotate(90);c.drawString(0,0,'100 mm vertical check');c.restoreState()
        para(c,'Record: date ______  measured horizontal ______  vertical ______ mm<br/>'
            'Trace the real rear foam inner/outer edges and mark any overlap with the aperture. '
            'Mark cover center, gouges, unsupported spans and interference. Paper checks planar relationships only; '
            'it cannot prove thickness, compression, stiffness, handle engagement or water performance.',35*MM,110*MM,A3[0]-70*MM)
        c.showPage()
    c.save()

    # Each private-free quote ZIP has one pair/stock, clean contours and its two specific sheets.
    package_files=[]
    temp=ROOT/'build/concentric_packages';temp.mkdir(parents=True,exist_ok=True)
    for variant in a['variants']:
        vid=variant['id']
        for stock in design['stock_options']:
            sid=stock['id']; drawing=temp/f'{vid}_{sid}_drawings.pdf'
            c=canvas.Canvas(str(drawing),pagesize=letter)
            selectedparts=[p for p in m['parts'] if p['variant']==vid and p['stock']==sid]
            for n,part in enumerate(selectedparts,1):part_sheet(c,part,n,stock)
            # Include common main aperture schedule from the final blueprint, without home photos.
            c.save();writer=PdfWriter()
            for page in PdfReader(drawing).pages:writer.add_page(page)
            writer.add_page(PdfReader(blueprint).pages[5])
            with drawing.open('wb') as f:writer.write(f)
            notes=(f'CB01 {vid} {sid} - DRAFT, QUOTE / PROTOTYPE REVIEW ONLY.\n'
                f'One main plate and one diverter plate. {stock["material"]}; nominal thickness {stock["thickness_mm"]} mm.\n'
                'No manufacture/order authorization. STEP/DXF units mm. STL numerics are mm, a unitless format.\n'
                'Only the two custom parts are supplied; no Kohler replacement part or home scan.\n'
                'Local XY origin is each outer circle center, rear Z=0. DXF has exactly two closed contours.\n'
                'Stock dimensions, flatness, edge quality, finish and position tolerances require shop confirmation.\n'
                'Support, rear foam landing, stud/cover/handle fit, centering and water sealing remain unresolved.\n'
                'Clear acrylic / printed plastic trials are for dry fit only, not permanent wet service.\n')
            name=f'quote_{vid}_{sid}_CB01_DRAFT.zip';dest=OUT/name
            payload={}
            for part in selectedparts:
                for ext in ['step','stl','dxf']:payload[Path(part[ext]).name]=(OUT/part[ext]).read_bytes()
            payload['selected_pair_drawings_DRAFT.pdf']=drawing.read_bytes()
            payload['READ_ME.txt']=notes.encode()
            payload['SHA256.json']=json.dumps({k:hashlib.sha256(v).hexdigest() for k,v in payload.items()},indent=2).encode()
            with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
                for name_,data in payload.items():z.writestr(name_,data)
            with zipfile.ZipFile(dest) as z:
                assert not any(p.endswith(('.png','.jpg','.blend','.obj')) for p in z.namelist())
                for page in PdfReader(drawing).pages:assert not page.images
                assert len(z.namelist())==9
            package_files.append({'variant':vid,'stock':sid,'file':name,'sha256':sha(dest),'CAD_parts':2,'drawing_pages':3})

    cards=[]
    projection_rows=''.join('<tr><td>'+ '-'.join(row['endpoints']) + '</td>' + ''.join(
        f'<td>{row[key]:.3f}</td>' for key in ['raw_caliper_mm','baseline_scan_absolute_delta_Z_mm',
            'conditional_caliper_XY_using_baseline_scan_depth_mm','conditional_depth_correction_mm'])+'</tr>'
        for row in recon['comparison'])
    for v in a['variants']:
        vid=v['id']
        links=' '.join(f'<a class="button" href="{p["file"]}">{p["stock"]} pair ZIP</a>' for p in package_files if p['variant']==vid)
        cards.append(f'<article><h2>{vid} · {html.escape(v["name"])}</h2><a href="views/{vid}_front.png"><img src="views/{vid}_front.png" alt="{vid} front appearance on actual travertine"></a>'
            f'<p>Main / diverter: <b>{v["main_diameter_mm"]:g} / {v["diverter_diameter_mm"]:g} mm</b>. '
            f'Borders: {v["main_border_mm"]:.2f} / {v["diverter_border_mm"]:.2f} mm. Gap: {v["gap_mm"]:.2f} mm.</p>'
            f'<p>Minimum projected main damage margin: <b>{v["minimum_main_margin_mm"]:.2f} mm</b>, after tracing allowance.</p>'
            f'<details><summary>Oblique view and quote files</summary><img src="views/{vid}_oblique.png" alt="{vid} oblique appearance"><p>{links}</p></details></article>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Concentric escutcheons · CB01</title><style>
body{margin:0;background:#eef3f3;color:#173b45;font:17px/1.55 system-ui}main{max-width:1140px;margin:auto;padding:30px}h1{font-size:38px;line-height:1.15}h2{font-size:23px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}article,.panel{background:white;padding:20px;border-radius:9px;margin:20px 0}img{display:block;max-width:100%;height:auto}a{color:#086b7b}.button{display:inline-block;border:1px solid #8eafb5;padding:8px 12px;border-radius:5px;margin:6px 8px 6px 0}.flag{border-left:5px solid #ad512f;padding:16px;background:#fff1e7}.small{font-size:14px}.exploded{max-height:680px;margin:auto}summary{cursor:pointer;font-weight:600}@media(max-width:750px){.grid{grid-template-columns:1fr}main{padding:18px}h1{font-size:30px}}
</style><main><h1>A constant border around each cover</h1><p>Two concentric alternatives on your captured travertine, using official Kohler exterior CAD. Each backing outline shares its cover's inferred center, with zero intentional offset.</p>
<p class="flag"><b>DRAFT - NOT FOR FABRICATION.</b> Cover centers, rear foam, hardware depth, support and physical fit remain unresolved. The old F005 offset/rectangular appearances do not satisfy the recorded constant-border requirement. These new options are unselected.</p>
<p><a class="button" href="concentric_blueprints_CB01_DRAFT.pdf">Blueprints and fit notes</a><a class="button" href="full_size_templates_CB01_DRAFT.pdf">1:1 A3 templates</a><a class="button" href="paired_concentric_CB01_DRAFT.blend">Blender workspace</a><a class="button" href="damage.html">Reveal the top gouges and over-cuts</a></p>
<div class="grid">'''+''.join(cards)+'''</div><section class="panel"><h2>What the smaller outlines change</h2><p>Both cover the traced damage at the current model scale. They leave less margin than the offset F005 shapes and both fall below the earlier exploratory 10 mm main-land target. A projected margin does not establish sound support or a watertight landing.</p><p>The insertion aperture is unchanged in installed coordinates. The original scan and captured hardware are preserved. Appearance views hide the captured hardware in a separate cosmetic wall copy; the Blender Observed layer retains it.</p></section>
<section class="panel"><h2>Exploded assembly</h2><img class="exploded" src="views/C1_exploded.png" alt="C1 exploded main and diverter trim"><p>From the wall: unresolved support/seal detail, custom backing plate, factory foam and inner plate, factory nuts, decorative cover, adapters and handles. Display offsets are not installed depths. The pink foam footprint is still hypothetical.</p></section>
<section class="panel"><h2>Before choosing a metal part</h2><p>Trace both rear foam edges on the template; check actual cover centers and equal exposure; reconcile stud diameter, axes and projection with the real plate and cover cavity. Then dry-fit the selected thickness with the factory parts and verify support, drainage, handle engagement and removal.</p><p>SS060 is 1.524 mm; SS125 is 3.175 mm; PROTO3 is 3 mm. The 3 mm trial is 1.476 mm thicker than SS060 and 0.175 mm thinner than SS125, so it cannot prove either metal depth stack without a thickness-correct check.</p><p>Six new center readings are preserved separately. Their fitted estimates have not silently replaced the R005/F005 placements used here. <a href="../../analysis/center_reconciliation_DRAFT.txt">Read the reconciliation</a>.</p></section>
<section class="panel" id="tip-depth"><h2>Your caliper readings include depth</h2><p>The six readings are confirmed <b>3D end-tip-center distances</b>. Their projection into the tile plane is shorter when the two tips have different depths: <b>dXY = √(d3D² − ΔZ²)</b>.</p><p>Using the current scan depths gives the conditional reductions below. These are illustrations, not accepted hole spacings; stud inclination also affects the centers at the plate plane.</p><div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%;text-align:left" cellpadding="8"><thead><tr><th>Pair</th><th>Raw 3D</th><th>Scan ΔZ</th><th>Conditional XY</th><th>Reduction</th></tr></thead><tbody>'''+projection_rows+'''</tbody></table></div><p class="small">All values in mm. The extra decimals support calculation review and do not establish accuracy.</p><p>When depth is allowed to vary, all six readings fit a 3D arrangement exactly. They do not determine its orientation or depth relative to the wall. Both mirror branches are kept as diagnostic estimates; the older fixed-scan-depth trial remains separate.</p><p>Measurement uncertainty, assembly clearance, machining tolerance and sealing support are separate requirements. The depth correction and fit residuals are not machining tolerances. <a href="concentric_blueprints_CB01_DRAFT.pdf#page=11">See the depth diagram on sheet 11</a>.</p></section>
<section class="panel"><h2>Upper-only screw-locating alternative</h2><img src="views/stud_locator_trial.png" alt="Locating tabs compared with captured hardware during insertion and at the seated plane"><p>The new trial adds metal around one round clearance hole and one slot, using the fixed-scan-depth reconciled tip-center state. It intersects the unchanged scanned stud regions, so it is retained as a diagnostic model while actual stud axes, diameters, nut bearing and cover depth are reconciled. This is a source/model conflict, not proof that the physical idea is impossible. Free-depth fits are retained separately and have not been substituted for hole coordinates.</p><p>Threaded engagement is unselected; the thread and engagement are unknown. Removable bridges could change the insertion sequence, but their seated clearance and retention still need resolution. Hole clearance alone does not guarantee centering on the actual cover.</p><p><a href="stud_locator_analysis.json">Locator collision analysis</a> · <a href="reconciled_model_state.json">Separate fitted model state</a> · <a href="diagnostic/MAIN-C1_LOC01_TAB_TRIAL_NOT_FOR_FABRICATION.step">Diagnostic upper STEP</a> · <a href="diagnostic/MAIN-C1_LOC01_TAB_TRIAL_NOT_FOR_FABRICATION.stl">Diagnostic upper STL</a>. This trial is excluded from the quote packages.</p></section>
<p class="small"><a href="analysis.json">Coverage calculations</a> · <a href="package_manifest.json">CAD hashes and stock checks</a> · <a href="blender_validation.json">Saved Blender checks</a> · <a href="../F005/index.html">Historical F005 research and diagnostics</a>. No files uploaded or orders placed. Quote ZIPs contain only the selected custom pair, clean cut files, drawings and notes.</p></main></html>'''
    (OUT/'index.html').write_text(page)
    validation={'status':'GENERATED - visual QA pending','pdf_pages':{blueprint.name:len(PdfReader(blueprint).pages),templates.name:len(PdfReader(templates).pages)},
                'quote_packages':package_files,'quote_package_privacy':'PASS: no raster photos or scan assets','raw_measurements_modified':False}
    (OUT/'document_validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    print(json.dumps(validation,indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['cad','documents']);args=p.parse_args()
    cad() if args.stage=='cad' else documents()
