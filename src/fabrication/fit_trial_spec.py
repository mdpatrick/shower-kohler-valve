"""Dimensional contract for the current flat capsule/ring design family.

This module does not infer a new physical measurement or certify an assembly.
It keeps documents and display dimensions tied to the same design as the CAD.
"""
import math
import re


def validate_design(d):
    m, v = d['main'], d['diverter']
    w, h = m['aperture_width_mm'], m['aperture_height_mm']
    numbers = [m['outer_diameter_mm'], w, h, v['outer_diameter_mm'],
               v['fallback_outer_diameter_mm'], v['aperture_diameter_mm']]
    numbers += [s['thickness_mm'] for s in d['stocks']]
    if not all(isinstance(x, (int, float)) and math.isfinite(x) and x > 0 for x in numbers):
        raise ValueError('All profile dimensions and thicknesses must be finite and positive')
    if m['shape'] != 'vertical capsule / obround' or h <= w:
        raise ValueError('This builder supports an upright capsule with height greater than width')
    if m['aperture_center_mm'] != [0, 0]:
        raise ValueError('This concentric design family requires a centered aperture')
    if not math.isclose(m['aperture_radius_mm'], w/2, abs_tol=1e-9, rel_tol=0):
        raise ValueError('Capsule end radius must equal half the opening width')
    if not math.isclose(m['straight_side_length_mm'], h-w, abs_tol=1e-9, rel_tol=0):
        raise ValueError('Capsule straight length must equal height minus width')
    if h >= m['outer_diameter_mm'] or v['aperture_diameter_mm'] >= min(v['outer_diameter_mm'], v['fallback_outer_diameter_mm']):
        raise ValueError('The aperture must remain inside the outer circle')
    if not 1 <= len(d['stocks']) <= 2 or len({s['id'] for s in d['stocks']}) != len(d['stocks']):
        raise ValueError('Use one shared stock thickness or one primary and one alternate')
    for s in d['stocks']:
        if s['id'] != f'T{round(s["thickness_mm"]*1000):04d}':
            raise ValueError('Stock ID must identify its thickness in micrometers')
    foam = d['foam']
    if not (0 < foam['width_mm'] < foam['outer_corner_radius_mm'] <= min(foam['outer_width_mm'], foam['outer_height_mm'])/2):
        raise ValueError('Invalid nominal foam band/corner geometry')
    low, high = foam['evaluated_outer_corner_radius_range_mm']
    if not foam['width_mm'] < low <= high <= min(foam['outer_width_mm'], foam['outer_height_mm'])/2:
        raise ValueError('Invalid foam corner sensitivity range')
    return d


def values(d, resolved, report=None):
    validate_design(d)
    m, v, f = d['main'], d['diverter'], d['foam']
    a = d['stocks'][0]
    b = d['stocks'][-1]
    out = dict(revision=d['revision'], main_od=m['outer_diameter_mm'],
               aperture_w=m['aperture_width_mm'], aperture_h=m['aperture_height_mm'],
               aperture_r=m['aperture_width_mm']/2,
               straight=m['aperture_height_mm']-m['aperture_width_mm'],
               arc_offset=(m['aperture_height_mm']-m['aperture_width_mm'])/2,
               div_od=v['outer_diameter_mm'], div_id=v['aperture_diameter_mm'],
               fallback_od=v['fallback_outer_diameter_mm'],
               stock=a['id'], alt_stock=b['id'], thickness=a['thickness_mm'],
               thickness_in=a['thickness_mm']/25.4, alt_thickness=b['thickness_mm'],
               depth_difference=b['thickness_mm']-a['thickness_mm'],
               foam_width=f['width_mm'], foam_depth=f['free_depth_mm'], foam_r=f['outer_corner_radius_mm'],
               inner_w=f['outer_width_mm'], inner_h=f['outer_height_mm'],
               inner_depth=f['free_total_plate_depth_mm'],
               main_cover=resolved['nominal']['trim_diameter_mm'],
               div_cover=resolved['nominal']['diverter_trim']['diameter_mm'],
               metal_tolerance=d['requested_shop_targets']['metal_profile_mm'],
               plastic_tolerance=d['requested_shop_targets']['plastic_profile_mm'],
               flatness=d['requested_shop_targets']['flatness_mm'])
    out['main_border'] = (out['main_od']-out['main_cover'])/2
    out['div_border'] = (out['div_od']-out['div_cover'])/2
    out['div_overlap'] = (out['div_cover']-out['div_id'])/2
    if report:
        cases = report['placement_scenarios']
        gaps = [c['gap_main_diverter_mm'] for c in cases]
        out.update(foam_land=report['nominal_foam_extra_land_mm'],
                   gap_min=min(gaps), gap_max=max(gaps),
                   hardware_min=min(c['minimum_projected_hardware_clearance_mm'] for c in cases),
                   capture_pieces=cases[0]['triangles_checked'], scenario_count=len(cases),
                   opening_extra_min=min(x['extra_custom_clearance_mm'] for x in report['inner_opening_envelopes']))
    return out


TOKEN = re.compile(r'\[\[([a-z_]+)(?::([^\]]+))?\]\]')


def expand(value, context):
    """Expand explicit [[name:format]] tokens; unknown names fail visibly."""
    if isinstance(value, str):
        def replacement(m):
            v = context[m[1]]
            return format(v, m[2] or ('g' if isinstance(v, (int, float)) else ''))
        return TOKEN.sub(replacement, value)
    if isinstance(value, list):
        return [expand(v, context) for v in value]
    if isinstance(value, dict):
        return {k: expand(v, context) for k, v in value.items()}
    return value
