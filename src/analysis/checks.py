from pathlib import Path
import json,math,numpy as np
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
from shapely.affinity import translate
from depth import analyze_depth
ROOT=Path(__file__).resolve().parents[2]

def capsule(w,h):return LineString([(0,-(h-w)/2),(0,(h-w)/2)]).buffer(w/2,quad_segs=128)

def run():
    d=json.loads((ROOT/'data/derived/resolved.json').read_text());reg=json.loads((ROOT/'data/derived/registration.json').read_text());a=d['assumptions'];c=d['candidate'];center=np.array(d['trim_center_mm'])
    features=d['features'];checks=[];coverage=[]
    accepted={m['id']:m for m in json.loads((ROOT/'canon/measurements.json').read_text())['measurements'] if m['status']=='user-confirmed'}
    byid={f['id']:f for f in features if 'contour_mm' in f}
    independent_predictions={
        'M08-X':max(p[0] for p in byid['CUT-03']['contour_mm'])-min(p[0] for p in byid['CUT-01']['contour_mm']),
        'M08-Y':max(p[1] for p in byid['CUT-01']['contour_mm'])-min(p[1] for p in byid['CUT-06']['contour_mm'])}
    for id,prediction in independent_predictions.items():
        measured=accepted.get(id)
        checks.append({'id':'INDEPENDENT-'+id,'status':'UNRESOLVED','prediction_mm':prediction,
            'physical_value_mm':measured['value_mm'] if measured else None,
            'physical_minus_model_mm':measured['value_mm']-prediction if measured else None,
            'used_to_fit':False,'conditional_result':'Residual reported; physical uncertainty and feature correspondence need review' if measured else 'No physical cross-check supplied',
            'criterion':'independent horizontal/vertical dimensions agree within justified measurement and tracing bounds',
            'needed':'M08 raw observations and uncertainty; do not silently rescale to erase disagreement'})
    for f in features:
        if not f.get('include_in_coverage'):continue
        points=np.array(f['contour_mm']);rr=np.linalg.norm(points-center,axis=1);k=int(np.argmax(rr))
        margins={'nominal_trim':d['nominal']['trim_diameter_mm']/2-rr[k],'prior_8in':101.6-rr[k],'prior_8_25in':104.775-rr[k],'candidate':c['diameter_mm']/2-rr[k]}
        coverage.append({'feature_id':f['id'],'state':'as_observed_at_capture','revision':d['revision'],'units':'mm','status':'UNRESOLVED',
            'result_type':'conditional projected geometry','limiting_point_mm':points[k].tolist(),'max_radius_mm':float(rr[k]),
            'outer_margin_mm':{k:float(v) for k,v in margins.items()},'candidate_margin_after_1_5mm_trace_allowance':float(margins['candidate']-1.5),
            'criterion':'conceal all damage and provide reviewed sound support/seal land; 10 mm exploratory allowance only',
            'source':f['source'],'unknowns':['absolute scale error','unseen defects','physical trim registration','sound stone and grout','installation placement']})
    worst=min(coverage,key=lambda x:x['outer_margin_mm']['candidate'])
    checks.append({'id':'COVERAGE-01','status':'UNRESOLVED','feature_ids':[x['feature_id'] for x in coverage],
        'conditional_result':'8-inch circle does not contain the entire traced damage envelope' if worst['outer_margin_mm']['prior_8in']<0 else '8-inch outline covers traced points but sound landing unproven',
        'limiting_feature':worst['feature_id'],'candidate_diameter_mm':c['diameter_mm'],'minimum_outline_margin_mm':worst['outer_margin_mm']['candidate'],
        'needed':'M01 scale, M08 damage extents, outer trim relationship and sound land verification'})
    opening=Polygon(next(f['contour_mm'] for f in features if f['id']=='OPEN-MAIN'))
    ic=d['inner_center_mm'];gw=a.get('gasket_outer_width_mm',a['inner_width_mm']);gh=a.get('gasket_outer_height_mm',a['inner_height_mm'])
    gout=translate(capsule(gw,gh),*ic)
    gin=translate(capsule(gw-2*a['gasket_width_mm'],gh-2*a['gasket_width_mm']),*ic)
    gasket=gout.difference(gin)
    ap=box(-c['aperture_width_mm']/2+c['aperture_radius_mm'],-c['aperture_height_mm']/2+c['aperture_radius_mm'],c['aperture_width_mm']/2-c['aperture_radius_mm'],c['aperture_height_mm']/2-c['aperture_radius_mm']).buffer(c['aperture_radius_mm'],quad_segs=64)
    ap=translate(ap,*c['aperture_center_mm']);plate=Point(*center).buffer(c['diameter_mm']/2,quad_segs=256).difference(ap)
    unsupported_wall=gasket.intersection(opening);unsupported_plate=gasket.difference(plate)
    checks.append({'id':'GASKET-WALL','status':'UNRESOLVED','conditional_result':'FAIL under provisional gasket outline','unsupported_projected_area_mm2':unsupported_wall.area,
        'criterion':'entire actual foam contact path lands on suitable continuous surface','feature_ids':['GASKET-01','OPEN-MAIN'],
        'needed':'M02 actual inner outline; M05 actual gasket footprint, notches and condition; physical support check',
        'note':'Area is of an assumed contact band, not an observed gasket or demonstrated compression.'})
    checks.append({'id':'GASKET-CANDIDATE','status':'UNRESOLVED','conditional_result':'FAIL under provisional gasket/aperture dimensions' if unsupported_plate.area>.01 else 'contained only in provisional geometry',
        'unsupported_projected_area_mm2':unsupported_plate.area,'criterion':'aperture must not remove actual gasket landing','feature_ids':['GASKET-01','CUSTOM-01'],
        'needed':'Measure before choosing single large aperture; contouring/rebuilding may be necessary. Candidate is not selected.'})
    studs=np.array(d['studs_mm']);mountmid=studs[:,:2].mean(0)
    checks.append({'id':'CENTERING-01','status':'UNRESOLVED','trim_center_inferred_mm':center.tolist(),'mount_midpoint_mm':mountmid.tolist(),
        'trim_minus_mount_midpoint_mm':(center-mountmid).tolist(),'opening_centroid_mm':list(opening.centroid.coords)[0],
        'candidate_minus_trim_center_mm':[0,0],'inferred_control_line_rotation_deg':d['trim_in_plane_rotation_deg'],
        'nominal_visible_border_min_max_mm':[(c['diameter_mm']-d['nominal']['trim_diameter_mm'])/2]*2,
        'criterion':'repeatable physically retained position with adequate border and seal land','needed':'M03/M06 datums; removable registration method; physical centering/retention test',
        'note':'Concentric placement is a design assumption, not proof of how the part is located.'})
    for id,p in zip(['STUD-SW','STUD-NE'],studs):
        checks.append({'id':'DEPTH-'+id,'feature_ids':[id+'-TIP'],'status':'UNRESOLVED','observed_tip_z_mm':float(p[2]),
            'guide_nominal_max_mm':11.1125,'guide_sources':['SRC-KOHLER-OLD-GUIDE p7','SRC-KOHLER-CURRENT-GUIDE step10'],
            'tip_minus_original_wall_limit_mm':float(p[2]-11.1125),'guide_datum':'finished wall, explicitly stated in 1041504-2-F p7','conditional_result':'apparent excess; confirm physical depth and applicable hardware before adjustment',
            'needed':'M07 physical straightedge-to-tip depth and thread/adjustment inspection by installer; no cutting authorized'})
    diverter=np.array(d['diverter_tip_mm']);dn=d['nominal']['diverter_trim']
    separation=float(np.linalg.norm(center-diverter[:2]));direction=(diverter[:2]-center)/separation
    gap=separation-c['diameter_mm']/2-dn['diameter_mm']/2
    checks.append({'id':'NEIGHBOR-TRIM-CLEARANCE','status':'UNRESOLVED','feature_ids':['CUSTOM-01','DIVERTER-TRIM','AXIS-DIVERTER-TIP'],
        'method':'projected circle separation in fitted stone plane; scan-derived center and nominal diameters',
        'center_separation_mm':separation,'candidate_to_diverter_gap_mm':gap,
        'factory_main_to_diverter_gap_mm':separation-d['nominal']['trim_diameter_mm']/2-dn['diameter_mm']/2,
        'gap_endpoints_xy_mm':[(center+direction*c['diameter_mm']/2).tolist(),(diverter[:2]-direction*dn['diameter_mm']/2).tolist()],
        'conditional_result':f'{gap:.1f} mm projected gap between candidate and separate diverter trim; no clearance certification',
        'criterion':'space for both actual trim rims, centering error, seal access, full handle operation and removal tools',
        'needed':'physical lower trim center/OD, registration, real handle travel and tool-access dry fit; scale/placement bounds unknown'})
    lower_separation=float(np.linalg.norm(np.array(d['controls_mm'][0][:2])-diverter[:2]))
    reach=d['nominal']['handle_lever_long_reach_mm']+dn['lever_long_reach_mm']
    checks.append({'id':'NEIGHBOR-HANDLE-ENVELOPE','status':'UNRESOLVED','center_separation_mm':lower_separation,
        'sum_nominal_long_reaches_mm':reach,'full_circle_projection_gap_mm':lower_separation-reach,
        'conditional_result':'Projected full-rotation reach circles overlap; this is not proof of actual collision',
        'criterion':'all actual permitted handle positions have physical clearance and tool/removal access',
        'needed':'on-site operating range, handle profiles and depth offsets; do not assume both rotate through full circles',
        'sources':['SRC-KOHLER-SPEC p3','SRC-SMALL-TRIM-SPEC p3','SCAN-WALL'],
        'note':'Uses centerline tip reaches only; section width and fingers/tools require additional space.'})
    # Full-resolution raw mesh vertex test in the proposed plate slice. No proxy use.
    v=np.load(ROOT/'data/derived/shower-hole-valve-polycam-vertices.npy');T=np.array(reg['raw_to_installed_mm']);v=v@T[:3,:3].T+T[:3,3]
    from shapely import contains_xy
    sel=(v[:,2]>=c['seal_display_thickness_mm'])&(v[:,2]<=c['seal_display_thickness_mm']+c['thickness_mm'])
    samples=v[sel];inside=contains_xy(opening.buffer(-1.5),samples[:,0],samples[:,1]);samples=samples[inside]
    hits=samples[contains_xy(plate,samples[:,0],samples[:,1])]
    checks.append({'id':'MESH-PLATE-SLICE','status':'UNRESOLVED','method':'full-resolution vertex sample inside opening at proposed plate depth; triangle crossings/hidden geometry not certified',
        'vertices_in_slice':len(samples),'vertices_in_candidate_material':len(hits),'example_points_mm':hits[:10].tolist(),
        'conditional_result':'captured vertex penetration' if len(hits) else 'no sampled vertex penetration; not a clearance pass',
        'needed':'physical clearance / thickness mockup; triangle-level check after accepted scale and aperture decisions'})
    grout=LineString(next(f['contour_mm'] for f in features if f['id']=='GROUT-01'))
    seal=Point(*center).buffer(c['diameter_mm']/2-6,quad_segs=256).boundary
    checks.append({'id':'NEW-SEAL-GROUT','status':'UNRESOLVED','crossings':str(seal.intersection(grout)),
        'criterion':'continuous compatible surface seal and support over actual substrate topography','needed':'grout recess width/depth/soundness and selected compatible sealing detail',
        'note':'Candidate land crosses GROUT-01. A planar annulus in CAD is not a continuous real landing.'})
    for id,purpose,need in [
        ('STRUCTURAL-SUPPORT','plate span stiffness and load path','supported contact map, retaining/clamping force, material/process, physical rocking/load check'),
        ('INSTALLATION-PATH','axial installation, removal and tools','thickness mockup; hubs/stud/nut envelope, handle removal and wrench access'),
        ('THREAD-ENGAGEMENT','correct stud, nut and handle engagement','installer observes threads and adapter selection; do not infer from tip'),
        ('WATERPROOFING','concealed water barrier continuity','qualified inspection through existing access and compatible repair detail')]:
        checks.append({'id':id,'status':'UNRESOLVED','criterion':purpose,'needed':need})
    new_state_note=json.loads((ROOT/'canon/project_state.json').read_text()).get('latest_user_state_note','').strip()
    checks.append({'id':'POST-SCAN-STATE','status':'UNRESOLVED' if new_state_note else 'PASS','result_type':'user report only; not a physical fit check',
        'conditional_result':'New current-state note requires reconciliation: '+new_state_note if new_state_note else 'User reports nothing has changed since capture (2026-10-14)',
        'criterion':'obtain explicit current-state report','source':'OBS-POST-SCAN-01',
        'needed':'report any future piping, valve, stud or wall changes before relying on this state'})
    # Exact checks on provisional reference solids, distinguished from physical fit.
    import cadquery as cq
    cm=json.loads((ROOT/'data/derived/cad/parts.json').read_text());parts={p['id']:p for p in cm['parts']}
    depth=analyze_depth(d,cm)
    for case,record in depth['cases'].items():
        for clash in record['collisions']:
            checks.append({'id':'CAD-CLASH-'+('FACTORY-' if case=='factory' else '')+clash['part'],
                'status':'FAIL' if clash['model_result']=='FAIL' else 'UNRESOLVED',
                'conditional_result':clash['model_result']+' in '+record['label'].lower(),
                'intersection_mm3':clash['intersection_mm3'],'physical_fit':'UNRESOLVED',
                'method':'exact OCCT common volume of disclosed reference solids; not a physical measurement',
                'needed':'actual local cavity, nut/inner-plate/valve profiles and stud depth; reversible factory adjustment feasibility'})
    result={'project_id':d['project_id'],'revision':d['revision'],'units':'mm','state':'diagnostic_trial_with_unchanged_hardware','fit_verdict':'FAIL in provisional geometry / physical fit UNRESOLVED / candidate not selected',
        'readiness':'DRAFT_NOT_FOR_FABRICATION','coverage':coverage,'checks':checks,
        'error_budget':{'scan_scale':{'bound_mm':None,'note':'nominal control spacing used as fit input, not independent scale check'},
            'feature_tracing':{'bound_mm':1.5,'note':'conditional R001 projection selection allowance'},'registration':{'absolute_bound_mm':None,'plane_consistency_rms_mm':reg['plane']['all_selected_rms_mm']},
            'physical_measurement':{'bound_mm':None},'fabrication':{'bound_mm':None},'installation_placement':{'bound_mm':None},
            'CAD_tessellation':{'linear_tolerance_mm':.04,'note':'export setting, not a physical tolerance; analytic STEP/DXF checked separately'},
            'combination':'No probabilistic RSS: scale is shared; unresolved bounds prevent a demonstrated fit pass.'},
        'alternatives':[
          {'id':'ALT-FACTORY','name':'Factory stud/adapter adjustment','viability':'may resolve seating only; does not repair oversized opening or missing gasket support'},
          {'id':'ALT-REBUILD','name':'Supported local rebuilding','viability':'potentially avoids added stack depth; backing access, sound substrate and waterproofing detail must be established'},
          {'id':'ALT-PLATE','name':'Custom backing plate','viability':'conditional coverage; current assumed aperture/gasket conflict prevents selection; support/retention/sealing unverified'},
          {'id':'ALT-COMBINATION','name':'Supported local repair plus shaped plate','viability':'may provide gasket landing with smaller apertures; no selected materials or permanent instructions yet'}]}
    OUT=ROOT/'deliverables/current/analysis';OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'depth_stack.json').write_text(json.dumps(depth,indent=2)+'\n')
    (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
    schedule={'project_id':d['project_id'],'revision':d['revision'],'status':'DRAFT / inspection schedule, no adjustment authorized','units':'mm',
        'items':[
          {'id':'STUD-'+name,'datum':'finished wall per 1041504-2-F p7; current measurements use original intact-stone plane',
           'current_model_tip_z_mm':p[2],'current_status':'accepted M07 depth' if 'M07-'+name in accepted else 'conditional scan estimate',
           'proposed_target_mm':None,'guide_comparison_mm':11.1125,'guide_context':'7/16 inch maximum from finished wall, explicit in 1041504-2-F p7. Not a stud-cut length or automatic target above a custom backing plate.',
           'responsible':'qualified plumber','prerequisites':['M07 depth readings','usable thread/adapter arrangement','selected final layer thickness'],
           'on_site_check':'Verify reversible factory adjustment, engagement and free outer-trim seating. No shortening or valve movement approved.'}
          for name,p in zip(['SW','NE'],studs)]+
          [{'id':'VALVE-POSE','current':'new state report requires reconciliation: '+new_state_note if new_state_note else 'scan pose retained; user confirms no post-scan changes 2026-10-14 (OBS-POST-SCAN-01)','proposed_translation_mm':None,'proposed_rotation_deg':None,'responsible':'qualified plumber','prerequisites':['physical access and pressure test'],'on_site_check':'Record any future real change before new fit assessment; no proposed move.'},
           {'id':'LANDING','current':'opening interrupts assumed factory gasket path','proposed':'continuous supported landing, detail unselected','responsible':'tile/waterproofing installer','prerequisites':['actual gasket trace','backing access and soundness','waterproofing-system identification'],'on_site_check':'Demonstrate full contact, rigid support and compatible sealing without cutting travertine.'} ]}
    (OUT/'contractor_schedule.json').write_text(json.dumps(schedule,indent=2)+'\n')
    for filename,data in [('registration.json',reg),('resolved.json',d)]: (OUT/filename).write_text(json.dumps(data,indent=2)+'\n')
    print('Worst feature',worst['feature_id'],'8-inch margin',round(worst['outer_margin_mm']['prior_8in'],2),'draft margin',round(worst['outer_margin_mm']['candidate'],2))
    print('Assumed gasket unsupported area: wall',round(unsupported_wall.area),'mm2; candidate',round(unsupported_plate.area),'mm2; all physical fit unresolved')
    return result

if __name__=='__main__':run()
