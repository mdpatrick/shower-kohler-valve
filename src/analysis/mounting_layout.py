"""Planar factory-hole survey; its local frame is NOT the cover/installed frame."""
import math


IDS = ('M11-NED', 'M11-SWD', 'M13-FAX', 'M13-FBX', 'M13-FAY', 'M13-FBY')


def derive_layout(values):
    if not all(k in values for k in IDS):
        return None
    da, db, fax, fbx, fay, fby = [values[k] for k in IDS]
    if not all(math.isfinite(v) and v > 0 for v in (da, db, fax, fbx, fay, fby)):
        raise ValueError('Hole survey requires finite positive diameters and far-edge readings')
    a = [fax-da/2, fay-da/2]
    b = [fbx-db/2, fby-db/2]
    dx, dy = a[0]-b[0], b[1]-a[1]
    if dx <= 0 or dy <= 0:
        raise ValueError('Front-view A must be upper-right of B in the TOP/LEFT frame')
    distance = math.hypot(dx, dy)
    result = dict(source_ids=list(IDS), frame='Front toward handles; x RIGHT from LEFT block, y DOWN from TOP block',
                  center_from_left_top_mm={'A': a, 'B': b}, diameters_mm={'A':da, 'B':db},
                  separation_xy_mm=[dx, dy], center_distance_mm=distance,
                  predicted_nearest_edge_gap_mm=distance-(da+db)/2,
                  uncertainty_mm=None, status='derived from owner-selected planar observations',
                  installed_pose='Separate transform required; no scan/valve relocation implied')
    if 'M02-W' in values and 'M02-H' in values:
        w, h = values['M02-W'], values['M02-H']
        local = {k:[p[0]-w/2, h/2-p[1]] for k,p in [('A',a),('B',b)]}
        result['outline_centered_xy_up_mm'] = local
        result['outline_midpoint_offset_mm'] = [(local['A'][i]+local['B'][i])/2 for i in range(2)]
        result['outline_note'] = 'Comparison frame only; tape height does not gain accuracy from derived decimals'
    if 'M11-G' in values:
        old = values['M11-G']+(da+db)/2
        result['earlier_diagonal_comparison'] = dict(edge_gap_mm=values['M11-G'], implied_center_mm=old,
            difference_mm=distance-old, role='Retained disagreement / robustness scenario; not selected layout or certified error bound')
    return result
