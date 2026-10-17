"""TR03 diagnostic: smaller locators and deeper removable collar.

All XY values use the existing FT02 cover-frame working placement. No accepted
caliper value, source vertex, or primary transform is changed by this study.
"""
from pathlib import Path
import json, sys, math, hashlib, copy
import numpy as np
from shapely.geometry import Point, LineString, box, shape, Polygon
from shapely.ops import unary_union
from shapely.affinity import translate

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.analysis.fit_trial_release import load_capture, slice_project
from src.fabrication.fit_trial import rr

BUILD = ROOT / 'build/FT02/tab_refinement'
OUT = ROOT / 'deliverables/current/fabrication/FT02/tab-refinement'

def read(p):
    return json.loads((ROOT / p).read_text())

def slot_shape(p, length, width):
    p = np.asarray(p)
    dx = np.array([(length-width)/2, 0])
    return LineString([p-dx,p+dx]).buffer(width/2,quad_segs=96)

def load_local():
    previous=read('deliverables/current/fabrication/FT02/tab-rethink/analysis.json')
    q=np.asarray(previous['plate_pose']['row_rotation'])
    t=np.asarray(previous['plate_pose']['translation_mm'])
    v,f=load_capture()
    v[:,:2]=(v[:,:2]-t)@q.T
    return previous,v,f

def probe():
    BUILD.mkdir(parents=True,exist_ok=True)
    previous,v,f=load_local()
    tris=v[f]
    mn,mx=tris.min(1),tris.max(1)
    local=tris[(mx[:,0]>-75)&(mn[:,0]<75)&(mx[:,1]>-90)&(mn[:,1]<90)]
    centers=previous['centers']
    rods={}
    footprints={}
    for k in ['A','B']:
        p=np.asarray(centers[k]);radius=11
        mask=np.linalg.norm(v[:,:2]-p,axis=1)<radius
        tube=tris[np.all(mask[f],axis=1)]
        # Separate observed enlarged tip from visible shaft without editing the
        # source. These planes are diagnostic segmentation, not physical ends.
        cut=22 if k=='A' else 18
        visible=unary_union(slice_project(tube,0,cut))
        bins=[]
        for z in np.arange(1,cut-2,2):
            pts=v[mask & (v[:,2]>=z)&(v[:,2]<z+2)]
            if len(pts)>12:
                bins.append([z+1,*((pts[:,:2].min(0)+pts[:,:2].max(0))/2)])
        b=np.array(bins);fit=np.polyfit(b[:,0],b[:,1:],1)
        end=float(v[mask,2].max())
        xy0=np.polyval(fit[:,0],0),np.polyval(fit[:,1],0)
        xy1=np.polyval(fit[:,0],end),np.polyval(fit[:,1],end)
        # 5 mm is a deliberately chosen evaluation envelope, not a new measured
        # rod diameter. Extend it through the region hidden by the removable nut.
        envelope=LineString([xy0,xy1]).buffer(2.5,quad_segs=96)
        full=unary_union(slice_project(tube,0,80))
        seated=unary_union(slice_project(tube,1,2.52))
        front=unary_union(slice_project(tube,9.05,12.05))
        footprints[k]={'full':full,'visible_shaft':visible,'envelope':envelope,'seated':seated,'form_front':front}
        rods[k]={'shaft_only_z_mm':[0,cut], 'inferred_axis_fit_z_mm':b[:,0].tolist(),
                 'inferred_axis_xy_at_z0_mm':list(xy0),'inferred_axis_xy_at_end_mm':list(xy1),
                 'assumed_envelope_diameter_mm':5,'envelope_max_z_mm':end,
                 'visible_shaft_bounds_mm':list(visible.bounds),
                 'scope':'Captured shaft below diagnostic nut cutoff plus separate inferred 5 mm envelope through hidden nut region. No verified shaft diameter or physical accuracy bound.'}
    candidates=[]
    for length,width,inward in [(10,7,2),(12,7,2),(12,8,2),(14,8,2),(18,10,4)]:
        checks={}
        for k,p in centers.items():
            p=np.array(p);sc=p-[np.sign(p[0])*inward,0]
            hole=slot_shape(sc,length,width)
            checks[k]={'slot_center_mm':sc.tolist()}
            for key,shape in footprints[k].items():
                checks[k][key]={'outside_slot_mm2':shape.difference(hole).area,
                                'minimum_clearance_mm':hole.boundary.distance(shape) if hole.covers(shape) else 0}
        candidates.append({'length_mm':length,'width_mm':width,'center_inward_mm':inward,'rods':checks})
    collar=[]
    collar_views={}
    for dep in [12,18,24,30]:
        draft=dep*math.tan(math.radians(1))
        outer=rr(118.35,145.10,118.35/2)
        inner=rr(114.35-2*draft,141.10-2*draft,57.175-draft)
        conservative=outer.difference(inner)
        cases=[]
        for label,lo,hi in [('seated',.05-dep,.05),('insertion_withdrawal',.05-dep,80)]:
            surface=unary_union(slice_project(local,lo,hi));hit=surface.intersection(conservative)
            cases.append({'case':label,'z_mm':[lo,hi],'overlap_mm2':hit.area,'bounds_mm':list(hit.bounds) if not hit.is_empty else []})
            if label=='seated':collar_views[str(dep)]={'surface':surface.__geo_interface__,'collar':conservative.__geo_interface__,'hit':hit.__geo_interface__}
        openings=[]
        for name,y,dia in [('upper',40.09,48.46),('lower',-39.95,50)]:
            fp=Point(0,y).buffer(dia/2,quad_segs=96)
            openings.append({'name':name,'diameter_mm':dia,'contained':inner.covers(fp),'clearance_mm':inner.boundary.distance(fp)})
        collar.append({'depth_mm':dep,'smallest_inner_mm':[114.35-2*draft,141.10-2*draft], 'cases':cases,'opening_proxies':openings})
    data={'revision':'TR03-probe','rods':rods,'slot_candidates':candidates,'collar_candidates':collar}
    (BUILD/'probe.json').write_text(json.dumps(data,indent=2)+'\n')
    (BUILD/'footprints.json').write_text(json.dumps({k:{kk:g.__geo_interface__ for kk,g in p.items()} for k,p in footprints.items()}))
    (BUILD/'collar_views.json').write_text(json.dumps(collar_views))
    print(json.dumps(data,indent=2))

