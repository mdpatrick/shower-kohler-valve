"""Supplemental measurement reconciliation. Never writes canon, registration or CAD."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = 'docs/physical_checks/installed_center_distances_2026-10-15.json'
REGISTRATION = 'data/derived/registration.json'
OUTPUT = 'deliverables/current/analysis/center_reconciliation_DRAFT'
ORDER = ['L', 'U', 'NE', 'SW']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def projected_distance(length, depth_difference):
    """Orthogonal separation of the same tips, conditional on their known delta Z."""
    if length <= 0 or abs(depth_difference) > length:
        raise ValueError('Depth difference must not exceed the 3D distance')
    return float(np.sqrt(length * length - depth_difference * depth_difference))


def free_3d_embeddings(distance_matrix, scan_prior):
    """Exact metric embeddings and both proper-rotation alignments; no scale fit."""
    D = np.asarray(distance_matrix, dtype=float)
    J = np.eye(4) - np.ones((4, 4)) / 4
    eigenvalues, eigenvectors = np.linalg.eigh(-0.5 * J @ (D ** 2) @ J)
    result = {'centered_gram_eigenvalues_mm2': eigenvalues.tolist(),
              'exact_euclidean_embedding_possible': bool(eigenvalues.min() >= -1e-7),
              'branches': []}
    if not result['exact_euclidean_embedding_possible']:
        return result
    points = eigenvectors[:, -3:] * np.sqrt(np.maximum(eigenvalues[-3:], 0))
    centered_prior = scan_prior - scan_prior.mean(axis=0)
    for sign in [1, -1]:
        candidate = points * np.array([1, 1, sign])
        u, _, vt = np.linalg.svd(candidate.T @ centered_prior)
        rotation = u @ np.diag([1, 1, np.linalg.det(u @ vt)]) @ vt
        aligned = candidate @ rotation + scan_prior.mean(axis=0)
        reconstructed = np.linalg.norm(aligned[:, None, :] - aligned[None, :, :], axis=2)
        assert np.max(np.abs(reconstructed - D)) < 1e-7
        result['branches'].append({
            'embedding_mirror_sign': sign,
            'hypothetical_installed_tip_centers_mm': dict(zip(ORDER, aligned.tolist())),
            'displacement_from_scaled_scan_mm': dict(zip(ORDER, (aligned - scan_prior).tolist())),
            'point_displacement_rms_mm': float(np.sqrt(np.mean(np.sum((aligned - scan_prior) ** 2, axis=1)))),
            'maximum_pair_residual_mm': float(np.max(np.abs(reconstructed - D))),
            'rotation_determinant': float(np.linalg.det(rotation)),
        })
    result['branches'].sort(key=lambda b: b['point_displacement_rms_mm'])
    result['interpretation'] = ('All six reported lengths can be satisfied by a 3D four-tip arrangement. '
        'The two mirror branches are rigidly oriented/translated toward the weak, uniformly scaled scan prior; '
        'no scale is fitted here. Six distances determine shape, not its orientation or absolute depth relative '
        'to the wall. Neither branch is accepted. Exact agreement with reused inputs is not validation, '
        'and point displacement is not scanner error or a tolerance bound.')
    return result


def compute(root=ROOT):
    evidence = json.loads((root / EVIDENCE).read_text())
    registration = json.loads((root / REGISTRATION).read_text())
    state = json.loads((root / 'canon/project_state.json').read_text())
    if evidence['project_id'] != state['project_id']:
        raise ValueError('Study belongs to a different project')
    if evidence['baseline_measurement_revision'] != state['revision']:
        raise ValueError('Reconcile the study with the new measurement revision first')
    if evidence.get('distance_metric') != 'euclidean_3d_tip_center_distance':
        raise ValueError('Review the confirmed end-tip distance definition before using this calculation')
    rows = evidence['observations']
    ids = [row['measurement_id'] for row in rows]
    pairs = [(ORDER.index(row['feature_a']), ORDER.index(row['feature_b'])) for row in rows]
    if len(set(ids)) != 6 or len({tuple(sorted(p)) for p in pairs}) != 6:
        raise ValueError('Exactly six unique pair distances are required')
    measured = np.array([row['value_mm'] for row in rows], dtype=float)
    if any(row['unit'] != 'mm' or row['raw_readings'] != [row['value_mm']] for row in rows):
        raise ValueError('Review units or repeat-reading reduction before fitting')
    if not np.all(np.isfinite(measured) & (measured > 0)):
        raise ValueError('Distances must be finite and positive')
    for photo in evidence['photos'].values():
        if sha(root / photo['path']) != photo['sha256']:
            raise ValueError('Original annotated evidence hash mismatch')
    baseline = np.array([
        registration['landmarks_installed_mm'][evidence['feature_map'][name]]['point_mm']
        for name in ORDER
    ])
    ul = next(i for i, pair in enumerate(pairs) if set(pair) == {0, 1})
    stud = next(i for i, pair in enumerate(pairs) if set(pair) == {2, 3})

    def distances(points, planar=False):
        return np.array([np.linalg.norm((points[a] - points[b])[:2 if planar else 3]) for a, b in pairs])

    original_lengths = distances(baseline)
    scale = measured[ul] / original_lengths[ul]
    scaled = baseline * scale
    relative = scaled - scaled[0]
    y_axis = relative[1, :2] / np.linalg.norm(relative[1, :2])
    x_axis = np.array([y_axis[1], -y_axis[0]])
    scan_local = np.column_stack([relative[:, :2] @ x_axis, relative[:, :2] @ y_axis, relative[:, 2]])
    initial = np.array([scan_local[1, 1], *scan_local[2, :2], *scan_local[3, :2]])

    def fit(mode, weight, loss='linear', omit=None):
        z = np.zeros(4) if mode == 'planar' else scan_local[:, 2]

        def points(v):
            return np.array([[0, 0, z[0]], [0, v[0], z[1]],
                             [v[1], v[2], z[2]], [v[3], v[4], z[3]]])

        def residual(v):
            error = distances(points(v)) - measured
            if omit is not None:
                error = np.delete(error, omit)
            return np.r_[error, np.sqrt(weight) * (v - initial)] if weight else error

        result = least_squares(residual, initial, loss=loss, f_scale=0.5,
                               bounds=([1, 0, -200, -200, -200], [250, 200, 250, 0, 250]),
                               xtol=1e-12, ftol=1e-12, gtol=1e-12, max_nfev=2000)
        if not result.success:
            raise RuntimeError(result.message)
        fitted = points(result.x)
        fitted_lengths = distances(fitted)
        error = fitted_lengths - measured
        # Explicit local-to-installed mapping, never applied to actual scan/CAD.
        installed = np.column_stack([
            fitted[:, :2] @ np.stack([x_axis, y_axis]) + scaled[0, :2],
            fitted[:, 2] + scaled[0, 2]
        ])
        return dict(mode=mode, scan_coordinate_penalty_weight=weight, loss=loss,
                    fitted_distances_mm=fitted_lengths.tolist(),
                    residuals_mm=error.tolist(), rms_residual_mm=float(np.sqrt(np.mean(error ** 2))),
                    maximum_absolute_residual_mm=float(np.abs(error).max()),
                    local_tip_centers_mm=dict(zip(ORDER, fitted.tolist())),
                    hypothetical_installed_tip_centers_mm=dict(zip(ORDER, installed.tolist())),
                    fitted_XY_stud_tip_separation_mm=float(distances(fitted, planar=True)[stud]),
                    omitted_measurement=ids[omit] if omit is not None else None,
                    optimizer_success=bool(result.success))

    fits = [fit(mode, weight) for mode in ['planar', 'scan_relative_depths'] for weight in [0, 1/16, 1/4]]
    fits += [fit(mode, 1/16, 'soft_l1') for mode in ['planar', 'scan_relative_depths']]
    reference = next(f for f in fits if f['mode'] == 'scan_relative_depths'
                     and f['scan_coordinate_penalty_weight'] == 1/16 and f['loss'] == 'linear')
    D = np.zeros((4, 4))
    for (i, j), length in zip(pairs, measured):
        D[i, j] = D[j, i] = length
    free_depth = free_3d_embeddings(D, scaled)
    comparisons = [dict(measurement_id=row['measurement_id'], endpoints=[row['feature_a'], row['feature_b']],
                        raw_caliper_mm=float(measured[i]), baseline_scan_3D_mm=float(original_lengths[i]),
                        baseline_scan_XY_mm=float(distances(baseline, planar=True)[i]),
                        baseline_scan_absolute_delta_Z_mm=float(abs(baseline[pairs[i][0], 2] - baseline[pairs[i][1], 2])),
                        conditional_caliper_XY_using_baseline_scan_depth_mm=projected_distance(measured[i], baseline[pairs[i][0], 2] - baseline[pairs[i][1], 2]),
                        conditional_depth_correction_mm=float(measured[i] - projected_distance(measured[i], baseline[pairs[i][0], 2] - baseline[pairs[i][1], 2])),
                        scan_scaled_to_80_control_mm=float(distances(scaled)[i]),
                        caliper_minus_scaled_scan_mm=float(measured[i] - distances(scaled)[i]),
                        reference_trial_fitted_mm=reference['fitted_distances_mm'][i],
                        reference_trial_adjustment_mm=reference['residuals_mm'][i])
                   for i, row in enumerate(rows)]
    # Hold out each pair only as an internal geometry diagnostic. No independent validation.
    holdout = [fit(mode, 0, omit=i) for mode in ['planar', 'scan_relative_depths'] for i in range(6)]
    return dict(
        project_id=evidence['project_id'], study_id='RECON-001', study_revision=evidence['study_revision'],
        baseline_measurement_revision=state['revision'], baseline_design_revision='F005',
        status='DRAFT_NOT_FOR_FABRICATION', units='mm', raw_record=EVIDENCE,
        inputs_sha256={p: sha(root / p) for p in [EVIDENCE, REGISTRATION, 'canon/measurements.json',
                                                'canon/scan_annotations.json', 'src/analysis/reconcile_installed_centers.py']},
        comparison_only_uniform_scale_factor=scale,
        scale_note='80 mm control reading calibrates this trial only. It is reused as a fitting input; neither the scaled prior nor agreement with the same reading is independent evidence. No scan transform is changed.',
        local_frame='L tip at origin; +Y along scan-projected L-to-U direction; +X toward right stud; Z relative to L. These are tip centers, not axis intersections at a plate plane.',
        fitting_method='Joint nonlinear least squares of six center distances, five XY degrees of freedom, optional weak scan-coordinate penalty. Lower tip and control-line direction fix the coordinate gauge. Studs constrained to their observed opposite sides.',
        weighting_note='Caliper residual weight 1 per distance. Scan coordinate penalty 0, 1/16, 1/4 is a chosen sensitivity study, not measured variances or confidence. 1/16 means four times the residual length scale for each scan coordinate. Distances sharing endpoints may have correlated errors.',
        confirmed_distance_metric=evidence['distance_metric'],
        projection_formula='d_XY = sqrt(d_3D^2 - (Z_a - Z_b)^2)',
        projection_note='Conditional XY values use unchanged baseline scan depth differences and original raw 3D readings. They are illustrative, not accepted wall-plane dimensions. Stud inclination additionally changes the axis intersection at the plate plane; projected tip XY is not that intersection unless the axis is normal.',
        depth_note='The user confirms unequal-depth 3D tip distances. The planar trials are counterfactual sensitivity checks only, not an alternative reading definition. Fixed scan-depth trials cannot establish true depth. Free-depth embeddings also remain unoriented relative to the wall without an external depth/plane datum.',
        robust_note='Soft-L1 sensitivity uses an illustrative 0.5 mm transition, not an accepted uncertainty. No individual caliper observation is automatically rejected or corrected.',
        selected_for_CAD=False, comparison=comparisons, trials=fits, leave_one_pair_out=holdout,
        free_depth_metric_check=free_depth,
        findings=[
            'Both lower-left stud distances exceed the scan; both upper-right distances are smaller. A single average scale cannot explain this feature-dependent pattern.',
            'The six raw distances admit an exact 3D embedding. Residuals in the older fixed-depth fit reflect its imposed scan depths/planar constraints as well as measurement uncertainty; they do not establish inconsistency of the raw six lengths.',
            'Neither exact free-depth fit nor small constrained-fit residuals establish physical accuracy. Depth, contact repeatability, registration and axis uncertainty remain unbounded; no source is declared globally more accurate.',
            'Do not force the inner plate conditional 112.05 mm spacing into this fit. It has different endpoints, an unmeasured NE bore, and its own measurement uncertainty.',
            'Current custom escutcheon geometry has one clearance aperture containing both stud paths, not two separate close-fit mounting holes. Retain this aperture intent while reconciling its clearance and foam landing.'
        ],
        clearance_policy={
            'formula':'D_hole_nominal >= D_stud_max + 2*(e_location + e_axis + e_install + e_cut_position + c_free) + delta_diameter_undersize',
            'definitions':'All e terms and c_free are worst-case radial allowances at the actual plate plane. delta_diameter_undersize is a diametral fabrication allowance. Obtain the vendor size/position convention so the same error is not counted twice. The formula is a sufficient conservative clearance budget for a round pass-through hole; it does not check bearing strength or seal land.',
            'location_error_bound_mm':None, 'stud_max_diameter_mm':None, 'selected_hole_diameter_mm':None,
            'round_or_slot':'For any future required custom mounting holes, compare round clearance versus one locating hole and a slot along the stud-pair line only if bearing, restraint, drainage and seal land remain suitable. No change to factory holes is selected.',
            'example':'An assumed 0.5 mm radial location allowance alone consumes 1.0 mm of diametral clearance, before fabrication and free-assembly clearance. This is an illustration, not a measured allowance for this installation.',
            'finish_and_thickness':'Include actual finish build, plate thickness, stud inclination and insertion path.',
            'separate_budgets':'First reconcile the 3D endpoint geometry; then bound location at the real plate plane. Assembly clearance, measurement/registration uncertainty, machining tolerance, and seal-support requirements are separate quantities. Do not use depth corrections or fit residuals as manufacturing tolerances.',
            'manufacturing_source':{'url':'https://sendcutsend.com/blog/basic-tolerances-and-cut-feature-relationships/', 'accessed':'2026-10-15', 'claim':'SendCutSend describes clearance fit and generally posts +/-0.005 inch cut tolerances, subject to material and thickness. This is approximately +/-0.127 mm, not an installation accuracy guarantee.'},
            'material_source':'https://sendcutsend.com/materials/stainless-steel-316/'
        },
        executed_checks=['Four evidence images copied byte-for-byte and SHA-256 verified',
                         'Six distinct positive finite mm observations validated',
                         'Six baseline scan pair distances independently recomputed',
                         'Eight joint-fit sensitivity trials converged',
                         'Twelve leave-one-pair-out diagnostics converged',
                         'Six conditional XY projections recomputed from raw 3D lengths and unchanged scan depth differences',
                         'Centered distance Gram matrix and both proper-rotation 3D embeddings checked'],
        physical_fit='NOT PERFORMED', fabrication_approval='NOT GIVEN',
        evidence_application='Supplemental calculation only. Raw six readings are preserved in the source record; no smoothing replaces them. Adoption into canon/design requires a revisioned endpoint and fit decision. Baseline scan, CAD and R005 measurements remain unchanged.'
    )


def save(root=ROOT):
    report = compute(root)
    output = root / OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['Installed center reconciliation — RECON-001', 'DRAFT_NOT_FOR_FABRICATION',
             'Supplement to R005 / F005. All figures in mm. No scan or CAD changes.', '',
             'Revision 2: user confirms 3D distances between end-tip centers, at unequal depths.',
             'The original six values are unchanged; they are not wall-plane hole spacings.', '',
             'Pair       Caliper   Scan 3D   Scaled scan   Weak-prior trial   Adjustment']
    for row in report['comparison']:
        lines.append(f"{'-'.join(row['endpoints']):<10} {row['raw_caliper_mm']:8.2f} {row['baseline_scan_3D_mm']:9.2f} {row['scan_scaled_to_80_control_mm']:13.2f} {row['reference_trial_fitted_mm']:18.2f} {row['reference_trial_adjustment_mm']:+12.2f}")
    lines += ['', 'Scan is scaled to the reported 80 mm control spacing for comparison only.',
              'The trial uses scan relative depths and a weak 1/16 coordinate penalty.',
              'Its fitted values are tip distances, not manufacturing dimensions.', '',
              'DEPTH CORRECTION — ILLUSTRATIVE, using unchanged baseline scan depths',
              report['projection_formula'],
              'Pair         Raw 3D    Scan delta Z    Conditional XY    Reduction']
    for row in report['comparison']:
        lines.append(f"{'-'.join(row['endpoints']):<10} {row['raw_caliper_mm']:8.2f} {row['baseline_scan_absolute_delta_Z_mm']:15.3f} {row['conditional_caliper_XY_using_baseline_scan_depth_mm']:17.3f} {row['conditional_depth_correction_mm']:12.3f}")
    lines += [report['projection_note'], '', 'FREE-DEPTH GEOMETRY CHECK',
              report['free_depth_metric_check'].get('interpretation', 'No exact 3D embedding exists for these readings.'),
              'Both rigidly aligned mirror branches and their full coordinates are retained in the JSON report.', '',
              'Sensitivity: mode / scan weight / loss / maximum adjustment / RMS']
    for trial in report['trials']:
        lines.append(f"{trial['mode']} / {trial['scan_coordinate_penalty_weight']} / {trial['loss']} / {trial['maximum_absolute_residual_mm']:.3f} / {trial['rms_residual_mm']:.3f}")
    lines += ['', *report['findings'], '', report['weighting_note'], report['depth_note'],
              '', 'CLEARANCE BUDGET', report['clearance_policy']['formula'],
              report['clearance_policy']['definitions'], report['clearance_policy']['example'],
              report['clearance_policy']['round_or_slot'],
              report['clearance_policy']['separate_budgets'],
              report['clearance_policy']['manufacturing_source']['claim'],
              report['clearance_policy']['manufacturing_source']['url'],
              '', 'Actual stud diameter, axes at the plate plane, and physical fit remain unverified.',
              report['evidence_application']]
    output.with_suffix('.txt').write_text('\n'.join(lines) + '\n')
    return {'report': str(output.with_suffix('.json').relative_to(root)),
            'readable_report': str(output.with_suffix('.txt').relative_to(root)),
            'status': report['status'], 'comparison': report['comparison'],
            'selected_for_CAD': False}


if __name__ == '__main__':
    print(json.dumps(save(), indent=2))
