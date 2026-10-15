"""ALIGN01: audit provisional tip landmarks without moving scan or CAD geometry.

Small, reproducible diagnostic of the captured tip caps. A best-fit projected
cap circle is a candidate center, not a measured shaft axis or fit approval.
"""
from pathlib import Path
import hashlib
import json
import os
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'deliverables/current/fabrication/aperture-access'
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'build/aperture_access/matplotlib'))
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Polygon


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def cap_vertices(r):
    # Stream the original derived vertex table through the preserved transform;
    # only two tiny neighborhoods are retained. No whole-scene load or rebuild.
    source = ROOT / 'data/derived/shower-hole-valve-polycam-vertices.npy'
    reg = ROOT / 'data/derived/registration.json'
    raw = np.load(source, mmap_mode='r')
    transform = np.asarray(json.loads(reg.read_text())['raw_to_installed_mm'])
    neighborhoods = []
    for start in range(0, len(raw), 65536):
        v = raw[start:start+65536] @ transform[:3, :3].T + transform[:3, 3]
        keep = np.zeros(len(v), dtype=bool)
        for point in r['controls_mm']:
            keep |= np.linalg.norm(v[:, :2]-point[:2], axis=1) < 12
        neighborhoods.append(v[keep])
    return np.concatenate(neighborhoods), [source, reg]


def display_crop_vertices():
    """Independent readback of the earlier display mesh, when available."""
    path = ROOT / 'build/aperture_access/captured_forward_display.stl'
    dtype = np.dtype([('normal', '<f4', (3,)), ('v', '<f4', (3, 3)), ('attr', '<u2')])
    if not path.exists():
        return None
    assert dtype.itemsize == 50
    data = np.fromfile(path, dtype=dtype, offset=84)
    return np.unique(data['v'].reshape(-1, 3), axis=0).astype(float)


def fit_cap(points, band):
    selected = points[points[:, 2] >= points[:, 2].max() - band]
    hull = selected[ConvexHull(selected[:, :2]).vertices, :2]
    center = (hull.min(0) + hull.max(0)) / 2
    radius = np.linalg.norm(hull - center, axis=1).mean()
    result = least_squares(lambda p: np.linalg.norm(hull - p[:2], axis=1) - p[2],
                           np.r_[center, radius])
    assert result.success and result.x[2] > 0
    c, radius = result.x[:2], result.x[2]
    # Independent algebraic circle estimate: agreement checks this calculation,
    # not whether the photographed physical part is round or metrically accurate.
    algebraic = np.linalg.lstsq(np.c_[2*hull, np.ones(len(hull))],
                               np.sum(hull*hull, axis=1), rcond=None)[0][:2]
    assert np.linalg.norm(algebraic-c) < .03
    rms = np.sqrt(np.mean((np.linalg.norm(hull-c, axis=1)-radius)**2))
    return dict(depth_band_mm=band, vertices=len(selected), center_xy_mm=c.tolist(),
                radius_mm=float(radius), radial_residual_rms_mm=float(rms),
                algebraic_center_difference_mm=float(np.linalg.norm(algebraic-c))), hull