def deeper():
    """Conservative Z-banded wall and pull-forward sweep for draft alternatives."""
    previous,v,f=load_local();tris=v[f]
    mn,mx=tris.min(1),tris.max(1)
    tris=tris[(mx[:,0]>-65)&(mn[:,0]<65)&(mx[:,1]>-80)&(mn[:,1]<80)]
    # Every bin is independently clipped; its largest outer and smallest inner
    # bounds contain the actual collar portion. Retain interior and edge triangles.
    surfaces={}
    for i in range(15):
        hi=.05-i*2;lo=hi-2
        surfaces[i]=unary_union(slice_project(tris,lo,hi))
    front=unary_union(slice_project(tris,.05,80))
    results=[];views={}
    for dep in [18,24,30]:
        for deg in [1,3,5,7,9]:
            wall=2; w=118.35; h=145.1; overlaps=[];sweep=[]
            for i in range(dep//2):
                dh=i*2*math.tan(math.radians(deg));dl=(i+1)*2*math.tan(math.radians(deg))
                outer=rr(w-2*dh,h-2*dh,w/2-dh)
                inner=rr(w-2*wall-2*dl,h-2*wall-2*dl,w/2-wall-dl)
                ann=outer.difference(inner)
                hit=ann.intersection(surfaces[i]);overlaps.append(hit)
                # During forward removal, this band crosses every shallower bin.
                surface=unary_union([front]+[surfaces[j] for j in range(i+1)])
                sweep.append(ann.intersection(surface))
            seated=unary_union(overlaps);swept=unary_union(sweep)
            radial=dep*math.tan(math.radians(deg))
            inner=rr(w-4-2*radial,h-4-2*radial,w/2-2-radial)
            gaps=[]
            for name,y,dia in [('upper',40.09,48.46),('lower',-39.95,50)]:
                fp=Point(0,y).buffer(dia/2,quad_segs=96)
                gaps.append({'name':name,'within':inner.covers(fp),'clearance_mm':inner.boundary.distance(fp)})
            row={'depth_mm':dep,'draft_deg':deg,'rear_outer_mm':[w-2*radial,h-2*radial],
                 'rear_inner_mm':[w-4-2*radial,h-4-2*radial],
                 'seated_overlap_mm2':seated.area,'withdrawal_overlap_mm2':swept.area,'proxy_checks':gaps}
            results.append(row)
            views[f'{dep}_{deg}']={'seated':seated.__geo_interface__,'withdrawal':swept.__geo_interface__}
    (BUILD/'deeper.json').write_text(json.dumps(results,indent=2)+'\n')
    (BUILD/'deeper_views.json').write_text(json.dumps(views))
    print(json.dumps(results,indent=2))

def build():
    import cadquery as cq
    import trimesh
    from src.fabrication.fit_trial import make_main
    from src.fabrication.repair_form import cap
    from src.analysis.tab_rethink import top_profile
    OUT.mkdir(parents=True,exist_ok=True)
    cfg=read('canon/tab_refinement_study.json')
    previous,v,f=load_local();centers=previous['centers']; loc=cfg['locators']
    slots={}
    for k,p in centers.items():
        sc=np.array(p)+np.array(loc['center_offsets_from_R006_cover_coordinates_mm'][k])
        slots[k]={'center_mm':sc.tolist(),'factory_center_mm':p,'size_mm':[12,8]}
    disk=Point(0,0).buffer(110,quad_segs=256)
    oldap=rr(116.35,151.1,58.175);base=disk.difference(oldap)
    def add_tabs(obj,z,height,fillet=False):
        for k,s in slots.items():
            p=np.array(s['center_mm']);sign=np.sign(p[0]);inside=p-[sign*2,0];root=np.array([sign*67,p[1]])
            obj=obj.union(cq.Workplane('XY',origin=(0,0,z)).center(*(root+inside)/2).slot2D(abs(root[0]-inside[0])+16,16).extrude(height))
        if fillet:obj=obj.edges('|Z').fillet(1.5)
        for s in slots.values():
            obj=obj.cut(cq.Workplane('XY',origin=(0,0,z-1)).center(*s['center_mm']).slot2D(12,8).extrude(height+2))
        return obj.clean()
    def export(obj,name):
        assert obj.val().isValid() and len(obj.val().Solids())==1
        paths={}
        for ext in ['step','stl']:
            p=OUT/(name+'.'+ext);cq.exporters.export(obj,str(p),tolerance=.015,angularTolerance=.04);paths[ext]=str(p.relative_to(ROOT))
        rb=cq.importers.importStep(str(ROOT/paths['step'])).val();mesh=trimesh.load(ROOT/paths['stl'],force='mesh')
        assert rb.isValid() and len(rb.Solids())==1 and mesh.is_watertight and len(mesh.split())==1
        delta=abs(rb.Volume()-obj.val().Volume());assert delta<.02
        return {'name':name,'files':paths,'valid_solid_count':1,'stl_watertight':True,'bounds_mm':mesh.bounds.tolist(),'volume_mm3':rb.Volume(),'STEP_volume_roundtrip_delta_mm3':delta}
    parts=[];plate_profiles={};added_profiles={}
    for stock in cfg['plate']['stock_mm']:
        nd=copy.deepcopy(read('canon/fit_trial_design.json'));nd['main'].update(cfg['plate'])
        obj=add_tabs(make_main(nd,stock),0,stock,True)
        p=export(obj,f'TR03_MAIN_220_T{round(stock*1000):04d}_SLOT12x8_STUDY_NOT_RELEASED')
        pp=top_profile(ROOT/p['files']['stl']);plate_profiles[str(stock)]=pp
        p['top_contour_count']=len(pp.interiors)+1;assert len(pp.interiors)==3
        p['original_ring_material_removed_mm3']=make_main(read('canon/fit_trial_design.json'),stock).cut(obj).val().Volume()
        assert p['original_ring_material_removed_mm3']<1e-6
        added_solid=obj.cut(make_main(read('canon/fit_trial_design.json'),stock))
        added_path=BUILD/f'actual_added_material_{stock}.stl'
        cq.exporters.export(added_solid,str(added_path),tolerance=.015,angularTolerance=.04)
        added_profiles[str(stock)]=top_profile(added_path)
        parts.append(p)
    form=cfg['form'];forms=[];reliefs=[]
    for x0,y0,x1,y1 in form['rear_relief_boxes_xy_mm']:
        reliefs.append(translate(rr(x1-x0,y1-y0,2),xoff=(x0+x1)/2,yoff=(y0+y1)/2))
    relief_union=unary_union(reliefs)
    for var in form['variants']:
        dep=var['max_depth_mm'];draft=dep*math.tan(math.radians(1));z=.05;w,h=118.35,145.1
        outer=cq.Solid.makeLoft([cap(w-2*draft,h-2*draft,z-dep).val(),cap(w,h,z).val()])
        inner=cq.Solid.makeLoft([cap(w-4-2*draft,h-4-2*draft,z-dep-.02).val(),cap(w-4,h-4,z+.02).val()])
        collar=cq.Workplane('XY').newObject([outer.cut(inner)])
        if var['rear_reliefs']:
            for x0,y0,x1,y1 in form['rear_relief_boxes_xy_mm']:
                cutter=cq.Workplane('XY',origin=((x0+x1)/2,(y0+y1)/2,z-dep-1)).rect(x1-x0,y1-y0).extrude(dep-12+1)
                cutter=cutter.edges('|Z').fillet(2)
                collar=collar.cut(cutter)
        panel=cq.Workplane('XY',origin=(0,0,z)).circle(120).extrude(12).cut(cap(w-4,h-4,z-1).extrude(14))
        tool=add_tabs(panel.union(collar),9.05,3)
        p=export(tool,'RF02_'+var['id']+'_TABBED_REMOVABLE_FORM_STUDY_NOT_RELEASED')
        p.update(var);forms.append(p)
    # Whole source, local scope, retained even when the nut hypothesis is used.
    alltri=v[f];mn,mx=alltri.min(1),alltri.max(1)
    local=alltri[(mx[:,0]>-125)&(mn[:,0]<125)&(mx[:,1]>-125)&(mn[:,1]<125)]
    nutmask=np.zeros(len(local),dtype=bool);visible=[]
    footprints=read('build/FT02/tab_refinement/footprints.json')
    probe=read('build/FT02/tab_refinement/probe.json')
    for k,p in centers.items():
        mask=np.all(np.linalg.norm(local[:,:,:2]-p,axis=2)<11,axis=1)
        nutmask|=mask
        visible.extend(slice_project(local[mask],0,probe['rods'][k]['shaft_only_z_mm'][1]))
    bare=unary_union(slice_project(local[~nutmask],0,80)+visible+[shape(footprints[k]['envelope']) for k in ['A','B']])
    full=unary_union(slice_project(local,0,80))
    tests=[];pp=plate_profiles['1.52'];added=added_profiles['1.52']
    for label,surf in [('with_captured_nuts',full),('nuts_removed_conditional_5mm_rod_envelope',bare)]:
        hit=added.intersection(surf)
        tests.append({'case':label,'added_plate_material_overlap_mm2':hit.area,'bounds_mm':list(hit.bounds) if not hit.is_empty else []})
    for z in [0,1]:
        surf=unary_union(slice_project(local,z,z+1.52));hit=added.intersection(surf)
        tests.append({'case':f'seated_z_{z}','added_plate_material_overlap_mm2':hit.area})
    # Front form tabs only: thick panel seating is a separate unresolved issue.
    form_open=rr(114.35,141.1,57.175);tabprofile=Point(0,0).buffer(120,quad_segs=256).difference(form_open)
    for k,s in slots.items():
        p=np.array(s['center_mm']);side=np.sign(p[0]);inside=p-[side*2,0];root=[side*67,p[1]]
        tabprofile=tabprofile.union(LineString([root,inside]).buffer(8,quad_segs=96)).difference(slot_shape(p,12,8))
    form_added=tabprofile.intersection(form_open)
    tabtests=[]
    for label,surf in [('seated_front_tabs',unary_union(slice_project(local,9.05,12.05))),('nut_removed_forward_path',bare)]:
        tabtests.append({'case':label,'added_tab_overlap_mm2':form_added.intersection(surf).area})
    # Conservative full depth envelope minus explicit rear clearance windows.
    collar_checks=[]
    for var in form['variants']:
        dep=var['max_depth_mm'];dr=dep*math.tan(math.radians(1))
        ann=rr(118.35,145.1,59.175).difference(rr(114.35-2*dr,141.1-2*dr,57.175-dr))
        if not var['rear_reliefs']:
            coll_hit=ann.intersection(unary_union(slice_project(local,.05-dep,80)))
        else:
            dr12=12*math.tan(math.radians(1))
            front_ann=rr(118.35,145.1,59.175).difference(rr(114.35-2*dr12,141.1-2*dr12,57.175-dr12))
            front_hit=front_ann.intersection(unary_union(slice_project(local,-11.95,80)))
            rear_hit=ann.difference(relief_union).intersection(unary_union(slice_project(local,.05-dep,80)))
            coll_hit=front_hit.union(rear_hit)
        collar_checks.append({'variant':var['id'],'conservative_insertion_withdrawal_overlap_mm2':coll_hit.area,'continuous_collar_depth_mm':12})
    # Gasket/handle footprints remain nominal proxies, never physical fit claims.
    d=read('canon/fit_trial_design.json');foam=d['foam'];fo=rr(130.35,165.1,40);fi=rr(118.35,153.1,34)
    band=translate(fo.difference(fi),yoff=previous['inner_pose']['translation_mm'][1])
    controls=[]
    for label,y,dia in [('upper',40.09,48.46),('lower',-39.95,50)]:
        g=Point(0,y).buffer(dia/2,quad_segs=128);controls.append({'control':label,'proxy_diameter_mm':dia,'material_overlap_mm2':pp.intersection(g).area,'clearance_mm':pp.distance(g)})
    slot_checks={}
    for k,s in slots.items():
        hole=slot_shape(s['center_mm'],12,8);vals={}
        for key,raw in footprints[k].items():
            g=shape(raw);vals[key]={'outside_slot_mm2':g.difference(hole).area,'minimum_clearance_mm':hole.boundary.distance(g) if hole.covers(g) else 0}
        slot_checks[k]=vals
    sources=['canon/tab_refinement_study.json','canon/measurements.json','canon/fit_trial_design.json','canon/repair_form_design.json','data/derived/registration.json','deliverables/current/fabrication/FT02/tab-rethink/analysis.json','docs/physical_checks/removable_trim_nut_2026-10-17.json','src/analysis/tab_refinement.py']
    report={'revision':'TR03 / RF02','status':cfg['status'],'config':cfg,'parts':parts,'forms':forms,'slots':slots,'slot_checks':slot_checks,
            'plate_capture_checks':tests,'form_tab_checks':tabtests,'collar_checks':collar_checks,
            'nominal_foam_support':{'entire_band_area_mm2':band.area,'supported_area_mm2':pp.intersection(band).area,'minimum_extra_reserve_mm':disk.difference(pp).distance(band),'corner_radius_assumed_mm':40},
            'factory_opening_proxies':controls,'scan_comparison':previous['scan_comparison'],
            'scan_comparison_method':'Read existing TR02 diagnostic: both scaled to caliper U-L 80 mm; not independent validation. Original retained transforms unchanged.',
            'rejected_uniform_deeper_collars':read('build/FT02/tab_refinement/deeper.json'),
            'limits':['Captured surfaces and working registration, not physical error bounds.','Nut-removed envelope through hidden region is inferred, not scanned bare hardware.','Factory opening footprints are not measured rear handle/hub geometry.','Full form-face seating, repair substrate, brace strength and actual release remain unverified.','D24_RELIEVED has rear clearance windows and only 12 mm continuous molding wall. No full-depth fill or permanent-liner approval.','No bend is required or included; do not bend acrylic or use metal deformation as an unplanned fit remedy.','No field checks, vendor submission, purchase or permanent installation completed.'],
            'sources_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}}
    (BUILD/'build_diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
    for r in tests:
        if r['case']!='with_captured_nuts':assert r['added_plate_material_overlap_mm2']<1e-5,r
    assert all(c['added_tab_overlap_mm2']<1e-5 for c in tabtests)
    assert all(c['conservative_insertion_withdrawal_overlap_mm2']<1e-5 for c in collar_checks)
    (OUT/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'plate':tests,'form_tabs':tabtests,'collars':collar_checks,'foam':report['nominal_foam_support'],'controls':controls},indent=2))

if __name__=='__main__':
    (build if '--build' in sys.argv else deeper if '--deeper' in sys.argv else probe)()
