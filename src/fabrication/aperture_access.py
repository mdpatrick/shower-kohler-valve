"""AP01: explicit control access, captured insertion and edge-flush gasket checks.

Read-only measurement/design inputs. F005/CB01 solids stay historical; these
upright-aperture alternatives are separate, unselected dry-fit candidates.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import os

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'deliverables/current/fabrication/aperture-access'
CACHE = ROOT / 'build/aperture_access'
os.environ.setdefault('MPLCONFIGDIR', str(CACHE / 'matplotlib'))
import numpy as np
import cadquery as cq
import ezdxf
import trimesh
from shapely.geometry import Point, Polygon, box
from shapely.affinity import translate
from shapely import contains_xy, points, distance
from shapely.ops import unary_union, nearest_points
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PatchPolygon, Circle, Rectangle
from matplotlib.collections import PolyCollection
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A3
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle


def read(name):
    return json.loads((ROOT / name).read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, value):
    p.write_text(json.dumps(value, indent=2) + '\n')


def rr(w, h, r, c):
    return translate(box(-w/2+r, -h/2+r, w/2-r, h/2-r).buffer(r, quad_segs=128), *c)


def solid_rr(w, h, r, t):
    return cq.Workplane('XY').rect(w, h).extrude(t).edges('|Z').fillet(r)


def captured_surface(r, reg, old, upright):
    """Recheck every triangle, not just fitted landmarks or plotted samples."""
    T = np.array(reg['raw_to_installed_mm'])
    v = np.load(ROOT/'data/derived/shower-hole-valve-polycam-vertices.npy') @ T[:3, :3].T + T[:3, 3]
    fs = []
    for line in (ROOT/'data/extracted/shower-hole-valve-polycam/10_14_2026.obj').open():
        if line.startswith('f '):
            ids = [int(s.split('/')[0])-1 for s in line.split()[1:]]
            fs.extend((ids[0], ids[i], ids[i+1]) for i in range(1, len(ids)-1))
    faces = np.asarray(fs)
    region = Polygon(next(f['contour_mm'] for f in r['features'] if f['id'] == 'OPEN-MAIN')).buffer(-3)
    b = region.bounds
    tri = v[faces]
    keep = ((tri[:, :, 2].max(1) >= .5) & (tri[:, :, 0].max(1) >= b[0]) &
            (tri[:, :, 0].min(1) <= b[2]) & (tri[:, :, 1].max(1) >= b[1]) &
            (tri[:, :, 1].min(1) <= b[3]))
    selected_faces = faces[keep]
    counts = [0, 0]
    conflicts = [[], []]
    considered = 0
    for tr in tri[keep]:
        poly = []
        for i, p in enumerate(tr):
            q = tr[(i+1) % 3]
            a, z = p[2] >= .5, q[2] >= .5
            if a:
                poly.append(p)
            if a != z:
                poly.append(p + (.5-p[2])/(q[2]-p[2]) * (q-p))
        if len(poly) < 3:
            continue
        piece = Polygon([(q[0], q[1]) for q in poly])
        if piece.area < 1e-9:
            continue
        if not piece.is_valid:
            piece = piece.buffer(0)
        clip = piece.intersection(region)
        if clip.area < 1e-9:
            continue
        considered += 1
        for i, aperture in enumerate([old, upright]):
            outside = clip.difference(aperture)
            if outside.area > 1e-7:
                counts[i] += 1
                conflicts[i].append(outside)
    samples = v[(v[:, 2] >= .5) & contains_xy(region, v[:, 0], v[:, 1])]
    result = {
        'triangles_considered': considered,
        'floor_z_mm': .5,
        'mask': 'OPEN-MAIN eroded 3 mm, explicitly excludes the stone border',
        'method': 'Clip each primary triangle to Z >= 0.5, project XY, intersect mask, compare with each aperture.',
        'old': {'conflict_triangles': counts[0], 'projected_conflict_area_mm2': unary_union(conflicts[0]).area},
        'upright': {'conflict_triangles': counts[1], 'projected_conflict_area_mm2': unary_union(conflicts[1]).area},
        'vertices_considered': len(samples),
        'upright_min_sample_edge_clearance_mm': float(distance(points(samples[:, :2]), upright.boundary).min()),
        'limitations': 'Captured surfaces only; no bounded scan accuracy, hidden components or complete physical volume. Axial insertion normal to the wall only, at/outside Z=0.5.'
    }
    # Separate, openly labeled display crop. Original mesh is never modified.
    crop = trimesh.Trimesh(vertices=v, faces=selected_faces, process=False)
    crop.remove_unreferenced_vertices()
    crop.export(CACHE/'captured_forward_display.stl')
    return result, samples


def export_cad(req):
    q = req['upright_trial']
    parts = []
    for diameter in req['outputs']['main_outer_diameters_mm']:
        variant = 'C1' if diameter == 220 else 'C2'
        for t in req['outputs']['thicknesses_mm']:
            stock = 'SS060' if t == 1.524 else 'SS125'
            name = f'MAIN-{variant}-{stock}_AP01_DRAFT_NOT_FOR_FABRICATION'
            blank = cq.Workplane('XY').circle(diameter/2).extrude(t)
            cutter = solid_rr(q['width_mm'], q['height_mm'], q['corner_radius_mm'], t+2).translate((0, 0, -1))
            part = blank.cut(cutter)
            s = part.val()
            assert s.isValid() and len(s.Solids()) == 1
            paths = {ext: OUT/'cad'/(name+'.'+ext) for ext in ['step', 'stl']}
            cq.exporters.export(s, str(paths['step']))
            cq.exporters.export(s, str(paths['stl']), tolerance=.025, angularTolerance=.05)
            back = cq.importers.importStep(str(paths['step'])).val()
            assert back.isValid() and abs(back.Volume()-s.Volume()) < .01
            expected_area = math.pi*(diameter/2)**2 - (q['width_mm']*q['height_mm']-(4-math.pi)*q['corner_radius_mm']**2)
            assert abs(s.Volume() - expected_area*t) < .001
            m = trimesh.load(paths['stl'], force='mesh')
            assert m.is_watertight and np.max(np.abs(m.extents-[diameter, diameter, t])) < .06
            dxf_check = None
            if t == 1.524:
                path = OUT/'cad'/f'MAIN-{variant}_AP01_CUT_ONLY_DRAFT_NOT_FOR_FABRICATION.dxf'
                wires = part.faces('>Z').wires().translate((0, 0, -t))
                assert len(wires.vals()) == 2
                cq.exporters.export(wires, str(path), exportType='DXF')
                doc = ezdxf.readfile(path)
                doc.units = ezdxf.units.MM
                doc.saveas(path)
                assert all(e.dxftype() in {'CIRCLE', 'LINE', 'ARC'} for e in doc.modelspace())
                rebuilt = cq.importers.importDXF(str(path)).wires().toPending().extrude(t)
                assert abs(rebuilt.val().Volume()-s.Volume()) < .02
                paths['dxf'] = path
                dxf_check = 'PASS: two closed contours, mm, no annotations; round-trip volume matches'
            parts.append(dict(id=name, outer_diameter_mm=diameter, thickness_mm=t,
                              aperture_mm=[q['width_mm'], q['height_mm'], q['corner_radius_mm']],
                              volume_mm3=s.Volume(), STEP_roundtrip='PASS', STL_watertight=True,
                              DXF_check=dxf_check,
                              files={ext:str(p.relative_to(OUT)) for ext,p in paths.items()},
                              sha256={ext:sha(p) for ext,p in paths.items()}))
    return parts


def figures(req, r, old, upright, outer, foam_inner, samples, result):
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11})
    c = np.asarray(r['inner_center_mm'])
    measured_center = c + r['inner_control_openings'][1]['center_local_mm']
    lower_center = c + r['inner_control_openings'][0]['center_local_mm']
    fig, axes = plt.subplots(1, 2, figsize=(12, 8.1), sharex=True, sharey=True)
    for ax, hole, title in zip(axes, [old, upright], ['Old: scan-derived diagonal opening', 'AP01: upright opening, 116.35 × 151.10, R33']):
        ax.add_patch(Circle(c, 110, facecolor='#e1edf0', edgecolor='#617981', lw=1))
        ax.add_patch(PatchPolygon(np.asarray(hole.exterior.coords), facecolor='white', edgecolor='#16768c', lw=2))
        # Foam band as clipped segments between the two boundaries; outer edge meets metal.
        xy1=np.asarray(outer.exterior.coords);xy2=np.asarray(foam_inner.exterior.coords)
        assert len(xy1)==len(xy2)
        for i in range(len(xy1)-1):
            ax.add_patch(PatchPolygon([xy1[i],xy1[i+1],xy2[i+1],xy2[i]], facecolor='#e4b25a', edgecolor='none', alpha=.65))
        ax.plot(*outer.exterior.xy, color='#606970', lw=1)
        ax.plot(*foam_inner.exterior.xy, color='#b78227', lw=1)
        subset=samples[::max(1,len(samples)//6000)]
        ax.scatter(subset[:,0],subset[:,1], s=.4, c='#65727b', alpha=.32, rasterized=True)
        ax.add_patch(Circle(measured_center,24.23,facecolor='none',edgecolor='#72509a',lw=2))
        ax.add_patch(Circle(r['controls_mm'][1][:2],16.895,facecolor='none',edgecolor='#72509a',lw=1,ls=':'))
        ax.add_patch(Circle(lower_center,25,facecolor='none',edgecolor='#72509a',lw=1.5,ls='--'))
        for label,p in zip(['L','U','SW','NE'],r['controls_mm']+r['studs_mm']):
            ax.plot(p[0],p[1],'+',color='#172c34',ms=8)
            ax.annotate(label,(p[0],p[1]),xytext=(6,5),textcoords='offset points',fontsize=12)
        u=np.array(r['controls_mm'][1][:2]);rad=hole.boundary.distance(Point(*u))
        edge = nearest_points(Point(*u), hole.boundary)[1]
        ax.annotate(f'U → nearest edge: {rad:.1f} mm', xy=(edge.x,edge.y),xytext=(0,132),
                    ha='center',fontsize=10,arrowprops={'arrowstyle':'->','color':'#16768c'},color='#16768c')
        ax.set_title(title,fontsize=12,pad=13)
        ax.set(xlim=(-91,91),ylim=(-49,143),xlabel='Installed X (mm)')
        ax.set_aspect('equal');ax.grid(alpha=.15)
    axes[0].set_ylabel('Installed Y (mm)')
    fig.suptitle('Give the connections room, while keeping the foam on metal',fontsize=17,y=.98)
    fig.text(.5,.065,'Gold: approximate 6 mm edge-flush foam • Purple solid: measured Ø48.46 upper inner opening\n'
             'Purple dotted: Ø33.79 cover opening • Dashed lower Ø50 is unmeasured • Gray: captured forward hardware',
             ha='center',fontsize=11,linespacing=1.6)
    fig.text(.5,.015,'Projected footprints at assumed placement; different depths. A projected overlap alone is not a physical collision.',ha='center',fontsize=10)
    fig.subplots_adjust(left=.07,right=.985,bottom=.15,top=.89,wspace=.13)
    fig.savefig(OUT/'aperture_comparison.png',dpi=175)
    fig.savefig(OUT/'aperture_comparison.svg')
    plt.close(fig)

    # Nominal exterior side view comes from Kohler's actual OBJ-derived components.
    fig,ax=plt.subplots(figsize=(10,10))
    palette=['#8d969d','#8d969d','#9ca6ad','#b5bec2']
    for idx,color in [(0,palette[0]),(1,palette[1]),(2,palette[2]),(3,palette[3])]:
        mesh=trimesh.load(ROOT/f'data/derived/fabrication_F005/KOHLER-T14489-4-{idx}.stl',force='mesh')
        arr=mesh.triangles[:,:,[2,1]].copy()
        arr[:,:,0]+=2.524;arr[:,:,1]+=c[1]
        ax.add_collection(PolyCollection(arr,facecolors=color,edgecolors='none',alpha=1))
    # The backing plate section at U has a clear vertical interval; no invented adapter solid.
    span=upright.intersection(__import__('shapely').geometry.LineString([(r['controls_mm'][1][0],-100),(r['controls_mm'][1][0],180)]))
    ys=[p[1] for p in span.coords];lo,hi=min(ys),max(ys)
    upper_plate_edge = c[1] + math.sqrt(110**2-(r['controls_mm'][1][0]-c[0])**2)
    ax.add_patch(Rectangle((1,hi),1.524,upper_plate_edge-hi,facecolor='#218aa0'))
    ax.add_patch(Rectangle((1,-5),1.524,lo+5 if lo>-5 else 0,facecolor='#218aa0'))
    ax.axvline(0,color='#364d56',lw=1.3)
    ax.axhline(r['controls_mm'][1][1],color='#71519a',lw=1,ls='--',alpha=.6)
    ax.plot(r['controls_mm'][1][2],r['controls_mm'][1][1],'o',ms=7,color='#af5034')
    ax.annotate('U tip from scan\n~32 mm from tile; identity unverified',
                xy=(r['controls_mm'][1][2],r['controls_mm'][1][1]),xytext=(11,42),fontsize=11,
                arrowprops={'arrowstyle':'->','color':'#af5034'},color='#87402a')
    ax.annotate('Actual adapter reach / spline overlap\nnot specified by this exterior CAD',xy=(40,79.8),xytext=(47,22),fontsize=11,
                arrowprops={'arrowstyle':'->','color':'#72509a'},color='#72509a')
    ax.annotate('Handle and bonnet\ninstall from the front',xy=(73,108),xytext=(30,143),fontsize=12,
                arrowprops={'arrowstyle':'->'})
    ax.annotate('AP01 backing\n1.524 mm trial',xy=(1.8,120),xytext=(10,124),fontsize=10,
                arrowprops={'arrowstyle':'->','color':'#218aa0'},color='#16768c')
    ax.text(-1,151,'Tile face',rotation=90,ha='right',va='top',fontsize=10)
    ax.text(11,7,'1 mm bedding is a display assumption. Factory exterior shifted by 2.524 mm.\n'
            'Gasket, inner plate and hidden mating details omitted here; see assembly guide.',fontsize=10)
    ax.set(xlim=(-6,119),ylim=(0,158),xlabel='Installed Z (mm): toward you →',ylabel='Installed Y (mm)')
    ax.grid(alpha=.15)
    ax.set_aspect('equal')
    ax.set_title('Upper control: exterior position and unknown engagement',fontsize=15,pad=20)
    fig.tight_layout();fig.savefig(OUT/'upper_connection_depth.png',dpi=175);fig.savefig(OUT/'upper_connection_depth.svg');plt.close(fig)


def paragraph(c, text, x, y, width=520, size=10):
    p=Paragraph(text,ParagraphStyle('p',fontName='Helvetica',fontSize=size,leading=size*1.42,textColor='#233b45'))
    _,h=p.wrap(width,1000);p.drawOn(c,x,y-h);return y-h-10


def pdf(req,r,result):
    path=OUT/'aperture_access_AP01_DRAFT.pdf'
    c=canvas.Canvas(str(path),pagesize=A4)
    c.setTitle('AP01 aperture access and full-size dry-fit templates')
    def head(title,num):
        w,h=c._pagesize;c.setFillColorRGB(.08,.2,.25);c.setFont('Helvetica-Bold',18);c.drawString(34,h-42,title)
        c.setFont('Helvetica',10);c.drawString(34,h-61,'AP01 / 2026-10-15 / DRAFT - NOT FOR FABRICATION')
        c.setFont('Helvetica',9);c.drawString(34,23,f'Page {num} | mm | No physical fit or manufacturing release')
    head('Aperture clearance around the controls',1)
    c.drawImage(str(OUT/'aperture_comparison.png'),29,345,width=537,height=363,preserveAspectRatio=True)
    y=paragraph(c,'<b>Recommended next dry-fit candidate:</b> centered upright opening 116.35 x 151.10 mm, R33. Circular outer sizes remain C1 diameter 220 mm and C2 diameter 214.15 mm; thickness trials 1.524 or 3.175 mm. No locating tabs or separate stud holes.',34,319)
    y=paragraph(c,f'<b>Recomputed:</b> {result["captured_surface"]["triangles_considered"]:,} clipped forward-surface triangles; no aperture conflict for either shape. Upright contains the old aperture with {result["upright_contains_old_extra_margin_mm"]:.3f} mm minimum extra gap. This is a captured-surface result, not an accuracy bound.',34,y)
    y=paragraph(c,'<b>Foam correction:</b> outer foam edge meets metal, as confirmed. A uniform 6 mm band with the assumed R40 plate corners leaves a nominal 1 mm extra strip before the new opening. Actual corner geometry, minimum band width, alignment and compression remain to be checked.',34,y)
    paragraph(c,'The upper 48.46 mm circle is your measured inner opening, not a measured hub or adapter diameter. The lower 50 mm circle remains a display assumption. Original scans and six 3D tip-to-tip readings are unchanged.',34,y)
    c.showPage();head('The remaining check is axial engagement',2)
    c.drawImage(str(OUT/'upper_connection_depth.png'),98,380,width=400,height=400,preserveAspectRatio=True)
    y=paragraph(c,'<b>Factory sequence:</b> attach the appropriate adapters to the stems, seat the inner plate over the studs, fit the cover, and secure it with handle assemblies on the inner-plate hubs. The complete knobs install from the front. A clear aperture does not determine spline or screw engagement.',34,363)
    y=paragraph(c,'<b>Thickness check:</b> added outward shift is backing thickness plus installed bedding, adjusted for any change in gasket compression. A 1.524 mm sheet with 1 mm assumed bedding shifts the factory plane 2.524 mm. The 3.175 mm sheet with the same bedding shifts it 4.175 mm. Neither is a manufacturer-approved tolerance.',34,y)
    y=paragraph(c,'<b>Dry fit with the real components:</b> verify backing insertion without contact, continuous gasket landing, inner plate and cover seating, both adapters properly seated and secured, intended handle-hub fastening, full operating travel without rubbing, and removal/drainage. Record the tested thickness and bedding; do not infer engagement from the U/L points.',34,y)
    y=paragraph(c,'Wood relief is the user-authorized preferred approach if the trim rods need to retract and other valve/stem depths are acceptable. It does not change stem position. Required pocket dimensions and retained stud engagement remain unspecified. Existing upper-stem rough-in comparison remains conditional on bare-tip identity and scale.',34,y)
    paragraph(c,'Sources: Kohler 1041504-2-F pp. 7-8 (resources.kohler.com/onlinecatalog/pdf/1041504_2.pdf); official T14489-4 OBJ exterior; user R005 readings and October 15 foam-edge/contact clarification. Full inputs, limits and hashes: analysis.json beside this PDF.',34,y,size=9)
    c.showPage()
    for num,diameter in enumerate(req['outputs']['main_outer_diameters_mm'],3):
        c.setPageSize(A3);head(f'Full-size template: outer diameter {diameter:g} mm',num)
        cx,cy=A3[0]/2,A3[1]*.51
        c.saveState();c.translate(cx,cy);c.scale(mm,mm)
        c.setLineWidth(.2);c.setStrokeColorRGB(.05,.3,.4);c.circle(0,0,diameter/2)
        q=req['upright_trial'];c.roundRect(-q['width_mm']/2,-q['height_mm']/2,q['width_mm'],q['height_mm'],q['corner_radius_mm'])
        c.setDash(2,1);c.setStrokeColorRGB(.55,.55,.55);c.roundRect(-65.175,-82.55,130.35,165.1,40)
        c.setStrokeColorRGB(.65,.4,.12);c.roundRect(-59.175,-76.55,118.35,153.1,34)
        c.setDash();c.setStrokeColorRGB(.4,.22,.6)
        for op in r['inner_control_openings']:
            x,y=op['center_local_mm'];c.circle(x,y,op['diameter_mm']/2)
        c.setStrokeColorRGB(.1,.2,.25);c.line(-4,0,4,0);c.line(0,-4,0,4)
        c.restoreState()
        y=paragraph(c,'PRINT AT 100% / ACTUAL SIZE. Disable fit-to-page. Measure both 100 mm bars before using. This paper template checks XY only; use a thickness-correct mockup for the depth/engagement test.',34,A3[1]-91,width=A3[0]-68,size=12)
        paragraph(c,'Blue: cut profile. Gray dashed: assumed inner metal outline. Gold dashed: nominal inner edge of 6 mm foam. Purple: inner-opening footprints (lower diameter unmeasured). Center cross: inferred factory plate center. All outlines upright; physical registration unverified.',34,187,width=A3[0]-150,size=11)
        c.setLineWidth(1);c.setStrokeColorRGB(.1,.25,.3)
        c.line(50,75,50+100*mm,75);c.line(50,70,50,80);c.line(50+100*mm,70,50+100*mm,80)
        c.setFont('Helvetica',10);c.drawString(160,88,'100 mm X')
        c.line(A3[0]-45,75,A3[0]-45,75+100*mm);c.line(A3[0]-50,75,A3[0]-40,75);c.line(A3[0]-50,75+100*mm,A3[0]-40,75+100*mm)
        c.saveState();c.translate(A3[0]-57,170);c.rotate(90);c.drawString(0,0,'100 mm Y');c.restoreState()
        c.showPage()
    c.save()


def html(req,result):
    rows=''.join(f'<tr><td>{p["outer_diameter_mm"]:g}</td><td>{p["thickness_mm"]:g}</td><td>'+ ' · '.join(f'<a href="{path}">{ext.upper()}</a>' for ext,path in p['files'].items())+'</td></tr>' for p in result['CAD'])
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Handle access and upright aperture | AP01</title>
<style>*{box-sizing:border-box}body{margin:0;background:#eef3f4;color:#213c46;font:17px/1.55 system-ui,sans-serif}main{max-width:1190px;margin:auto;padding:28px}h1{font-size:36px;line-height:1.2}h2{font-size:25px;line-height:1.3}section{background:white;border-radius:9px;margin:24px 0;padding:24px}a{color:#086b85}img{display:block;width:100%;height:auto}figure{margin:18px 0}figcaption,.small{font-size:14px;color:#4d6570}.flag{border-left:5px solid #bc7b26;padding:12px 18px;background:#fbf3e6}.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}.grid section{margin:0}th,td{text-align:left;padding:10px;border-bottom:1px solid #d9e1e4}table{border-collapse:collapse;width:100%}li{margin:10px 0}@media(max-width:700px){main{padding:16px}.grid{grid-template-columns:1fr}h1{font-size:29px}section{padding:17px}}</style>
<main><a href="../concentric-border-study/index.html">← Paired circular plate review</a><h1>Room for the connections, then a real engagement check</h1>
<p>The whole knob installs from the front. The custom backing opening must clear the hardware and any rearward-reaching connection parts; the added thickness must also let both handles engage and fasten properly.</p>
<p class="flag"><b>AP01 is the recommended next dry-fit shape.</b> Its upright opening improves access around U and L. Physical handle engagement, gasket support, retention and sealing are still unverified. Earlier CB01 quote files contain the old aperture.</p>
<section><h2>Why the old opening was diagonal</h2><p>It followed the convex outline of selected forward scan surfaces, including the diagonal studs, with a 1.75 mm offset. That produced a compact hardware insertion envelope. It was not a factory-required contour and did not validate the missing adapters or handle attachment.</p>
<figure><img src="aperture_comparison.png" alt="Old diagonal opening and wider upright rounded rectangle, with foam band, actual opening diameters and captured hardware"><figcaption>U and L are original scan tip centers. Measured opening footprints are projected at provisional reference placements. Parts occupy different depths: an XY overlap alone is not a proven collision.</figcaption></figure>
<p><b>U to the nearest aperture edge: 11.3 mm before, 35.9 mm in AP01.</b> The entire measured Ø48.46 upper inner-opening footprint fits inside AP01 at the current reference placement, with about 11.0 mm minimum spare margin. This diameter is an opening measurement, not the adapter or hub outside diameter.</p>
<p>AP01 is 116.35 × 151.10 mm with R33 corners. It contains the complete old buffered opening with a minimum 0.446 mm additional gap. Both main outer circles remain concentric candidates: Ø220 and Ø214.15 mm. No new locating tabs or stud holes have been added.</p>
<p><b>Captured-surface check:</b> '''+f'{result["captured_surface"]["triangles_considered"]:,}'+''' forward triangles were clipped and checked again. Neither aperture conflicts with those captured projections. The check excludes the stone-edge mask and cannot establish hidden hardware, scan accuracy or actual fit.</p></section>
<section><h2>The foam meets the outer plate edge</h2><p>Your correction is now recorded. The 6 mm-wide foam belongs to the removed inner plate and meets its outer metal edge. The earlier explanatory drawing incorrectly showed an inset. The F005 CAD foam already used the flush-edge scenario; this observation now supports that outer-edge choice.</p>
<p>The upright trial sits 7 mm inside the assumed metal outline. A uniform 6 mm band therefore leaves <b>1 mm nominal extra land</b> between the aperture and foam. That remainder is not an accepted tolerance: the R40 corners, local minimum width, registration and compression need physical checking.</p><p><a href="../../review/rear/index.html#foam-and-studs">Corrected foam and rear-contact review</a></p></section>
<section><h2>The knob does not go through this backing plate</h2><figure><img src="upper_connection_depth.png" alt="Side view from official Kohler exterior mesh: upper knob and bonnet in front of backing, scan U tip and unknown inner engagement"><figcaption>Actual Kohler nominal exterior mesh, positioned for the 1.524 mm plate + 1 mm assumed bedding trial. It does not contain authoritative hidden spline/thread geometry. Inner plate and gasket are omitted from this view for clarity; they remain required.</figcaption></figure>
<p><a href="https://resources.kohler.com/onlinecatalog/pdf/1041504_2.pdf#page=7">Kohler's guide, pages 7–8</a>, places adapters on the stems and secures the decorative cover through handle assemblies attached to the inner-plate hubs. The adapter must be the appropriate length for engagement and cover seating.</p>
<p>The aperture addresses side clearance. The depth stack addresses reach. A 1.524 mm plate plus 1 mm assumed bedding moves the factory seating plane outward by 2.524 mm; the 3.175 mm sheet makes that 4.175 mm. Actual bedding and compression may change those numbers. No known spline-overlap margin can currently be subtracted from them.</p>
<p>The previous upper-stem rough-in warning also remains open: the scan tip is about 32 mm beyond tile, roughly 5 mm beyond the nominal bare-upper-tip range <em>if it is the same bare feature and the scan scale is correct</em>. That is a check to resolve, not a confirmed installation defect or an allowable 5 mm tolerance.</p></section>
<div class="grid"><section><h2>What will establish handle fit</h2><ol><li>Slide the thickness-correct backing mockup over the exposed hardware without contact.</li><li>Following the factory sequence, seat and secure the correct adapters, then fit the real foam/inner plate and nuts; confirm a continuous landing.</li><li>Fit the decorative cover and fasten both handles by their intended interfaces. Confirm they engage without bottoming, slipping or using screw force to pull a mismatch together.</li><li>Check the full intended handle motion, cover drainage and later removal. Record thickness, bedding and each result.</li></ol><p>These checks are still unperformed. Paper checks alignment only.</p></section>
<section><h2>Wood contact is now confirmed by you</h2><p>The rods meet the wood surface. Clearance holes in that wood are your preferred, authorized approach if inward trim-stud adjustment is needed and the other depth checks pass.</p><p>That would permit the rods to retract through their valve threads. It would not move U, L or the valve body. Required travel, retained thread engagement, wood role and clear drilling path determine the eventual relief dimensions; no pocket size is prescribed here.</p></section></div>
<section id="files"><h2>Updated dry-fit files</h2><p><a href="aperture_access_AP01_DRAFT.pdf">Comparison, depth explanation and two full-size A3 templates</a> · <a href="analysis.json">Recomputed checks and input hashes</a> · <a href="aperture_access_AP01_DRAFT.blend">Blender access study</a></p>
<p>These four main-plate solids are separate AP01 alternatives. The CB01 diverter parts are unchanged. STEP/STL round trips passed; each DXF contains only two closed cut contours in millimeters. No quote package or manufacturing release has been changed.</p><table><thead><tr><th>Outer Ø (mm)</th><th>Thickness (mm)</th><th>Draft files</th></tr></thead><tbody>'''+rows+'''</tbody></table></section>
<p class="small">AP01 / October 15, 2026. Numeric R005 measurements, original scan and registration preserved. No physical adjustment, drilling, purchase or upload performed.</p></main></html>'''
    (OUT/'index.html').write_text(html)


def attach_panel():
    path=ROOT/'deliverables/current/fabrication/concentric-border-study/index.html'
    if not path.exists():
        return
    text=re.sub(r'<!-- AP01 BEGIN -->.*?<!-- AP01 END -->','',path.read_text(),flags=re.S)
    panel='''<!-- AP01 BEGIN --><section class="panel" id="aperture-access"><h2>Updated: upright opening and handle access</h2><p>The foam meets the removed inner plate's outer edge; rear rod contact with wood is confirmed by the user. AP01 compares a centered upright opening against the old diagonal contour, with full upper-opening footprints and a separate engagement/depth check.</p><p><a href="../aperture-access/index.html">Open the updated access comparison and dry-fit CAD</a>. Historical CB01/LOC01 drawings and quote files below still use the diagonal aperture; do not use them as the AP01 cutting design.</p></section><!-- AP01 END -->'''
    path.write_text(text.replace('<main>','<main>'+panel,1))


def run():
    for p in [OUT,OUT/'cad',CACHE]:p.mkdir(parents=True,exist_ok=True)
    req=read('canon/aperture_access_study.json');r=read('data/derived/resolved.json')
    reg=read('data/derived/registration.json');d=read('canon/fabrication_designs.json')
    assert req['evidence_revision']==r['revision']
    q=req['upright_trial'];c=np.asarray(r['inner_center_mm']);o=req['inner_outline']
    outer=rr(o['width_mm'],o['height_mm'],o['corner_radius_mm'],c)
    foam_inner=rr(o['width_mm']-12,o['height_mm']-12,o['corner_radius_mm']-6,c)
    upright=rr(q['width_mm'],q['height_mm'],q['corner_radius_mm'],c)
    old=Polygon(d['aperture']['base_convex_polygon_installed_mm']).buffer(d['aperture']['outward_radius_mm'],quad_segs=128)
    assert upright.covers(old) and foam_inner.covers(upright)
    controls={}
    for label,point,op in zip(['L','U'],r['controls_mm'],r['inner_control_openings']):
        center=c+op['center_local_mm'];disk=Point(*center).buffer(op['diameter_mm']/2,quad_segs=256)
        controls[label]=dict(scan_tip_mm=point,reference_opening_center_mm=center.tolist(),reference_diameter_mm=op['diameter_mm'],
                            reference_status=op['status'],
                            old_center_to_aperture_edge_mm=old.boundary.distance(Point(*point[:2])),
                            upright_center_to_aperture_edge_mm=upright.boundary.distance(Point(*point[:2])),
                            old_reference_disk_outside_aperture_mm2=disk.difference(old).area,
                            upright_reference_disk_outside_aperture_mm2=disk.difference(upright).area,
                            upright_reference_disk_margin_mm=disk.distance(upright.boundary))
    capture,samples=captured_surface(r,reg,old,upright)
    assert capture['upright']['conflict_triangles']==0
    result=dict(id='AP01',status=req['status'],controls=controls,captured_surface=capture,
                upright_contains_old_extra_margin_mm=old.boundary.distance(upright.boundary),
                foam_overlap_mm2=upright.intersection(outer.difference(foam_inner)).area,
                nominal_extra_land_mm=upright.distance(foam_inner.boundary),
                placement=dict(center_installed_mm=c.tolist(),rotation_deg=0,status='Provisional original reference placement'),
                CAD=export_cad(req),physical_fit='UNPERFORMED',manufacturing_release='HOLD',
                checks_scope='Planar and captured-surface tests only; axial engagement remains unresolved',
                input_sha256={p:sha(ROOT/p) for p in ['canon/aperture_access_study.json','docs/physical_checks/foam_edge_and_access_2026-10-15.json',
                             'canon/measurements.json','canon/fabrication_designs.json','data/derived/resolved.json','data/derived/registration.json',
                             'data/evidence/kohler-T14489-4.obj','data/evidence/kohler-1041504_2.pdf','src/fabrication/aperture_access.py']})
    assert result['foam_overlap_mm2']<1e-7 and all(x['upright_reference_disk_outside_aperture_mm2']<1e-7 for x in controls.values())
    write(OUT/'analysis.json',result)
    figures(req,r,old,upright,outer,foam_inner,samples,result)
    pdf(req,r,result);html(req,result);attach_panel()
    print(json.dumps({k:result[k] for k in ['id','controls','captured_surface','nominal_extra_land_mm']},indent=2))


if __name__=='__main__':
    run()