def attach_panel():
    image = 'control_alignment.png'
    for relative in ['aperture-access', 'concentric-border-study']:
        path = ROOT / 'deliverables/current/fabrication' / relative / 'index.html'
        if not path.exists():
            continue
        prefix = '' if relative == 'aperture-access' else '../aperture-access/'
        panel = f'''<!-- ALIGN01 BEGIN --><section class="panel" id="control-alignment">
<h2>Correction: the stored U/L points are not verified shaft centers</h2>
<p>The off-center appearance is real in the reconstruction. Both original landmarks sit near the left edge of the captured tip caps. A separate cap-outline fit places the apparent centers about <b>3.1–3.4 mm farther right</b>. This is a scan-based diagnostic, not a measured alignment correction.</p>
<figure><a href="{prefix}{image}"><img src="{prefix}{image}" alt="Unchanged aperture and scan reference openings, with exact stored-point and fitted-tip-cap-center markers; enlarged upper and lower cap views"></a><figcaption>Purple circles: inner-plate openings, not knob diameters. Upper Ø48.46 is measured; lower Ø50 remains assumed. Black ×: original surface pick. Blue +: provisional tip-cap center. Circles and CAD have not been moved to force a match.</figcaption></figure>
<p>Your observation that the knobs look about as wide as the inner-plate openings is retained qualitatively; no knob diameter has been accepted. Where a part actually crosses an opening at the same depth, the radial allowance is <b>(opening diameter − passing-part diameter) / 2</b>, and center offset consumes that allowance. Similar diameters can therefore leave very little freedom for misalignment. The critical rear profile must be identified; the visible knob diameter alone does not establish what passes through each plane.</p>
<p><b>Fit remains unresolved in both centering and depth.</b> L's reference circle was centered on the old pick by construction. U's reference-circle center is 0.647 mm above its old pick. Those small coordinate differences do not establish physical concentricity. The new cap fit suggests roughly 3.2–3.3 mm offsets from the displayed circles.</p>
<p>A real assembly needs each stem, adapter and handle mating axis aligned. The rigid factory plate must register to both controls and studs together. Moving the plate alone could lose the current nominal 1 mm foam-side land; moving the whole trim/backing arrangement would require fresh wall-coverage and diverter-spacing checks. Do not turn this discrepancy into a machining tolerance or independently move the two factory holes.</p>
<p>The custom backing has one large upright aperture. Its existing geometric clearance results apply to the old provisional placement only. The small circles are factory-opening references, not additional holes in the custom cutting files. Actual centering, rear connection clearance and axial engagement require the real factory parts and a thickness-correct dry fit.</p>
<p><a href="{prefix}control_alignment.json">Recomputed offsets, cap-fit sensitivity and limitations</a> · <a href="https://resources.kohler.com/onlinecatalog/pdf/1041504_2.pdf#page=7">Kohler assembly sequence, pp. 7–8</a></p>
</section><!-- ALIGN01 END -->'''
        content = re.sub(r'<!-- ALIGN01 BEGIN -->.*?<!-- ALIGN01 END -->', '', path.read_text(), flags=re.S)
        content = re.sub(r'<!-- ALIGN01 TIP NOTICE -->.*?<!-- ALIGN01 TIP END -->', '', content, flags=re.S)
        if relative == 'concentric-border-study':
            notice = '<!-- ALIGN01 TIP NOTICE --><p><b>Landmark correction:</b> the U/L scan picks used below are tip-surface points near the cap edges, not verified end-tip centers. These older reconciliation calculations are retained as historical diagnostics. <a href="#control-alignment">Read the center audit before using them for fit or scale.</a></p><!-- ALIGN01 TIP END -->'
            content = content.replace('<h2>Your caliper readings include depth</h2>', '<h2>Your caliper readings include depth</h2>'+notice)
        else:
            content = content.replace('U and L are original scan tip centers.', 'U and L are provisional original surface picks, not verified shaft axes; see the ALIGN01 correction above.')
            content = content.replace('>Comparison, depth explanation and two full-size A3 templates</a>', '>Original AP01 drawings/templates — read ALIGN01 centering correction first</a>')
            content = content.replace('>Blender access study</a>', '>AP01 Blender snapshot — original picks; see ALIGN01</a>')
        path.write_text(content.replace('<main>', '<main>'+panel, 1))


