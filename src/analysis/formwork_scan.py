"""FS01: printed-form calibration and separate, reproducible scan comparisons.

No CAD or earlier registration is changed. All analysis reads preserved inputs.
Rebuild with ./project assess-formwork-scan; inspection choices live in canon.
"""
from pathlib import Path
import itertools, json, math, os, shutil, sys, zipfile
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull
import trimesh

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.ingest import sha, members, cached_member_ok

OUT = ROOT / 'deliverables/current/analysis/formwork-scan-FS01'
CACHE = ROOT / 'build/formwork_scan_FS01'
os.environ.setdefault('MPLCONFIGDIR', str(CACHE / 'matplotlib'))
PAIRS = [('U', 'L'), ('A', 'B'), ('U', 'A'), ('L', 'A'), ('U', 'B'), ('L', 'B')]


def read(p):
    return json.loads((ROOT / p).read_text())


def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def preserved_mesh(cfg):
    archive = ROOT / cfg['archive']
    assert sha(archive) == cfg['archive_sha256']
    target = ROOT / Path(cfg['extracted_obj']).parent
    assert not target.is_symlink()
    with zipfile.ZipFile(archive) as z:
        inventory = members(z)
        assert shutil.disk_usage(ROOT).free > 2 * sum(e['size_bytes'] for e in inventory)
        for e in inventory:
            p = target / e['name']
            assert not p.is_symlink() and p.resolve().is_relative_to(target.resolve())
            p.parent.mkdir(parents=True, exist_ok=True)
            if not cached_member_ok(p, e, target):
                with z.open(e['name']) as a, p.open('wb') as b:
                    shutil.copyfileobj(a, b)
            assert cached_member_ok(p, e, target)
    vertices, faces = [], []
    for line in (ROOT / cfg['extracted_obj']).open():
        if line.startswith('v '):
            vertices.append(list(map(float, line.split()[1:4])))
        elif line.startswith('f '):
            ids = [int(x.split('/')[0])-1 for x in line.split()[1:]]
            for i in range(1, len(ids)-1):
                faces.append([ids[0], ids[i], ids[i+1]])
    return np.array(vertices), np.array(faces)


def plane(points, iterations, quantile):
    p = points.copy()
    for _ in range(iterations):
        c = p.mean(0)
        _, u = np.linalg.eigh(np.cov(p.T))
        n = u[:, 0] * (1 if u[2, 0] > 0 else -1)
        d = (p-c) @ n
        p = p[abs(d) < np.quantile(abs(d), quantile)]
    y = np.array([0., 1, 0]); y -= n*(y@n); y /= np.linalg.norm(y)
    q = np.array([np.cross(y, n), y, n])
    t = np.eye(4); t[:3, :3] = q; t[:3, 3] = -q@c
    return t, float(np.sqrt(np.mean(((points-c)@n)**2)))


def transform(v, t):
    return v @ t[:3, :3].T + t[:3, 3]


def resample(path, count=2048):
    lengths = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    keep = np.r_[True, np.diff(lengths) > 1e-10]
    return np.array([np.interp(np.linspace(0, lengths[-1], count), lengths[keep], path[keep, i]) for i in range(path.shape[1])]).T


def circle(path):
    p = resample(path)[:, :2]
    fit = least_squares(lambda t: np.linalg.norm(p-t[:2], axis=1)-t[2],
                        [.045, .022, .616], loss='soft_l1', f_scale=.005)
    return {'center_raw_units': fit.x[:2].tolist(), 'radius_raw_units': float(fit.x[2]),
            'radial_residual_rms_raw': float(np.sqrt(np.mean(fit.fun**2))),
            'xy_spans_raw': np.ptp(path[:, :2], axis=0).tolist()}


