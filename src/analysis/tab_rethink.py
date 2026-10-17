"""TR02: local tab alternative and two separate scan diagnostics; no canon edits."""
from pathlib import Path
import sys,json,hashlib,math,copy
import numpy as np
import cadquery as cq
import trimesh
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
from shapely.affinity import affine_transform,translate
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.fabrication.fit_trial import make_main,rr
from src.analysis.fit_trial_release import load_capture,slice_project
from src.analysis.registration_trial import coeff
from src.analysis.control_alignment import fit_cap
BUILD=ROOT/'build/FT02/tab_rethink'
OUT=ROOT/'deliverables/current/fabrication/FT02/tab-rethink'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def top_profile(path):
    """Project the actual exported CAD top triangles, including root fillets."""
    mesh=trimesh.load(path,force='mesh');tri=mesh.triangles
    top=tri[np.all(np.abs(tri[:,:,2]-mesh.bounds[1,2])<.001,axis=1)]
    result=unary_union([Polygon(t[:,:2]) for t in top])
    assert result.is_valid and result.geom_type=='Polygon'
    return result

def run():
    BUILD.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    d=read('canon/fit_trial_design.json');r=read('data/derived/resolved.json')
    old=read('deliverables/current/fabrication/FT02/engineering/locator_evaluation.json')
    centers=old['transforms']['mounting_centers_in_cover_frame_mm'];t=1.50
    plain=make_main(d,t);oldpart=make_main(d,t,centers);part=plain
    ap=rr(d['main']['aperture_width_mm'],d['main']['aperture_height_mm'],d['main']['aperture_radius_mm'])
    disk=Point(0,0).buffer(110,quad_segs=256);profile=disk.difference(ap)
    slots={};added=[]
    for name,p in centers.items():
        p=np.array(p);side=np.sign(p[0]);inner=p-np.array([side*8,0]);root=np.array([side*67,p[1]])
        raw=LineString([root,inner]).buffer(9,quad_segs=128)
        hole=LineString([p,inner]).buffer(5,quad_segs=128)
        assert ap.covers(hole), 'Slot must remain wholly inside the original aperture'
        tab=cq.Workplane('XY').center(*(root+inner)/2).slot2D(abs(root[0]-inner[0])+18,18,0).extrude(t)
        part=part.union(tab);profile=profile.union(raw).difference(hole)
        slots[name]={'outer_cap_center_mm':p.tolist(),'inner_cap_center_mm':inner.tolist(),'slot_center_mm':((p+inner)/2).tolist(),'size_mm':[18,10],'minimum_slot_to_original_aperture_mm':ap.boundary.distance(hole),'minimum_nominal_end_web_mm':4}
        added.append((raw,hole))
    part=part.edges('|Z').fillet(1.5)
    for s in slots.values():
        part=part.cut(cq.Workplane('XY').center(*s['slot_center_mm']).slot2D(18,10,0).extrude(t+2).translate((0,0,-1)))
    # Exact solid checks prove only the intended local design change.
    removed=plain.cut(part).val().Volume();assert removed<1e-6,removed
    assert len(part.val().Solids())==1 and part.val().isValid()
    p2=part.faces('>Z').wires().translate((0,0,-t))
    assert len(p2.vals())==4
    assets={}
    for name,obj in [('plain',plain),('previous_tabs',oldpart),('longer_tabs',part)]:
        path=BUILD/(name+'.stl');cq.exporters.export(obj,str(path),tolerance=.015,angularTolerance=.04)
        mesh=trimesh.load(path,force='mesh');assert mesh.is_watertight
        assets[name]={'path':str(path.relative_to(ROOT)),'sha256':sha(path),'bounds_mm':mesh.bounds.tolist()}
    profile=top_profile(BUILD/'longer_tabs.stl')
    step=BUILD/'TR02_LONGER_TABS_EXPLANATORY_NOT_RELEASED.step'
    cq.exporters.export(part,str(step));back=cq.importers.importStep(str(step)).val()
    assert back.isValid() and len(back.Solids())==1 and abs(back.Volume()-part.val().Volume())<.01
    foam=d['foam'];fo=rr(foam['outer_width_mm'],foam['outer_height_mm'],40);fi=rr(foam['outer_width_mm']-12,foam['outer_height_mm']-12,34)
    band=translate(fo.difference(fi),yoff=old['transforms']['inner_outline_to_cover_xy_up']['translation_mm'][1])
    assert profile.intersection(band).area>=disk.difference(ap).intersection(band).area-1e-6
    v,f=load_capture();Q=np.array(old['transforms']['cover_to_installed_xy_up']['row_rotation']);origin=np.array(old['transforms']['cover_to_installed_xy_up']['translation_mm'])
    tris=v[f];mn=tris.min(1);mx=tris.max(1);tris=tris[(mx[:,0]>-120)&(mn[:,0]<125)&(mx[:,1]>-80)&(mn[:,1]<155)]
    extra=affine_transform(profile.difference(disk.difference(ap)),coeff(Q,origin))
    collision=[];capture_slices={}
    for label,lo,hi in [('seated_illustrative_1mm_bed',1,2.5),('full_insertion_current_capture',1,80)]:
        pieces=slice_project(tris,lo,hi);full=unary_union(pieces);capture_slices[label]=full;hit=extra.intersection(full)
        collision.append({'case':label,'z_mm':[lo,hi],'added_tab_projected_surface_overlap_mm2':hit.area,'bounds_mm':list(hit.bounds) if not hit.is_empty else [],'scope':'Actual CAD top-face tessellation, including root fillets, versus captured triangle projection. Placement approximate. Not full solid collision or physical fit.'})
    narrowing=[]
    for inset in [0,1,2]:
        nd=copy.deepcopy(d)
        for key in ['aperture_width_mm','aperture_height_mm']:nd['main'][key]-=2*inset
        nd['main']['aperture_radius_mm']-=inset
        nap=rr(nd['main']['aperture_width_mm'],nd['main']['aperture_height_mm'],nd['main']['aperture_radius_mm'])
        npart=make_main(nd,t);npf=disk.difference(nap)
        for (name,p),(raw,hole) in zip(centers.items(),added):
            p=np.array(p);side=np.sign(p[0]);inner=p-[side*8,0];root=np.array([side*67,p[1]])
            npart=npart.union(cq.Workplane('XY').center(*(root+inner)/2).slot2D(abs(root[0]-inner[0])+18,18,0).extrude(t))
            npf=npf.union(raw).difference(hole)
        npart=npart.edges('|Z').fillet(1.5)
        for s in slots.values():npart=npart.cut(cq.Workplane('XY').center(*s['slot_center_mm']).slot2D(18,10,0).extrude(t+2).translate((0,0,-1)))
        assert npart.val().isValid() and len(npart.val().Solids())==1
        sp=BUILD/f'inward_{inset}.stl';cq.exporters.export(npart,str(sp),tolerance=.015,angularTolerance=.04)
        npf=top_profile(sp)
        assets[f'inward_{inset}']={'path':str(sp.relative_to(ROOT)),'sha256':sha(sp),'bounds_mm':trimesh.load(sp,force='mesh').bounds.tolist()}
        st=OUT/f'TR02_INWARD_{inset}MM_TABS_EXPLANATORY_NOT_RELEASED.step';cq.exporters.export(npart,str(st))
        rb=cq.importers.importStep(str(st)).val();assert rb.isValid() and len(rb.Solids())==1
        growing=npf.difference(profile);checks=[]
        for label,cap in capture_slices.items():
            hit=affine_transform(growing,coeff(Q,origin)).intersection(cap)
            checks.append({'case':label,'extra_ring_overlap_mm2':hit.area,'bounds_mm':list(hit.bounds) if not hit.is_empty else []})
        # Support reserve to any internal cut, including the enlarged tab slots.
        innercuts=disk.difference(npf);reserve=innercuts.distance(band)
        control=[]
        for name,cy,radius in [('U',40.09,24.23),('L',-39.95,25)]:
            footprint=Point(0,cy).buffer(radius,quad_segs=128)
            overlap=footprint.intersection(npf).area
            control.append({'control':name,'reference_diameter_mm':radius*2,'material_overlap_mm2':overlap,'clearance_to_material_mm':npf.distance(footprint),'scope':'Factory opening footprint, not measured handle rear diameter. Lower 50 mm is provisional; no axial engagement proof.'})
        narrowing.append({'inward_per_edge_mm':inset,'capsule_mm':[nd['main']['aperture_width_mm'],nd['main']['aperture_height_mm'],nd['main']['aperture_radius_mm']],'nominal_min_foam_reserve_including_slots_mm':reserve,'foam_overlap_area_mm2':npf.intersection(band).area,'complete_nominal_foam_area_mm2':band.area,'capture_checks':checks,'factory_opening_footprints':control,'step':str(st.relative_to(ROOT))})
    # Preserve the original scan transform; calculate a separate local comparison.
    original={k:np.array(p) for k,p in zip(['L','U','B','A'],r['controls_mm']+r['studs_mm'])}
    fitted={};fits={};sensitivity=[]
    for name,p in original.items():
        vv=v[np.linalg.norm(v[:,:2]-p[:2],axis=1)<10]
        fit,_=fit_cap(vv,2);fits[name]=fit
        fitted[name]=np.r_[fit['center_xy_mm'],vv[:,2].max()]
    factor=80/np.linalg.norm(fitted['U']-fitted['L'])
    fit80={k:p*factor for k,p in fitted.items()}
    ass=read('deliverables/current/fabrication/fit-trial/attached_scan_assessment.json')
    pv=np.load(ROOT/'build/attached_scan/plane_vertices.npy');sv=ass['uniform_mm_per_raw_unit'];target=np.array(ass['view']['center']);pixel=1.4/1800
    picks={k:dict(ass['manual_visual_picks'][k]) for k in ['U','L']}
    for name,px in [('A',[1264,696]),('B',[510,1023])]:
        xy=target[:2]+(np.array(px)-[900,900])*[pixel,-pixel]
        idx=int(np.argmin(np.linalg.norm(pv[:,:2]-xy,axis=1)))
        picks[name]={'pixels':px,'zero_based_vertex':idx,'point_wall_units':pv[idx].tolist(),'method':'Visible end-center pixel selected on existing wall-normal render; nearest XY mesh vertex. Not a hidden bore center.'}
    L=np.array(picks['L']['point_wall_units'])
    attached={k:(np.array(p['point_wall_units'])-np.r_[L[:2],0])*sv for k,p in picks.items()}
    raw=read('docs/physical_checks/installed_center_distances_2026-10-15.json');table=[]
    for row in raw['observations']:
        a,b=[{'NE':'A','SW':'B'}.get(row[x],row[x]) for x in ['feature_a','feature_b']]
        table.append({'pair':a+'-'+b,'owner_3d_mm':row['value_mm'],'original_stored_picks_3d_mm':float(np.linalg.norm(original[a]-original[b])),'original_refitted_80_anchor_3d_mm':float(np.linalg.norm(fit80[a]-fit80[b])),'attached_visible_picks_3d_mm':float(np.linalg.norm(attached[a]-attached[b])),'attached_xy_mm':float(np.linalg.norm((attached[a]-attached[b])[:2]))})
    for depthband in [.5,1,1.5,2,2.5,3]:
        pp={}
        for name,p in original.items():
            vv=v[np.linalg.norm(v[:,:2]-p[:2],axis=1)<10];ft,_=fit_cap(vv,depthband);pp[name]=np.r_[ft['center_xy_mm'],vv[:,2].max()]
        sf=80/np.linalg.norm(pp['U']-pp['L']);sensitivity.append({'cap_depth_band_mm':depthband,'A_B_80_anchor_mm':float(np.linalg.norm(pp['A']-pp['B'])*sf)})
    sources=['canon/measurements.json','canon/fit_trial_design.json','canon/repair_form_design.json','deliverables/current/fabrication/FT02/REPAIR_FORM_TRIAL/RF01_MAIN_REMOVABLE_FORM_PETG.stl','data/derived/registration.json','data/derived/resolved.json','deliverables/current/fabrication/fit-trial/attached_scan_assessment.json','data/raw/polycam/shower-hole-valve-polycam.zip','data/raw/polycam/polycam-inner-plate-attached.zip']
    report={'id':'TR02','date':'2026-10-17','status':'EXPLANATORY_DESIGN_STUDY_NOT_RELEASED','latest_user_intent':'Tabs are approximate locators. Align the backing visually before retaining/bonding it. Concern is shower water entering the wall, not valve pressure leakage. Adding tabs does not itself shift the backing or foam.','assets':assets,'plate_pose':old['transforms']['cover_to_installed_xy_up'],'inner_pose':old['transforms']['inner_outline_to_cover_xy_up'],'centers':centers,'slots':slots,'geometry':{'outer_diameter_mm':220,'original_capsule_mm':[116.35,151.10,58.175],'sheet_mm':t,'tab_width_mm':18,'inward_slot_extension_mm':8,'root_fillet_mm':1.5,'plain_material_removed_mm3':removed,'plain_material_not_removed':True,'foam_pose_unchanged':True,'cutouts_within_original_aperture':True,'STEP_readback_valid_one_solid':True},'captured_surface_checks':collision,'scan_comparison':table,'original_cap_fits':fits,'original_diagnostic_scale_factor':factor,'original_fit_points_mm':{k:p.tolist() for k,p in fitted.items()},'original_cap_fit_sensitivity':sensitivity,'attached_visible_picks':picks,'attached_local_points_mm':{k:p.tolist() for k,p in attached.items()},'attached_outline_check_mm':ass['checks_mm'],'coplanar_factory_layout':read('canon/measurements.json')['active_locating_layout'],'limits':['Refitted primary is a separate calculation. Original scan and transform stay unchanged.','Both 80 mm anchored comparisons use that reading as calibration, not validation.','Tip or exposed fastener-end distances are not coplanar factory bore spacing and not stud-axis intersections with a new flat plate.','Attached-state hardware can obscure the original contact points; hidden rod axes cannot be checked from that scan.','Pick, shape, scale and seating differences are not certified machining tolerance bounds.','No partial foam support width, adhesive or final water seal is approved.','Existing no-tab vendor files and previous tabbed quote remain unchanged.'], 'sources_sha256':{p:sha(p) for p in sources},'official_reference':{'url':'https://resources.kohler.com/onlinecatalog/pdf/1041504_2.pdf','page':7,'basis':'Factory plate lies flat; foam surrounds opening; decorative drain remains down. Custom backing/bonding is a project adaptation, not a Kohler-approved repair.'}}
    report['inward_support_variants']=narrowing
    (OUT/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(BUILD/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'candidate':report['geometry'],'captured_surface_checks':collision,'narrowing':narrowing,'comparison':table,'sensitivity':sensitivity},indent=2))
if __name__=='__main__':run()
