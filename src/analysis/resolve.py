"""Resolve design parameters from evidence, with no writes to accepted canon."""
from pathlib import Path
import json,math,numpy as np
from shapely.geometry import Polygon,Point,LineString,box
from shapely.affinity import translate
ROOT=Path(__file__).resolve().parents[2]

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
    if 'M06-OD' in accepted:nom['trim_diameter_mm']=accepted['M06-OD']
    if 'M01' in accepted:nom['control_spacing_mm']=accepted['M01']
    for i,axis in enumerate(['X','Y']):
        if all(k in accepted for k in ['M06-OD','M06-'+axis+'N','M06-'+axis+'F']):
            center[i]=bottom[i]+nom['trim_diameter_mm']/2-(accepted['M06-'+axis+'N']+accepted['M06-'+axis+'F'])/2
    maxrad=max(np.linalg.norm(np.array(f['contour_mm'])-center,axis=1).max() for f in resolved if f.get('include_in_coverage'))
    studs=[list(reg['landmarks_installed_mm'][id]['point_mm']) for id in ['STUD-SW-TIP','STUD-NE-TIP']]
    slots=[]
    for name,point in zip(['SW','NE'],studs):
        if 'M07-'+name in accepted:point[2]=accepted['M07-'+name]
        slot={'center_mm':point[:2].copy(),'width_mm':a['stud_clearance_slot_width_mm'],'height_mm':a['stud_clearance_slot_length_mm'],'status':'scan-driven provisional hole'}
        for i,axis,extent in [(0,'X',a['inner_width_mm']),(1,'Y',a['inner_height_mm'])]:
            near='M03-'+name+'-'+axis+'N';far='M03-'+name+'-'+axis+'F'
            if near in accepted and far in accepted:
                slot['center_mm'][i]=float(inner_center[i]-extent/2+(accepted[near]+accepted[far])/2)
                slot['width_mm' if i==0 else 'height_mm']=accepted[far]-accepted[near];slot['status']='accepted edge dimensions; part placement still provisional'
        slots.append(slot)
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
        'inner_center_mm':inner_center.tolist(),'inner_slots':slots,
        'assumptions':a,'nominal':nom,'candidate':candidate,'accepted_measurement_ids':list(accepted),
        'scale_status':reg['scale_status'],'secondary_scans_used_to_fit':False,'features':resolved}
    out=ROOT/'data/derived/resolved.json';out.write_text(json.dumps(parameters,indent=2)+'\n');return parameters

if __name__=='__main__':
    d=resolve();print('Draft candidate diameter',d['candidate']['diameter_mm'],'mm; trim center',d['trim_center_mm'])
