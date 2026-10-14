"""Conditional depth screening; never treats an unidentified tip as a bare stem."""

def analyze_rough_in(d):
    nominal=d['nominal']['main_valve_rough_in']
    tip=nominal['upper_bare_tip_from_axis_mm']
    wall_min,wall_max=nominal['finished_wall_from_axis_mm']
    allowed=[tip-wall_max,tip-wall_min]
    scan=d['controls_mm'][1][2]
    measured=d.get('diagnostic_control_depths_mm',{})
    value=measured.get('upper',scan)
    return {
        'status':'UNRESOLVED','physical_fit':'UNRESOLVED',
        'nominal_source':nominal['source'],'nominal_axis_datum':nominal['axis_datum'],
        'upper_bare_tip_from_axis_mm':tip,'finished_wall_from_axis_mm':[wall_min,wall_max],
        'nominal_bare_upper_tip_from_tile_mm':allowed,
        'scan_upper_tip_from_tile_mm':scan,'measured_as_found_tip_depths_mm':measured,
        'comparison_tip_mm':value,
        'comparison_basis':'accepted as-found tip reading; identity unverified' if 'upper' in measured else 'conditional scan tip; identity and physical scale unverified',
        'conditional_excess_above_nominal_max_mm':value-allowed[1],
        'conditional_result':'outside nominal interval if same bare tip' if value<allowed[0] or value>allowed[1] else 'within nominal interval if same bare tip; not a fit pass',
        'same_bare_tip_verified':False,
        'valve_move_target_mm':None,
        'needed':'Check 10: identify each exposed tip/adapter, read H and both gaps; installer checks plaster guard or documented axis datum and final handle engagement.',
        'limits':['The 7/16-inch stud limit does not apply to the control stems.',
                  'No lower-control or separate-diverter depth limit is inferred from the upper-stem dimension.',
                  'A removable adapter, different revision, tilt or scan error can invalidate this comparison.',
                  'The added backing plate is not automatically an approved rough-in correction.']}
