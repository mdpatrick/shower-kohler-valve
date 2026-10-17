"""Resolve design parameters from evidence, with no writes to accepted canon."""
from pathlib import Path
import json,math,numpy as np
import sys
from shapely.geometry import Polygon,Point,LineString,box
from shapely.affinity import translate
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.analysis.mounting_layout import derive_layout

def resolve():
    reg=json.loads((ROOT/'data/derived/registration.json').read_text());T=np.array(reg['raw_to_installed_mm'])
    fc=json.loads((ROOT/'canon/features.json').read_text());dc=json.loads((ROOT/'canon/design_decisions.json').read_text())
    mc=json.loads((ROOT/'canon/measurements.json').read_text());accepted={m['id']:m['value_mm'] for m in mc['measurements'] if m['status']=='user-confirmed' and m.get('value_mm') is not None}
    resolved=[]
    for f in fc['features']:
        f=dict(f)
        if 'projected_contour_raw' in f:
            f['contour_mm']=[(T@np.r_[p,1])[:2].tolist() for p in f['projected_contour_raw']]
        if 'point_raw' in f:f['point_mm']=(T@np.r_[f['point_raw'],1])[:3].tolist()
        resolved.append(f)
    top=np.array(reg['landmarks_installed_mm']['AXIS-UPPER-TIP']['point_mm']);bottom=np.array(reg['landmarks_installed_mm']['AXIS-LOWER-TIP']['point_mm'])
    center=(top[:2]+bottom[:2])/2;inner_center=center.copy();angle=-math.degrees(math.atan2((top-bottom)[0],(top-bottom)[1]))
    a=dict(dc['visualization_assumptions']);nom=dict(dc['nominal_parameters'])
    for id,key in [('M02-W','inner_width_mm'),('M02-H','inner_height_mm'),('M04-T','inner_sheet_thickness_mm'),('M04-D','inner_formed_depth_mm'),('M04-R','rear_projection_envelope_mm'),('M04-H','hub_projection_envelope_mm'),('M05-OW','gasket_outer_width_mm'),('M05-OH','gasket_outer_height_mm'),('M05-W','gasket_width_mm'),('M05-T','gasket_free_thickness_mm'),('M06-C','outer_cavity_depth_mm')]:
        if id in accepted:a[key]=accepted[id]
    for id,key in [('M11-UD','inner_upper_opening_diameter_mm'),('M11-LD','inner_lower_opening_diameter_mm')]:
        if id in accepted:a[key]=accepted[id]
    # A representative foam width is not a measured minimum or a verified path.
    if 'M05-B' in accepted and 'M05-W' not in accepted:a['gasket_width_mm']=accepted['M05-B']
    depth_constraints={'overall_free_depth_mm':accepted.get('M04-O'),
        'free_foam_thickness_mm':accepted.get('M05-T'),
        'representative_band_width_mm':accepted.get('M05-B'),
        'installed_foam_thickness_mm':None,'foam_backing_to_front_mm':None,
        'metal_datum_relation':'Foam backing versus rear metal contact lands is unmeasured.',
        'display_basis':'Independent provisional metal and foam depths.'}
    if all(id in accepted for id in ('M04-O','M05-T')):
        remainder=accepted['M04-O']-accepted['M05-T']
        if remainder<=0:raise ValueError('Overall free depth must exceed foam thickness; reconcile measurement contacts')
        depth_constraints['foam_backing_to_front_mm']=remainder
        # Match the measured free envelope, without accepting this as M04-D.
        # The display alone equates its metal origin with the foam backing plane.
        if 'M04-D' not in accepted:
            a['inner_formed_depth_mm']=remainder
            depth_constraints['display_basis']='Measured free overall envelope; metal origin provisionally equals foam backing. Remainder is approximate, not sheet thickness or an accepted rear-land datum depth.'
        else:
            depth_constraints['display_basis']='Rear-land formed depth measured independently; compare free envelope and reconcile foam backing offset before fit approval.'
    if 'M06-OD' in accepted:nom['trim_diameter_mm']=accepted['M06-OD']
    if 'M01' in accepted:nom['control_spacing_mm']=accepted['M01']
    if all(k in accepted for k in ('M06-OD','M12-LCB')):
        center[1]=bottom[1]+nom['trim_diameter_mm']/2-accepted['M12-LCB']
    for i,axis in enumerate(['X','Y']):
        if all(k in accepted for k in ['M06-OD','M06-'+axis+'N','M06-'+axis+'F']):
            center[i]=bottom[i]+nom['trim_diameter_mm']/2-(accepted['M06-'+axis+'N']+accepted['M06-'+axis+'F'])/2
    outer_holes=[]
    for name,point in [('lower',bottom),('upper',top)]:
        id='M12-'+('LD' if name=='lower' else 'UD');local=point[:2]-center
        if name=='upper' and 'M12-CCY' in accepted:
            local[1]=bottom[1]-center[1]+accepted['M12-CCY']
        outer_holes.append({'name':name,'center_local_mm':local.tolist(),'diameter_mm':accepted.get(id,36),
            'diameter_status':'user-confirmed' if id in accepted else '36 mm display assumption; independently measure this opening',
            'placement_status':'lower opening provisionally aligned with observed lower tip; upper vertical spacing measured' if 'M12-CCY' in accepted else 'scan-axis display alignment; actual cover opening registration unmeasured'})
    outer_constraints={'source':'SRC-USER-OUTER-PLATE-01','photo_face':'front toward handles',
        'inside_opening_edge_gap_mm':accepted.get('M12-G'),'bottom_rim_to_lower_inside_edge_mm':accepted.get('M06-YN'),
        'vertical_center_spacing_mm':accepted.get('M12-CCY'),'lower_center_from_bottom_mm':accepted.get('M12-LCB'),
        'rear_cavity_measured':'M06-C' in accepted,
        'placement_note':'Loose-cover measurements do not rescale the primary scan or move captured control/stud geometry. Lower opening alignment with the lower tip is provisional; fit and retention remain unverified.'}
    maxrad=max(np.linalg.norm(np.array(f['contour_mm'])-center,axis=1).max() for f in resolved if f.get('include_in_coverage'))
    studs=[list(reg['landmarks_installed_mm'][id]['point_mm']) for id in ['STUD-SW-TIP','STUD-NE-TIP']]
    slots=[]
    for name,point in zip(['SW','NE'],studs):
        if 'M07-'+name in accepted:point[2]=accepted['M07-'+name]
        diameter=accepted.get('M11-'+name+'D',a.get('mounting_hole_diameter_mm',7))
        slot={'center_mm':point[:2].copy(),'width_mm':diameter,'height_mm':diameter,'shape':'round; observed in user front photo',
              'diameter_status':'user-confirmed' if 'M11-'+name+'D' in accepted else 'display assumption; independently measure this hole',
              'status':'scan-driven provisional position'}
        slots.append(slot)
    # Solve the measured edge constraints without treating the unmeasured NE bore,
    # diagonal angle or vertical placement as accepted. Never move the scan/studs.
    if 'M11-G' in accepted and 'M11-R' in accepted:
        direction=np.array(studs[1][:2])-np.array(studs[0][:2]);direction/=np.linalg.norm(direction)
        cc=accepted['M11-G']+(slots[0]['width_mm']+slots[1]['width_mm'])/2
        ne=np.array(slots[1]['center_mm']);ne[0]=inner_center[0]+a['inner_width_mm']/2-accepted['M11-R']-slots[1]['width_mm']/2
        slots[1]['center_mm']=ne.tolist();slots[0]['center_mm']=(ne-direction*cc).tolist()
        for slot in slots:slot['status']='measured edge constraints; NE diameter, diagonal angle and vertical placement remain provisional'
    for name,slot in zip(['SW','NE'],slots):
        for i,axis,extent in [(0,'X',a['inner_width_mm']),(1,'Y',a['inner_height_mm'])]:
            near='M03-'+name+'-'+axis+'N';far='M03-'+name+'-'+axis+'F'
            if near in accepted and far in accepted:
                slot['center_mm'][i]=float(inner_center[i]-extent/2+(accepted[near]+accepted[far])/2)
                slot['width_mm' if i==0 else 'height_mm']=accepted[far]-accepted[near]
                slot['status']='paired edge datums override provisional coordinates; check residuals against diagonal and rim gaps'
    layout=derive_layout(accepted)
    if layout:
        for label,slot in zip(['B','A'],slots):
            slot['center_mm']=(inner_center+np.array(layout['outline_centered_xy_up_mm'][label])).tolist()
            slot['width_mm']=slot['height_mm']=layout['diameters_mm'][label]
            slot['diameter_status']='user-confirmed'
            slot['status']='Final planar TOP/LEFT survey; outline-frame preview only, installed registration separate'
        a['inner_photo_basis']='Measured face outline, upper aperture and both mounting bores/positions. Lower opening, corner radii and formed depths remain reference assumptions.'
    holes=[]
    for i,point in enumerate([bottom,top]):
        local=point[:2]-inner_center
        if i==1 and 'M11-UC' in accepted:local[1]=a['inner_height_mm']/2-accepted['M11-UC']
        holes.append({'center_local_mm':local.tolist(),'diameter_mm':a['inner_lower_opening_diameter_mm' if i==0 else 'inner_upper_opening_diameter_mm'],
                      'status':'upper diameter/top gap measured; horizontal centering provisional' if i==1 and 'M11-UC' in accepted else 'unmeasured display reference'})
    plate_constraints={'photo_face':'front toward handles','source':'SRC-USER-INNER-PLATE-01',
        'mounting_center_spacing_mm':accepted.get('M11-CC'),
        'conditional_display_center_spacing_mm':float(np.linalg.norm(np.array(slots[1]['center_mm'])-np.array(slots[0]['center_mm']))),
        'missing':['NE mounting-hole diameter','lower large-opening diameter','mounting-hole vertical datums','outline corner shape/radii','rear gasket footprint','sheet thickness, rear metal datum, rim and nut-seat depths','installed foam compression'],
        'placement_note':'No plate photograph or measurement changes the primary wall registration or captured hardware pose.'}
    if layout:
        plate_constraints['active_locating_layout']=layout
        plate_constraints['mounting_center_spacing_mm']=layout['center_distance_mm']
        plate_constraints['missing']=[x for x in plate_constraints['missing'] if x not in ['NE mounting-hole diameter','mounting-hole vertical datums']]
    # Source geometry is used once for this conditional provisional scale. No independent validation is claimed.
    candidate=dict(dc['candidate']);land=candidate['target_sound_land_mm'];dia=math.ceil(2*(maxrad+land+1.5)/candidate['diameter_rounding_mm'])*candidate['diameter_rounding_mm']
    # Rounded rectangular aperture accommodates observed valve/body/stud envelope; not merely copied factory holes.
    candidate.update({'diameter_mm':dia,'max_traced_damage_radius_mm':float(maxrad),'center_mm':center.tolist(),
                      'aperture_width_mm':118,'aperture_height_mm':136,'aperture_radius_mm':14,'aperture_center_mm':[2,35],
                      'aperture_purpose':'clear visible valve/body/stud envelope for axial installation; conservative draft requires full-mesh slice and gasket check',
                      'separate_fastener_holes':[],'hole_policy':'no additional holes: both observed stud paths fall in the single aperture; verify thread/service paths before design release',
                      'seal_display_thickness_mm':1,'seal_thickness_status':'visual separator only; actual cured layer unknown'})
    diverter=reg['landmarks_installed_mm']['AXIS-DIVERTER-TIP']['point_mm']
    observations=json.loads((ROOT/'canon/observations.json').read_text())['observations']
    parameters={'project_id':'shower-kohler-valve','revision':mc['revision'],'status':'DRAFT_NOT_FOR_FABRICATION','units':'mm',
        'frame':'installed','trim_center_mm':center.tolist(),'trim_in_plane_rotation_deg':angle,
        'centering_status':'inferred midpoint of observed control tips; actual outer-trim relation and retention unverified',
        'controls_mm':[bottom.tolist(),top.tolist()],'diverter_tip_mm':diverter,'observations':observations,
        'diagnostic_control_depths_mm':{name:accepted[id] for name,id in [('upper','M10-UPPER'),('lower','M10-LOWER')] if id in accepted},
        'studs_mm':studs,'studs_state':'current measured envelopes where available; raw as-capture scan preserved',
        'inner_center_mm':inner_center.tolist(),'inner_slots':slots,'inner_control_openings':holes,'inner_plate_constraints':plate_constraints,'inner_plate_depth':depth_constraints,
        'outer_control_openings':outer_holes,'outer_plate_constraints':outer_constraints,
        'assumptions':a,'nominal':nom,'candidate':candidate,'accepted_measurement_ids':list(accepted),
        'scale_status':reg['scale_status'],'secondary_scans_used_to_fit':False,'features':resolved}
    out=ROOT/'data/derived/resolved.json';out.write_text(json.dumps(parameters,indent=2)+'\n');return parameters

if __name__=='__main__':
    d=resolve();print('Draft candidate diameter',d['candidate']['diameter_mm'],'mm; trim center',d['trim_center_mm'])