def opening(path, scale):
    p = resample(path)[:, :2]
    keep = np.ones(len(p), bool)
    # Tabs have their own contours and must not pull the capsule fit inward.
    for center in [[59/194.84, 27/194.84], [-40/194.84, -16/194.84]]:
        keep &= np.linalg.norm(p-center, axis=1) > 15/194.84
    p = p[keep]
    def residual(t):
        cx, cy, th, radius, half = t
        q = (p-[cx, cy]) @ rotation(th)
        q[:, 1] -= np.clip(q[:, 1], -half, half)
        return np.linalg.norm(q, axis=1)-radius
    fit = least_squares(residual, [.05, .02, -.02, .29, .067], loss='soft_l1', f_scale=.002,
                        bounds=([-.1, -.1, -.2, .25, .02], [.2, .2, .2, .35, .12]))
    cx, cy, theta, radius, half = fit.x
    return {'center_raw_units': [cx, cy], 'rotation_rad': theta,
            'width_mm': 2*radius*scale, 'height_mm': 2*(radius+half)*scale,
            'radial_residual_rms_mm': float(np.sqrt(np.mean(fit.fun**2))*scale)}


def rotation(theta):
    return np.array([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])


def cap_fit(points, band):
    selected = points[points[:, 2] >= points[:, 2].max()-band]
    hull = selected[ConvexHull(selected[:, :2]).vertices, :2]
    c = (hull.min(0)+hull.max(0))/2
    fit = least_squares(lambda t: np.linalg.norm(hull-t[:2], axis=1)-t[2],
                        [*c, np.linalg.norm(hull-c, axis=1).mean()])
    return {'band_mm': band, 'center_mm': [*fit.x[:2], float(points[:, 2].max())],
            'cap_radius_mm': float(fit.x[2]),
            'radial_residual_rms_mm': float(np.sqrt(np.mean(fit.fun**2)))}


