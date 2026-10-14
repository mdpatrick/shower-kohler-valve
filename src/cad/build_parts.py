"""Authoritative provisional solids. These are NOT approved manufacturing dimensions."""
from pathlib import Path
import json,math,numpy as np
import cadquery as cq
import ezdxf
ROOT=Path(__file__).resolve().parents[2]

def capsule(w,h,z):
    return cq.Workplane('XY').slot2D(h,w,90).extrude(z)

def rounded_rect(w,h,r,z):
    return cq.Workplane('XY').rect(w,h).extrude(z).edges('|Z').fillet(r)

def build():
    d=json.loads((ROOT/'data/derived/resolved.json').read_text());a=d['assumptions'];c=d['candidate'];center=np.array(d['trim_center_mm']);ic=np.array(d['inner_center_mm'])
    OUT=ROOT/'deliverables/current/cad';OUT.mkdir(parents=True,exist_ok=True)
    cache=ROOT/'data/derived/cad';cache.mkdir(parents=True,exist_ok=True)
    parts={};meta=[];checks=[];assembly=cq.Assembly(name='DRAFT_NOT_FOR_FABRICATION_'+d['revision'])
    def add(id,solid,xyz,color,collection,evidence,export=False):
        shape=solid.val() if isinstance(solid,cq.Workplane) else solid
        if not shape.isValid():raise ValueError('Invalid solid '+id)
        parts[id]=shape
        bb=shape.BoundingBox();stl=cache/f'{id}.stl'
        cq.exporters.export(shape,str(stl),tolerance=.04,angularTolerance=.08)
        step=None
        if export:
            step=OUT/f'{id}_DRAFT_NOT_FOR_FABRICATION.step';cq.exporters.export(shape,str(step))
            re=cq.importers.importStep(str(step));rb=re.val().BoundingBox()
            assert re.val().isValid() and len(re.solids().vals())==len(shape.Solids())
            assert all(abs(x-y)<1e-5 for x,y in zip([bb.xlen,bb.ylen,bb.zlen],[rb.xlen,rb.ylen,rb.zlen]))
            assert abs(re.val().Volume()-shape.Volume())<max(1e-5,shape.Volume()*1e-8)
            checks.append({'id':id,'status':'PASS','check':'STEP reimport validity, solid count, bounds and volume','physical_fit':'UNRESOLVED'})
        assembly.add(shape,name=id,loc=cq.Location(cq.Vector(*xyz)),color=cq.Color(*color))
        factory_xyz=None if id in ('CUSTOM-01','NEW-SEAL-PATH') else list(map(float,xyz))
        if factory_xyz and collection in ('02_INNER_AND_GASKET','03_OUTER_TRIM'):
            factory_xyz[2]-=newwall
        meta.append({'id':id,'stl':str(stl.relative_to(ROOT)),'step':str(step.relative_to(ROOT)) if step else None,
            'factory_location_mm':factory_xyz,
            'location_mm':list(map(float,xyz)),'color':color,'collection':collection,'evidence':evidence,
            'status':'provisional reference' if id!='CUSTOM-01' else 'unselected candidate',
            'bounds_local_mm':[[bb.xmin,bb.ymin,bb.zmin],[bb.xmax,bb.ymax,bb.zmax]],'volume_mm3':shape.Volume(),
            'tessellation_tolerance_mm':.04,'angular_tolerance_radians':.08})
    # The cutting contours are derived from this exact custom solid's top face.
    ap_center=np.array(c['aperture_center_mm'])-center
    plate=cq.Workplane('XY').circle(c['diameter_mm']/2).extrude(c['thickness_mm'])
    aperture=rounded_rect(c['aperture_width_mm'],c['aperture_height_mm'],c['aperture_radius_mm'],c['thickness_mm']+2).translate((float(ap_center[0]),float(ap_center[1]),-1))
    plate=plate.cut(aperture)
    base=c['seal_display_thickness_mm'];newwall=base+c['thickness_mm'];gasketz=newwall
    add('CUSTOM-01',plate,(*center,base),(.18,.52,.64),'04_CUSTOM_CANDIDATE','Computed draft profile / material and thickness unapproved',True)
    gw=a.get('gasket_outer_width_mm',a['inner_width_mm']);gh=a.get('gasket_outer_height_mm',a['inner_height_mm'])
    gasket=capsule(gw,gh,a['gasket_free_thickness_mm']).cut(capsule(gw-2*a['gasket_width_mm'],gh-2*a['gasket_width_mm'],a['gasket_free_thickness_mm']+2).translate((0,0,-1)))
    add('GASKET-01',gasket,(*ic,gasketz),(.64,.22,.45),'02_INNER_AND_GASKET','Contact path topology provisional; use accepted dimensions where available')
    inner=capsule(a['inner_width_mm'],a['inner_height_mm'],a['inner_sheet_thickness_mm'])
    # Raised peripheral flange is a visible, separately disclosed formed-depth placeholder.
    lip=capsule(a['inner_width_mm']-6,a['inner_height_mm']-6,a['inner_formed_depth_mm']).cut(capsule(a['inner_width_mm']-12,a['inner_height_mm']-12,a['inner_formed_depth_mm']+2).translate((0,0,-1)))
    inner=inner.union(lip)
    for i,point in enumerate(d['controls_mm']):
        x,y=np.array(point[:2])-ic
        bore=32 if i==0 else 20
        inner=inner.cut(cq.Workplane('XY').center(float(x),float(y)).circle(bore).extrude(50).translate((0,0,-1)))
        # Open rear recess to front hub transition is not inferable from the scans.
        ring=cq.Workplane('XY').center(float(x),float(y)).circle(bore+3).circle(bore).extrude(a.get('hub_projection_envelope_mm',a['inner_formed_depth_mm']+3))
        inner=inner.union(ring)
    for slot in d['inner_slots']:
        x,y=np.array(slot['center_mm'])-ic;sw=slot['width_mm'];sh=slot['height_mm']
        wp=cq.Workplane('XY').center(float(x),float(y))
        hole=(wp.circle(sw/2) if abs(sw-sh)<1e-6 else wp.slot2D(max(sw,sh),min(sw,sh),90 if sh>sw else 0)).extrude(100).translate((0,0,-1))
        inner=inner.cut(hole)
    innerz=gasketz+a['gasket_free_thickness_mm']
    add('PLATE-INNER',inner,(*ic,innerz),(.9,.55,.16),'02_INNER_AND_GASKET','Factory guide form + current evidence; unconfirmed surfaces remain assumed',True)
    if a.get('rear_projection_envelope_mm',0)>0:
        envelope=capsule(a['inner_width_mm']-10,a['inner_height_mm']-10,a['rear_projection_envelope_mm'])
        add('REAR-PROJECTION-ENVELOPE',envelope,(*ic,innerz-a['rear_projection_envelope_mm']),(.85,.2,.5),'01_OBSERVED_ENVELOPES','Maximum measured rear extent envelope ONLY; not a solid physical plate')
    # Nominal exterior form sampled from official OBJ radial profile (inch->mm).
    # Rear shell is assumed; BIM exterior cannot establish cavity or mating dimensions.
    radius=d['nominal']['trim_diameter_mm']/2;t=a['outer_shell_thickness_mm'];front=a['outer_cavity_depth_mm']+t
    meridian=[(0,front),(60,front),(71,13),(radius-2,13),(radius,11),(radius,0),(radius-t,0),(radius-t,10),(radius-3,11.5),(71,11.5),(60,front-t),(0,front-t)]
    outer=cq.Workplane('XZ').polyline(meridian).close().revolve(360,(0,0),(0,1))
    for point in d['controls_mm']:
        x,y=np.array(point[:2])-center
        outer=outer.cut(cq.Workplane('XY').center(float(x),float(y)).circle(18).extrude(40).translate((0,0,-2)))
    outer=outer.cut(cq.Workplane('XY').box(a['drain_width_mm'],8,a['drain_height_mm'],centered=(True,True,False)).translate((0,-radius+2,0)))
    add('TRIM-OUTER',outer,(*center,newwall),(.63,.67,.68),'03_OUTER_TRIM','User identified K-T14489-4-BN; nominal exterior; cavity/shell/drain detail assumed',True)
    # Service/hardware envelopes retain measured tip positions. Their hidden axes remain unknown.
    for i,point in enumerate(d['controls_mm']):
        x,y,z=point
        bodyr=30 if i==0 else 18
        envelope=cq.Workplane('XY').circle(bodyr).extrude(z-12+25).translate((0,0,-25)).union(cq.Workplane('XY').circle(6).extrude(12).translate((0,0,z-12)))
        add('VALVE-LOWER' if i==0 else 'VALVE-UPPER',envelope,(x,y,0),(.46,.34,.15),'01_OBSERVED_ENVELOPES','Visible collar/tip envelope; normal-axis approximation, not hidden valve reconstruction')
        # Nominal display handle, not fit authority. Length from dimensioned manufacturer drawing.
        handle=cq.Workplane('XY').circle(21).circle(16).extrude(58)
        handle=handle.union(cq.Workplane('XY').circle(12).extrude(16).translate((0,0,58)))
        long=d['nominal']['handle_lever_long_reach_mm'];short=a['main_lever_short_reach_mm']
        sign=-1 if i==0 else 1
        lever=cq.Workplane('XY').box(a['lever_width_mm'],long+short,a['lever_depth_mm']).translate((0,sign*(long-short)/2,76))
        handle=handle.union(lever)
        add('HANDLE-LOWER' if i==0 else 'HANDLE-UPPER',handle,(x,y,newwall+27.95),(.48,.51,.52),'03_OUTER_TRIM','Nominal 3in long reach; short reach/cross-section/housing assumed. Reference direction only; engagement/travel require dry fit')
    # Separate lower diverter stays at the original wall plane in both display states.
    dx,dy,dz=d['diverter_tip_mm'];dn=d['nominal']['diverter_trim'];dr=dn['diameter_mm']/2
    dt=a['diverter_trim_shell_mm'];dd=a['diverter_trim_body_depth_mm'];bore=a['diverter_trim_opening_diameter_mm']/2
    small=cq.Workplane('XY').circle(dr).extrude(dd)
    small=small.cut(cq.Workplane('XY').circle(dr-dt).extrude(dd-dt+1).translate((0,0,-1)))
    small=small.cut(cq.Workplane('XY').circle(bore).extrude(dd+2).translate((0,0,-1)))
    add('DIVERTER-TRIM',small,(dx,dy,0),(.68,.55,.28),'03B_DIVERTER_REFERENCE','K-T14491-4 nominal OD only; simplified rear cavity/shell/bore assumed; center from captured tip')
    smallhandle=cq.Workplane('XY').circle(21).circle(16).extrude(58)
    smallhandle=smallhandle.union(cq.Workplane('XY').circle(12).extrude(16).translate((0,0,58)))
    smallhandle=smallhandle.union(cq.Workplane('XY').box(a['lever_width_mm'],dn['lever_long_reach_mm']+dn['lever_short_reach_mm'],a['lever_depth_mm']).translate((0,(dn['lever_short_reach_mm']-dn['lever_long_reach_mm'])/2,76)))
    add('DIVERTER-HANDLE',smallhandle,(dx,dy,dn['total_projection_mm']-80),(.68,.55,.28),'03B_DIVERTER_REFERENCE','Documented lever reaches/projection; cross-section/housing/engagement assumed; shown down, travel unverified')
    for id,point in zip(['STUD-SW','STUD-NE'],d['studs_mm']):
        x,y,z=point
        stud=cq.Workplane('XY').circle(a['stud_envelope_diameter_mm']/2).extrude(z+15).translate((0,0,-15))
        add(id,stud,(x,y,0),(.65,.55,.23),'01_OBSERVED_ENVELOPES','Observed tip; envelope axis, diameter and hidden engagement unverified')
        nut=cq.Workplane('XY').polygon(6,10).circle(a['stud_envelope_diameter_mm']/2).extrude(4)
        add(id+'-NUT',nut,(x,y,innerz+a['inner_sheet_thickness_mm']),(.48,.48,.5),'02_INNER_AND_GASKET','Assumed nut envelope; seating unknown')
    # New sealing interface is only a diagnostic band; it is NOT a sealant specification.
    ring=cq.Workplane('XY').circle(c['diameter_mm']/2-3).circle(c['diameter_mm']/2-9).extrude(base)
    add('NEW-SEAL-PATH',ring,(*center,0),(.27,.58,.35),'05_PROPOSED_MATERIALS','Illustrative location; thickness/chemistry/adhesion/continuity unverified')
    astep=OUT/'assembly_DRAFT_NOT_FOR_FABRICATION.step';assembly.export(str(astep),mode='default')
    imported=cq.importers.importStep(str(astep));assert imported.val().isValid()
    expected=sum(len(p.Solids()) for p in parts.values());assert len(imported.solids().vals())==expected
    checks.append({'id':'ASSEMBLY','status':'PASS','check':'non-fused STEP solid count','expected':expected,'actual':len(imported.solids().vals())})
    dxf=OUT/'CUSTOM-01_DRAFT_NOT_FOR_FABRICATION.dxf'
    # Top-face wires, translated to Z=0, retain exact circles/arcs and no annotations.
    top=plate.faces('>Z').wires().translate((0,0,-c['thickness_mm']))
    cq.exporters.export(top,str(dxf),exportType='DXF')
    doc=ezdxf.readfile(dxf);doc.units=ezdxf.units.MM;doc.saveas(dxf)
    entities=list(doc.modelspace());assert all(e.dxftype() in ('LINE','ARC','CIRCLE','LWPOLYLINE','SPLINE','POLYLINE') for e in entities)
    dp=cq.importers.importDXF(str(dxf)).wires().toPending().extrude(c['thickness_mm'])
    assert dp.val().isValid() and abs(dp.val().Volume()-plate.val().Volume())<.01
    assert len(plate.faces('>Z').wires().vals())==2
    checks.append({'id':'DXF','status':'PASS','units':'mm','contours':2,'internal_apertures':1,'separate_fastener_holes':0,'entity_types':sorted(set(e.dxftype() for e in entities)),'reimport_volume_agrees':True})
    manifest={'revision':d['revision'],'status':'DRAFT_NOT_FOR_FABRICATION','units':'mm','parts':meta,'checks':checks,
       'warnings':['Reference solids are not replacement Kohler parts.','Hidden cavity, gasket, slots and engagement unknown.','No physical fit or material approval.'],
       'assembly_state':'proposed_provisional','wall':'irregular mesh accompanies STEP in Blender/GLB; not converted to faceted STEP'}
    (cache/'parts.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'cad_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Generated',len(parts),'parts;',len(checks),'CAD/export checks passed; physical fit UNRESOLVED')
    return manifest

if __name__=='__main__':build()
