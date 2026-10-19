"""FS02 functional check: neighboring plate gap and tab-depth transfer.

No CAD, accepted measurement, scan or registration is changed. All geometry
below is a sensitivity calculation in the existing working placement.
"""
from pathlib import Path
import hashlib
import json
import math
import os

import numpy as np
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'deliverables/current/analysis/tab-shafts-FS02'
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'build/FS02/mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle


def read(path):
    return json.loads((ROOT / path).read_text())


def generate():
    source = 'deliverables/current/analysis/tab-shafts-FS02/analysis.json'
    r = read(source)
    design = read('canon/fit_trial_design.json')
    earlier = read('deliverables/current/fabrication/FT02/design_report.json')
    t = read('deliverables/current/fabrication/FT02/engineering/locator_evaluation.json')['transforms']['cover_to_installed_xy_up']
    cb = read('deliverables/current/fabrication/concentric-border-study/analysis.json')
    center = np.array(t['translation_mm'])
    rotation = np.array(t['row_rotation'])
    diverter = np.array(cb['centers_installed_mm']['DIV'])
    main_r = design['main']['outer_diameter_mm'] / 2
    div_r = design['diverter']['outer_diameter_mm'] / 2
    radius_sum = main_r + div_r
    a = np.array(r['trial']['A']['center_cover_xy_mm'])
    b = np.array(r['trial']['B']['center_cover_xy_mm'])
    direction = (a - b) / np.linalg.norm(a - b)
    holes = [(a, direction, 0., r['trial']['A']['diameter_mm'] / 2),
             (b, direction, (r['trial']['B']['length_mm'] - r['trial']['B']['width_mm']) / 2,
              r['trial']['B']['width_mm'] / 2)]
    shafts = []
    transfer = []
    metal_back = 0.0  # sensitivity assumption, not an accepted bedding datum
    metal_thickness = 1.52
    for k in 'AB':
        line = np.array(r['shaft_fits'][k]['without_inner_plate']['line'])
        xy = lambda z: np.array([z, 1.]) @ line
        shaft_r = 2.5 * math.sqrt(1 + np.dot(line[0], line[0]))
        shafts.append((np.array([xy(-3), xy(0)]), shaft_r))
        form_mid = -1.5
        metal_mid = metal_back + metal_thickness / 2 - 8.05
        delta = xy(metal_mid) - xy(form_mid)
        transfer.append({
            'rod': k,
            'form_tab_installed_z_mm': [5.05, 8.05],
            'hypothetical_metal_installed_z_mm': [metal_back, metal_back + metal_thickness],
            'center_plane_difference_mm': metal_mid - form_mid,
            'shaft_xy_change_mm': delta.tolist(),
            'shaft_xy_change_norm_mm': float(np.linalg.norm(delta)),
            'source_shaft_fit_front_z_mm': r['shaft_fits'][k]['without_inner_plate']['fit_z'],
            'metal_plane_extrapolates_beyond_fitted_band': True,
            'scope': 'Hypothetical zero-bedding metal plane. No final hole coordinates selected. Actual bedding, shaft adjustment and hidden surfaces remain unresolved.'
        })

    def constraints(pose):
        x, y, degrees = pose
        angle = math.radians(degrees)
        q = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])
        result = []
        for (c, u, half_segment, hole_r), (points, shaft_r) in zip(holes, shafts):
            local = (points - [x, y]) @ q - c
            nearest = np.clip(local @ u, -half_segment, half_segment)[:, None] * u
            result.extend(hole_r - shaft_r - np.linalg.norm(local - nearest, axis=1))
        return np.array(result)

    def gap(pose):
        moved = np.array(pose[:2]) @ rotation + center
        return float(np.linalg.norm(moved - diverter) - radius_sum)

    extrema = []
    for sign in [1, -1]:
        solutions = []
        for start in [[0, 0, 0], [.3, .3, .2], [-.3, -.3, -.2]]:
            solution = minimize(lambda p: sign * gap(p), start, method='SLSQP',
                bounds=[(-10, 10), (-10, 10), (-5, 5)],
                constraints=[{'type': 'ineq', 'fun': constraints}],
                options={'ftol': 1e-11, 'maxiter': 300})
            if solution.success and constraints(solution.x).min() >= -1e-6:
                solutions.append(solution)
        assert solutions
        best = min(solutions, key=lambda s: s.fun)
        assert max(abs(best.x[:2])) < 9.9 and abs(best.x[2]) < 4.9
        extrema.append({'gap_mm': gap(best.x), 'pose_cover_xy_mm_angle_deg': best.x.tolist()})

    shifts = [{'main_downward_mm': shift,
               'gap_mm': float(np.linalg.norm(center - [0, shift] - diverter) - radius_sum)}
              for shift in [0, .5, 1, 2, 3, 4]]
    result = {
        'id': 'FS02-FUNCTIONAL-CENTERING',
        'status': 'MODEL_SENSITIVITY_NOT_FINAL_PLACEMENT',
        'main_diameter_mm': 2 * main_r, 'diverter_diameter_mm': 2 * div_r,
        'main_working_center_installed_mm': center.tolist(),
        'diverter_inferred_center_installed_mm': diverter.tolist(),
        'center_distance_mm': float(np.linalg.norm(center - diverter)),
        'nominal_working_gap_mm': gap([0, 0, 0]),
        'existing_placement_scenarios': [{key: case[key] for key in
            ['state', 'center_separation_mm', 'gap_main_diverter_mm']}
            for case in earlier['placement_scenarios']],
        'downward_sensitivity': shifts,
        'RF05_ideal_seated_play_gap_extrema': extrema,
        'gap_extrema_scope': 'SLSQP estimates, original fitted 5 mm bare shafts through 3 mm tabs, independent extrema. Main circle assumed to follow form center exactly; diverter fixed. No bracing, print/scan error or physical registration uncertainty. No guaranteed actual minimum gap.',
        'depth_transfer_sensitivity': transfer,
        'conclusion': 'RF05 can test a more repeatable pose. A snug fit is not absolute centering validation or a perfected metal-tab specification. Actual intended cover positions and separation must govern the repair, and hole positions must be transferred to the final tab depth.',
        'owner_measurements_requested': [],
        'source_sha256': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in
            [source, 'canon/fit_trial_design.json', 'deliverables/current/fabrication/FT02/engineering/locator_evaluation.json',
             'deliverables/current/fabrication/concentric-border-study/analysis.json', 'deliverables/current/fabrication/FT02/design_report.json']}
    }
    (OUT / 'centering_transfer.json').write_text(json.dumps(result, indent=2) + '\n')

    # Use installed axes, translated to the working main center. No scan pixels
    # or generated component imagery are needed for this analytic diagram.
    div = diverter - center
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.4), gridspec_kw={'width_ratios': [1, 1.2]})
    for ax in axes:
        ax.add_patch(Circle((0, 0), main_r, facecolor='#dfedf0', edgecolor='#247c8c', lw=2))
        ax.add_patch(Circle(div, div_r, facecolor='#e2e8eb', edgecolor='#445c69', lw=2))
        ax.set_aspect('equal')
        ax.grid(alpha=.12)
    axes[0].plot(0, 0, '+', color='#247c8c')
    axes[0].plot(*div, '+', color='#445c69')
    axes[0].text(0, 12, 'MAIN\nØ220 mm', ha='center', va='center')
    axes[0].text(div[0], div[1], 'DIVERTER\nØ124 mm', ha='center', va='center')
    axes[0].set(xlim=(-122, 122), ylim=(div[1]-70, 122), title='Two metal outer outlines', xlabel='X from main center (mm)', ylabel='Y from main center (mm)')
    axes[1].add_patch(Circle((0, -3), main_r, facecolor='none', edgecolor='#b34032', linestyle='--', lw=2))
    axes[1].set(xlim=(-32, 32), ylim=(-121, -101), title='Close-up: shifting main downward uses the gap', xlabel='X from main center (mm)')
    axes[1].text(0, -103, f'Working gap ≈ {shifts[0]["gap_mm"]:.1f} mm', ha='center', color='#247c8c')
    axes[1].text(0, -119, f'After 3 mm downward shift: ≈ {shifts[-2]["gap_mm"]:.1f} mm', ha='center', color='#b34032')
    axes[1].annotate('Main, shifted', xy=(21, -110.97), xytext=(20, -106.5), ha='center', color='#b34032', fontsize=9,
                     arrowprops={'arrowstyle':'->', 'color':'#b34032'})
    fig.suptitle('Tight on the rods does not establish the gap between the plates', fontsize=17)
    fig.text(.5, .025, 'Existing working placement estimate, not measured installed centers. Dashed outline is a hypothetical shift.\nKeep both backings concentric with their factory covers; do not shift a backing to compensate for an off-center repair.', ha='center', fontsize=10)
    fig.subplots_adjust(left=.07, right=.98, bottom=.15, top=.88, wspace=.27)
    fig.savefig(OUT / 'centering_gap.png', dpi=160)
    plt.close(fig)
    print(json.dumps({'working_gap_mm': result['nominal_working_gap_mm'], 'ideal_RF05_gap_extrema': extrema, 'transfer_xy_mm': [x['shaft_xy_change_norm_mm'] for x in transfer]}, indent=2))
    return result


if __name__ == '__main__':
    generate()