def analyze():
    OUT.mkdir(parents=True, exist_ok=True); CACHE.mkdir(parents=True, exist_ok=True)
    cfg = read('canon/formwork_scan_assessment_FS01.json')
    raw, faces = preserved_mesh(cfg)
    a = cfg['rough_plane']; t0, _ = plane(raw, a['iterations'], a['retained_quantile_each_iteration'])
    rough = transform(raw, t0)
    a = cfg['face_plane']; radius = np.linalg.norm(rough[:, :2]-a['annulus_center_rough_units'], axis=1)
    patches = rough[(radius > a['annulus_radii_raw_units'][0]) & (radius < a['annulus_radii_raw_units'][1])]
    t1, face_rms = plane(patches, a['trim_iterations'], a['retained_quantile_each_iteration'])
    face_t = t1 @ t0; v = transform(raw, face_t)
    mesh = trimesh.Trimesh(v, faces, process=False)
    sections, rim_fits = {}, []
    for z in cfg['calibration']['section_sensitivity_raw_units']:
        sec = mesh.section(plane_normal=[0, 0, 1], plane_origin=[0, 0, z])
        paths = sec.discrete
        rim = max((p for p in paths if np.ptp(p[:, 0]) > 1), key=len)
        aperture = max((p for p in paths if .5 < np.ptp(p[:, 0]) < .7 and .6 < np.ptp(p[:, 1]) < .8), key=len)
        sections[z] = {'rim': rim, 'aperture': aperture, 'all': paths}
        fit = circle(rim); fit['z_raw_units'] = z
        fit['scale_mm_per_raw_unit'] = 120 / fit['radius_raw_units']
        fit['usable_rim'] = z <= -.01
        rim_fits.append(fit)
    nominal = next(r for r in rim_fits if r['z_raw_units'] == cfg['calibration']['nominal_face_section_raw_units'])
    scale = nominal['scale_mm_per_raw_unit']
    aperture_fits = [dict(z_raw_units=z, **opening(p['aperture'], scale)) for z, p in sections.items()]
    ap = next(r for r in aperture_fits if r['z_raw_units'] == -.01)
    # Frame centered on the independent outer-rim fit; roll from the long opening.
    # Opening-center disagreement is reported, not quietly corrected.
    q = rotation(ap['rotation_rad'])
    local = np.eye(4); local[:2, :2] = q.T*scale; local[2, 2] = scale
    local[:2, 3] = -q.T @ np.array(nominal['center_raw_units'])*scale
    raw_to_form = local @ face_t
    scan = transform(raw, raw_to_form)
    np.save(CACHE / 'vertices_mm.npy', scan); np.save(CACHE / 'faces.npy', faces)
    np.save(CACHE / 'face_vertices_units.npy', v)
    tip_method = cfg['tip_method']; view = cfg['inspection_view']; tip_fits = {}; points = {}; alternate_points = {}
    for name, pixels in view['tip_seed_pixels'].items():
        xy = (np.array(view['face_frame_center_raw_units']) + (np.array(pixels)-view['pixels']/2)*
              [view['span_raw_units']/view['pixels'], -view['span_raw_units']/view['pixels']])*scale
        region = v[np.linalg.norm(v[:, :2]*scale-xy, axis=1) < tip_method['neighborhood_radius_mm']]*scale
        is_control = name in ('U', 'L')
        bands = tip_method['control_sensitivity_bands_mm' if is_control else 'rod_sensitivity_bands_mm']
        fits = [cap_fit(region, b) for b in bands]
        band = tip_method['control_cap_band_mm' if is_control else 'rod_cap_band_mm']
        chosen = next(f for f in fits if f['band_mm'] == band)
        def to_local(p):
            p = np.array(p); p[:2] = (p[:2]-np.array(nominal['center_raw_units'])*scale) @ q
            return p
        points[name] = to_local(chosen['center_mm']).tolist()
        alternate_points[name] = [to_local(f['center_mm']) for f in fits]
        tip_fits[name] = {'seed_pixels': pixels, 'chosen_band_mm': band, 'sensitivity_fits_in_face_mm': fits}
    old = read('deliverables/current/fabrication/FT02/tab-rethink/analysis.json')
    scales = [r['scale_mm_per_raw_unit']/scale for r in rim_fits if r['usable_rim']]
    rows = []
    for (a, b), prior in zip(PAIRS, old['scan_comparison']):
        assert prior['pair'] == a+'-'+b
        new = float(np.linalg.norm(np.array(points[a])-points[b]))
        variants = [float(np.linalg.norm(pa-pb)*s) for pa, pb, s in itertools.product(alternate_points[a], alternate_points[b], scales)]
        rows.append({'pair': a+'-'+b, 'caliper_3d_mm': prior['owner_3d_mm'],
                     'without_inner_plate_mm': prior['original_refitted_80_anchor_3d_mm'],
                     'with_inner_plate_mm': prior['attached_visible_picks_3d_mm'],
                     'with_formwork_mm': new, 'formwork_minus_caliper_mm': new-prior['owner_3d_mm'],
                     'formwork_method_sensitivity_mm': [min(variants), max(variants)]})
    # Visible rod slices: diagnostic of poor recovery of small features, not a
    # new physical rod measurement or a hidden hole-center estimate.
    rods = {}
    face_mm = v*scale
    for name, max_z in [('A', 11), ('B', 10)]:
        center = np.array(next(f for f in tip_fits[name]['sensitivity_fits_in_face_mm'] if f['band_mm'] == 1.5)['center_mm'][:2])
        bins = []
        for z in range(2, max_z+1):
            p = face_mm[(np.linalg.norm(face_mm[:, :2]-center, axis=1) < 7) & (abs(face_mm[:, 2]-z) < .5)]
            if len(p) < 10: continue
            fit = least_squares(lambda t: np.linalg.norm(p[:, :2]-t[:2], axis=1)-t[2],
                                [*center, 2.4], loss='soft_l1', f_scale=.15)
            bins.append({'z_mm': z, 'center_face_mm': fit.x[:2].tolist(), 'diameter_mm': float(fit.x[2]*2), 'radial_residual_rms_mm': float(np.sqrt(np.mean(fit.fun**2)))})
        rods[name] = {'visible_bins': bins, 'median_mesh_diameter_mm': float(np.median([b['diameter_mm'] for b in bins]))}
    # Preserve actual section data for a directly inspectable slot plot.
    section_data = {}
    for z in [-.005, -.01, -.02]:
        section_data[str(z)] = [p.tolist() for p in sections[z]['all'] if len(p) > 30]
    write(CACHE/'sections.json', section_data)
    # A hypothetical narrower slot illustrates the intended improvement only.
    rod_nominal = .190*25.4
    play = [{'slot_length_mm': l, 'slot_width_mm': w, 'one_axis_centered_clearance_x_mm': (l-rod_nominal)/2,
             'one_axis_centered_clearance_y_mm': (w-rod_nominal)/2} for l, w in [(12, 8), (10, 7)]]
    paths = ['canon/formwork_scan_assessment_FS01.json', 'canon/formwork_print_RF03.json', 'canon/measurements.json',
             'deliverables/current/analysis/registration.json', 'canon/transforms.json',
             'deliverables/current/fabrication/FT02/tab-rethink/analysis.json', cfg['archive'], cfg['selected_reference']]
    result = {'revision': 'FS01', 'status': 'SCAN_DIAGNOSTIC_NOT_A_TIGHTER_FORM_RELEASE',
              'assumption': cfg['owner_assumption'], 'identity_basis': cfg['identity_basis'],
              'input_vertices': len(raw), 'input_triangles': len(faces), 'uniform_mm_per_raw_unit': scale,
              'raw_to_face_units': face_t.tolist(), 'raw_to_form_diagnostic_mm': raw_to_form.tolist(),
              'form_frame': 'Origin at outer-rim fitted center projected onto front face. X right/Y up/Z toward shower. Roll from upright opening. No primary registration applied.',
              'calibration': dict(cfg['calibration'], nominal=nominal, rim_section_sensitivity=rim_fits),
              'form_cross_checks': {
                  'front_face_plane_rms_mm': face_rms*scale,
                  'outer_rim_radial_rms_mm': nominal['radial_residual_rms_raw']*scale,
                  'outer_rim_xy_spans_mm': (np.array(nominal['xy_spans_raw'])*scale).tolist(),
                  'opening_width_scan_mm': ap['width_mm'], 'opening_width_CAD_mm': 114.35,
                  'opening_height_scan_mm': ap['height_mm'], 'opening_height_CAD_mm': 141.10,
                  'opening_vs_outer_center_offset_mm': (q.T @ (np.array(ap['center_raw_units'])-nominal['center_raw_units'])*scale).tolist(),
                  'opening_center_offset_norm_mm': float(np.linalg.norm(np.array(ap['center_raw_units'])-nominal['center_raw_units'])*scale),
                  'opening_fits': aperture_fits,
                  'not_recoverable': ['Complete 12 x 8 mm slot walls: A disappears into reconstructed material below the face; B is partly occluded.', '8 mm face thickness and hidden 24 mm skirt/reliefs cannot be independently checked from this front scan.']},
              'tip_points_form_frame_mm': points, 'tip_fits': tip_fits, 'comparison': rows,
              'old_scan_calibration': 'Both earlier diagnostics use caliper U-L = 80 mm to set scale. Their 80.0 mm results are inputs, not independent validation. The new scan uses only the printed form for scale.',
              'coplanar_plate_bores': {'A_mm': [116.34, 58.57], 'B_mm': [13.55, 106.02], 'diameters_mm': [5.66, 5.66], 'separation_mm': float(math.hypot(102.79, 47.45)), 'scope': 'R006 coplanar loose-plate calipers; independent of 3D projecting-tip distances. Kept unchanged.'},
              'rod_mesh_diagnostics': rods,
              'nominal_rod_diameter_mm': rod_nominal,
              'nominal_rod_basis': 'Existing project Kohler 1038645 identification: 10-24 stud, nominal major diameter 0.190 inch. Not a new caliper reading.',
              'hypothetical_slot_play': play, 'decision': cfg['decision'],
              'limits': ['Sensitivity ranges show choices within this analysis, not certified measurement bounds or confidence intervals.',
                         'Uniform calibration does not remove local photogrammetry smoothing, reflective-metal distortion or occlusion.',
                         '3D end-tip distances do not specify rod axes at the tab plane. Do not substitute them for R006 planar hole locations.',
                         'New form placement is observed; repeatable positioning, full seating, insertion/removal and water performance are not established.',
                         'Later captures may include different nut positions or adjustments; the same contact surface is not guaranteed by matching feature names.',
                         'Secondary loose reflective plate scans are not additional installed-hardware observations and are not averaged into this table.'],
              'sources_sha256': {p: sha(ROOT/p) for p in paths}}
    write(OUT/'analysis.json', result)
    print(json.dumps({'scale': scale, 'comparisons': rows, 'cross_checks': {k:v for k,v in result['form_cross_checks'].items() if k != 'opening_fits'}}, indent=2))


if __name__ == '__main__':
    analyze()
