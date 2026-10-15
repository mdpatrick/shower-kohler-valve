"""LOC01: test a concrete locating-tab trial against preserved forward surfaces."""
from pathlib import Path
import hashlib
import json
import math
import os
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[2]/'build/cache/matplotlib'))
import numpy as np
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import nearest_points, unary_union
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'deliverables/current/fabrication/concentric-border-study'


def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


def clipped(tri, low, high=None):
    points=[p for p in tri]
    for threshold, above in [(low,True)]+([] if high is None else [(high,False)]):
        output=[]
        for p,q in zip(points,points[1:]+points[:1]):
            a=p[2]>=threshold if above else p[2]<=threshold
            b=q[2]>=threshold if above else q[2]<=threshold
            if a:output.append(p)
            if a!=b:output.append(p+(threshold-p[2])/(q[2]-p[2])*(q-p))
        points=output
        if len(points)<3:return Polygon()
    p=Polygon([(q[0],q[1]) for q in points])
    return p if p.is_valid else p.buffer(0)


def run():
    cfg=read('canon/stud_locator_study.json');g=cfg['geometry_trial'];ref=cfg['reference_state']
    report=read(ref['source']);r=read('data/derived/resolved.json');d=read('canon/fabrication_designs.json')
    for path,digest in report['inputs_sha256'].items():assert sha(path)==digest,'Stale center study: '+path
    trial=next(t for t in report['trials'] if all(t[k]==ref[k] for k in ['mode','scan_coordinate_penalty_weight','loss']))
    pts=trial['hypothetical_installed_tip_centers_mm']
    # Preserve this derived model state explicitly; it cannot replace the as-observed mesh.
    state={'id':ref['id'],'status':'HYPOTHETICAL_DERIVED_MODEL_STATE','tip_centers_installed_mm':pts,
           'source_report_sha256':sha(ref['source']),'assumptions':ref,'raw_observations':report['raw_record'],
           'trial_residuals_mm':trial['residuals_mm'],'residuals_are_not_accuracy_bounds':True}
    (OUT/'reconciled_model_state.json').write_text(json.dumps(state,indent=2)+'\n')
    ap=Polygon(d['aperture']['base_convex_polygon_installed_mm']).buffer(d['aperture']['outward_radius_mm'],quad_segs=128)
    center=np.array(r['trim_center_mm']);outer=Point(*center).buffer(g['main_outer_diameter_mm']/2,quad_segs=256)
    direction=np.array(pts['NE'][:2])-np.array(pts['SW'][:2]);direction/=np.linalg.norm(direction)
    tabs=[];holes=[];items=[]
    for key in ['NE','SW']:
        p=np.array(pts[key][:2]);root=np.array(nearest_points(Point(*p),ap.boundary)[1].coords[0]);unit=root-p;unit/=np.linalg.norm(unit)
        anchor=root+unit*g['tab_root_overlap_mm']
        tab=LineString([p,anchor]).buffer(g['tab_width_mm']/2,quad_segs=64)
        if key=='NE':hole=Point(*p).buffer(g['round_hole_diameter_mm']/2,quad_segs=128)
        else:
            half=(g['SW_slot_total_length_mm']-g['SW_slot_width_mm'])/2
            hole=LineString([p-half*direction,p+half*direction]).buffer(g['SW_slot_width_mm']/2,quad_segs=128)
        tabs.append(tab);holes.append(hole)
        items.append({'id':key,'center_installed_xy_mm':p.tolist(),'root_installed_xy_mm':anchor.tolist(),
                      'hole_kind':'round clearance' if key=='NE' else 'clearance slot along stud pair'})
    material=outer.difference(ap).union(unary_union(tabs)).difference(unary_union(holes))
    added=material.intersection(ap)
    assert material.geom_type=='Polygon' and len(material.interiors)==3
    # Use actual source triangles and its unchanged transform; clip only the relevant local regions.
    reg=read('data/derived/registration.json');T=np.array(reg['raw_to_installed_mm'])
    vertices=np.load(ROOT/'data/derived/shower-hole-valve-polycam-vertices.npy')@T[:3,:3].T+T[:3,3]
    faces=[]
    for line in (ROOT/'data/extracted/shower-hole-valve-polycam/10_14_2026.obj').open():
        if line.startswith('f '):
            ids=[int(s.split('/')[0])-1 for s in line.split()[1:]]
            faces.extend((ids[0],ids[j],ids[j+1]) for j in range(1,len(ids)-1))
    tri=vertices[np.array(faces)];b=added.bounds
    keep=(tri[:,:,0].max(1)>=b[0])&(tri[:,:,0].min(1)<=b[2])&(tri[:,:,1].max(1)>=b[1])&(tri[:,:,1].min(1)<=b[3])&(tri[:,:,2].max(1)>=0)
    tri=tri[keep]
    roi=[]
    for tr in tri:
        p=Polygon(tr[:,:2])
        if p.is_valid and p.area>1e-9 and p.intersects(added):roi.append(tr)
    def collisions(low, high=None):
        pieces=[];count=0;top=None
        for tr in roi:
            if tr[:,2].max()<low or high is not None and tr[:,2].min()>high:continue
            poly=clipped(tr,low,high)
            hit=poly.intersection(added)
            if hit.area>1e-7:
                pieces.append(hit);count+=1
                top=max(top if top is not None else -1e9,float(tr[:,2].max()))
        union=unary_union(pieces)
        return {'triangles':count,'projected_conflict_area_mm2':union.area,'bounds_mm':list(union.bounds) if not union.is_empty else None,'max_conflicting_triangle_vertex_Z_mm':top},union
    z=g['rear_plane_z_mm'];t=g['thickness_mm']
    sweep,sweep_shape=collisions(z)
    seated,seated_shape=collisions(z,z+t)
    sensitivity=[]
    for back in [0,1,2.524,6,10,14,18,22,26,30,34]:
        result,_=collisions(back,back+t);sensitivity.append({'rear_plane_z_mm':back,**result})
    # Export diagnostic CAD only. Exact circles/capsules; no released cutting DXF.
    def poly_solid(poly,depth):
        return cq.Workplane('XY').polyline([(x-center[0],y-center[1]) for x,y in poly.exterior.coords[:-1]]).close().extrude(depth)
    blank=cq.Workplane('XY').circle(g['main_outer_diameter_mm']/2).extrude(t)
    base=cq.Workplane('XY').polyline([(x-center[0],y-center[1]) for x,y in d['aperture']['base_convex_polygon_installed_mm']]).close().offset2D(d['aperture']['outward_radius_mm']).extrude(t)
    solid=blank.cut(base)
    for tab in tabs:solid=solid.union(poly_solid(tab,t))
    for hole in holes:solid=solid.cut(poly_solid(hole,t))
    shape=solid.val();assert shape.isValid() and len(shape.Solids())==1
    assert len(solid.faces('>Z').wires().vals())==4
    diag=OUT/'diagnostic';diag.mkdir(exist_ok=True)
    stem='MAIN-C1_LOC01_TAB_TRIAL_NOT_FOR_FABRICATION'
    for ext in ['step','stl']:cq.exporters.export(solid,str(diag/(stem+'.'+ext)))
    result={'study':'LOC01','status':'DIAGNOSTIC_NOT_FOR_FABRICATION','source_configuration':'canon/stud_locator_study.json',
        'source_sha256':{p:sha(p) for p in ['canon/stud_locator_study.json',ref['source'],'data/derived/registration.json','canon/measurements.json']},
        'model_state':state['id'],'parameters':g,'locators':items,'added_material_area_mm2':added.area,
        'integral_tabs_insertion_sweep':sweep,'removable_tabs_seated_plane':seated,'depth_sensitivity':sensitivity,
        'conclusion':('FLAT_TAB_TRIAL_CONFLICTS_WITH_CAPTURED_HARDWARE' if sweep['triangles'] else 'NO_CAPTURED_SWEEP_CONFLICT; physical fit still unresolved'),
        'bearing':'NOT VALIDATED: actual nut/washer seats and clamping load unknown',
        'centering':'Hole clearance and an elongated slot allow motion; actual assembled cover datum and restraint must be verified.',
        'threaded_engagement':cfg['threaded_engagement'],
        'limits':'Fitted tips projected along assumed normal axes, against unchanged captured hardware. No measured axis/cross-section/uncertainty bound. Intersections are conditional model conflicts, not proof of a physical defect. Hidden solids may add conflicts. Max Z is a triangle-vertex bound, not a precise required standoff.',
        'diagnostic_CAD':[str(diag.relative_to(OUT)/(stem+'.'+ext)) for ext in ['step','stl']],
        'source_scan_modified':False,'physical_fit':'NOT PERFORMED','manufacturing_release':'NOT GIVEN'}
    (OUT/'stud_locator_analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    fig,axs=plt.subplots(1,2,figsize=(11,6))
    def draw(ax,p,color,alpha=1):
        if p.is_empty:return
        if p.geom_type=='Polygon':
            ax.fill(*p.exterior.xy,color=color,alpha=alpha)
            for ring in p.interiors:ax.fill(*ring.xy,color='white')
        elif hasattr(p,'geoms'):
            for q in p.geoms:draw(ax,q,color,alpha)
    for ax,hit,title in [(axs[0],sweep_shape,'Integral tabs: complete insertion sweep'),(axs[1],seated_shape,'Removable tabs: seated at Z=1 to 2.524')]:
        draw(ax,material,'#dce9ec');draw(ax,added,'#e8bd78');draw(ax,hit,'#b83125')
        for key in ['NE','SW']:
            p=pts[key];ax.plot(p[0],p[1],'+',color='#192e36');ax.text(p[0]+5,p[1]+8,key,fontsize=10)
        for key in ['U','L']:
            p=pts[key];ax.plot(p[0],p[1],'o',ms=4,color='#25828c');ax.text(p[0]+5,p[1],key,fontsize=10)
        ax.set_aspect('equal');ax.set_xlim(-85,85);ax.set_ylim(-45,130);ax.set_title(title,fontsize=11);ax.set_xlabel('Installed X (mm)');ax.grid(alpha=.15)
    axs[0].set_ylabel('Installed Y (mm)')
    fig.suptitle('Upper-only locating trial - hypothetical holes / axes',fontsize=15)
    fig.text(.5,.02,'Amber: added tab metal. Red: projected captured-surface interference. Not a released mounting design.',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.10,1,.95))
    fig.savefig(OUT/'views/stud_locator_trial.png',dpi=170)
    fig.savefig(OUT/'views/stud_locator_trial.svg')
    print(json.dumps({k:result[k] for k in ['conclusion','integral_tabs_insertion_sweep','removable_tabs_seated_plane','depth_sensitivity']},indent=2),flush=True)


if __name__=='__main__':run()