def plot(r, rows, hulls):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
    fig = plt.figure(figsize=(12, 9.4), facecolor='#f6f9fa')
    gs = fig.add_gridspec(2, 2, width_ratios=[1.15, 1])
    ax = fig.add_subplot(gs[:, 0])
    center = np.asarray(r['inner_center_mm'])
    ax.add_patch(Circle(center, 110, facecolor='#d5e7eb', edgecolor='#387989'))
    ax.add_patch(FancyBboxPatch(center-np.array([116.35, 151.1])/2,
                               116.35, 151.1, boxstyle='round,pad=0,rounding_size=33',
                               facecolor='white', edgecolor='#247e8f', lw=2))
    for i, row in enumerate(rows):
        c = np.asarray(row['reference_opening_center_xy_mm'])
        old = np.asarray(row['stored_surface_point_mm'][:2])
        fit = np.asarray(row['diagnostic_cap_center_xy_mm'])
        ax.add_patch(Circle(c, row['reference_opening_diameter_mm']/2, fill=False,
                            edgecolor='#855da0', lw=2, ls='-' if row['control']=='U' else '--'))
        ax.add_patch(Polygon(hulls[i], color='#9da8ad'))
        ax.plot(*old, 'x', color='#192b34', ms=6, mew=1.8)
        ax.plot(*fit, '+', color='#007eb5', ms=9, mew=2)
        ax.annotate(row['control']+' connection', fit, xytext=(-95, fit[1]+14),
                    arrowprops=dict(arrowstyle='-', color='#4b6471'), fontsize=11)
    ax.set(xlim=(-115, 116), ylim=(-73, 153), xlabel='Installed X (mm)', ylabel='Installed Y (mm)')
    ax.set_aspect('equal'); ax.grid(alpha=.12)
    ax.set_title('Existing provisional circles and aperture\nNo geometry moved', fontsize=13, pad=15)
    for panel, idx in enumerate([1, 0]):
        row = rows[idx]; axz = fig.add_subplot(gs[panel, 1])
        c = np.asarray(row['reference_opening_center_xy_mm'])
        old = np.asarray(row['stored_surface_point_mm'][:2])-c
        fit = np.asarray(row['diagnostic_cap_center_xy_mm'])-c
        axz.add_patch(Polygon(hulls[idx]-c, facecolor='#c1c9ce', edgecolor='#6e7d85', alpha=.8))
        axz.plot(0, 0, 'o', mfc='white', mec='#855da0', ms=11, mew=2, label='Opening center')
        axz.plot(*old, 'x', color='#192b34', ms=9, mew=2, label='Stored surface pick')
        axz.plot(*fit, '+', color='#007eb5', ms=13, mew=2, label='Fitted cap center')
        axz.annotate('', fit, (0, 0), arrowprops=dict(arrowstyle='<->', color='#007eb5'))
        axz.text(3.1, -5.1, f'{row["fit_to_reference_opening_offset_mm"]:.2f} mm offset',
                 ha='center', color='#006b99', fontsize=12)
        axz.set(xlim=(-2.5, 9), ylim=(-6, 6), xlabel='X from opening center (mm)', ylabel='Y from opening center (mm)')
        axz.set_aspect('equal'); axz.grid(alpha=.15)
        axz.set_title(row['control']+' tip cap enlarged — same scale in X/Y', fontsize=12)
    handles = [plt.Line2D([], [], color='#855da0', marker='o', mfc='white', lw=0, label='Reference opening center'),
               plt.Line2D([], [], color='#192b34', marker='x', lw=0, label='Original surface pick'),
               plt.Line2D([], [], color='#007eb5', marker='+', lw=0, label='Diagnostic cap center')]
    fig.legend(handles=handles, loc='lower center', bbox_to_anchor=(.5, .065), ncol=3, frameon=False)
    fig.suptitle('The apparent offset comes from unverified center picks', fontsize=18, y=.97)
    fig.text(.5, .045, 'Upper opening Ø48.46 measured · Lower Ø50 assumed · No measured knob diameter or shaft-axis fit',
             ha='center', fontsize=11)
    fig.text(.5, .018, 'Cap fit uses a 2 mm front-depth band; its stability is not an accuracy bound. ALIGN01 / DRAFT',
             ha='center', fontsize=10, color='#5a707a')
    fig.subplots_adjust(left=.07, right=.98, bottom=.16, top=.89, wspace=.27, hspace=.4)
    fig.savefig(OUT/'control_alignment.png', dpi=155)
    plt.close(fig)


def run():
    r = read('data/derived/resolved.json'); verts, paths = cap_vertices(r)
    display = display_crop_vertices()
    rows, hulls = [], []
    for name, p, opening in zip(['L', 'U'], r['controls_mm'], r['inner_control_openings']):
        p = np.asarray(p); center = np.asarray(r['inner_center_mm']) + opening['center_local_mm']
        local = verts[np.linalg.norm(verts[:, :2]-p[:2], axis=1) < 12]
        trials = [fit_cap(local, band)[0] for band in [.35, .5, 1, 1.5, 2, 2.5, 3]]
        fit, hull = fit_cap(local, 2); c = np.asarray(fit['center_xy_mm']); hulls.append(hull)
        crop_difference = None
        if display is not None:
            cropped = display[np.linalg.norm(display[:, :2]-p[:2], axis=1) < 12]
            crop_fit, _ = fit_cap(cropped, 2)
            crop_difference = float(np.linalg.norm(c-np.asarray(crop_fit['center_xy_mm'])))
            assert crop_difference < .001
        bounds = np.asarray([t['center_xy_mm'] for t in trials])
        offset = float(np.linalg.norm(c-center))
        assert offset > 3 and offset < 4
        rows.append(dict(control=name, stored_surface_point_mm=p.tolist(),
                         reference_opening_center_xy_mm=center.tolist(),
                         reference_opening_diameter_mm=opening['diameter_mm'],
                         reference_opening_status=opening['status'],
                         stored_point_to_reference_offset_mm=float(np.linalg.norm(p[:2]-center)),
                         diagnostic_cap_center_xy_mm=c.tolist(), cap_frontmost_sample_z_mm=float(local[:, 2].max()),
                         fit_to_stored_delta_xy_mm=(c-p[:2]).tolist(), fit_to_reference_opening_offset_mm=offset,
                         display_crop_center_readback_difference_mm=crop_difference,
                         cap_center_band_sensitivity_span_xy_mm=np.ptp(bounds, axis=0).tolist(),
                         trials=trials))
    result = dict(id='ALIGN01', status='DIAGNOSTIC_ONLY_NOT_A_REGISTERED_CORRECTION', date='2026-10-15',
                  method='For each unchanged tip neighborhood (12 mm radius), take the top 0.35–3 mm of captured vertices, fit a circle to the projected convex hull, and independently compare an algebraic circle fit. Show the 2 mm-band result. No shaft-axis angle or center at the plate plane is inferred.',
                  controls=rows,
                  interpretation='Original picks lie near the left edge of both cap footprints. L reference circle reused its pick and is not independent evidence. U measured top-gap placement differs by 0.647 mm from its pick. Neither pick is a demonstrated axis center.',
                  input_sha256={str(p.relative_to(ROOT)): sha(p) for p in paths+[ROOT/'data/derived/resolved.json', ROOT/'canon/features.json', ROOT/'src/analysis/control_alignment.py']},
                  unchanged=['Original scans and transforms', 'R005 numeric measurements', 'AP01 CAD', 'Factory-opening reference positions', 'Existing Blender snapshots'],
                  limits=['Unbounded scan scale/distortion and physical registration uncertainty', 'Cap fit is not a measured shaft axis, hidden mating profile or engagement depth', 'Tiny residuals and band sensitivity do not bound real-world error', 'The lower inner opening diameter and placement remain unmeasured', 'User knob-size observation is qualitative; no numerical diameter accepted', 'Moving the factory plate alone invalidates the current nominal foam-land relation; moving the whole assembly needs new coverage and diverter-spacing checks'],
                  physical_fit='UNPERFORMED', fabrication_release='HOLD')
    (OUT/'control_alignment.json').write_text(json.dumps(result, indent=2)+'\n')
    plot(r, rows, hulls); attach_panel()
    print(json.dumps({r['control']: {k: r[k] for k in ['stored_point_to_reference_offset_mm', 'fit_to_stored_delta_xy_mm', 'fit_to_reference_opening_offset_mm']} for r in rows}, indent=2))


if __name__ == '__main__':
    run()
