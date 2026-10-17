"""Bounded R006/FT02 layout and local full-capture interference study.

No source mesh is moved. Registration is a separately recorded working hypothesis.
Low triangles and opening-boundary triangles are included, unlike FT01's test.
"""
from pathlib import Path
import sys,json,math,hashlib,os
import numpy as np
from shapely.geometry import Point,Polygon,LineString,box
from shapely.ops import unary_union
from shapely.affinity import affine_transform,translate
import shapely
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'build/FT02/mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch,Circle
from src.analysis.registration_trial import rigid,coeff
from src.fabrication.fit_trial import rr
OUT=ROOT/'deliverables/current/fabrication/FT02/engineering'

def read(path):return json.loads((ROOT/path).read_text())
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

def load_capture():
    cache=ROOT/'build/FT02';cache.mkdir(parents=True,exist_ok=True)
    # Cache identity tied to original extracted bytes and unchanged transform.
    src='data/extracted/shower-hole-valve-polycam/10_14_2026.obj'
    reg=read('data/derived/registration.json');fingerprint=sha(src)+sha('data/derived/registration.json')
    if not (cache/'capture.sha').exists() or (cache/'capture.sha').read_text()!=fingerprint:
        v=np.load(ROOT/'data/derived/shower-hole-valve-polycam-vertices.npy')
        T=np.array(reg['raw_to_installed_mm']);v=v@T[:3,:3].T+T[:3,3]
        faces=[]
        with (ROOT/src).open() as f:
            for line in f:
                if line.startswith('f '):
                    p=[int(x.split('/')[0])-1 for x in line.split()[1:]]
                    for j in range(1,len(p)-1):faces.append([p[0],p[j],p[j+1]])
        f=np.asarray(faces,dtype=np.int32)
        assert f.min()>=0 and f.max()<len(v)
        np.save(cache/'primary_vertices_mm.npy',v);np.save(cache/'primary_faces.npy',f)
        (cache/'capture.sha').write_text(fingerprint)
    return np.load(cache/'primary_vertices_mm.npy'),np.load(cache/'primary_faces.npy')

def clip_z(points,z,above):
    out=[]
    for i,p in enumerate(points):
        q=points[(i+1)%len(points)]
        a=(p[2]>=z) if above else (p[2]<=z);b=(q[2]>=z) if above else (q[2]<=z)
        if a:out.append(p)
        if a!=b:out.append(p+(q-p)*((z-p[2])/(q[2]-p[2])))
    return out

def slice_project(tris,lo,hi):
    mask=(tris[:,:,2].max(1)>=lo)&(tris[:,:,2].min(1)<=hi)
    polys=[]
    for tri in tris[mask]:
        p=clip_z(list(tri),lo,True)
        if len(p)<3:continue
        p=clip_z(p,hi,False)
        if len(p)<3:continue
        q=Polygon(np.array(p)[:,:2])
        if not q.is_valid:q=q.buffer(0)
        if not q.is_empty and q.area>1e-10:polys.append(q)
    return polys

def tab_shapes(centers,width=15,hole=7.0,slot_length=10.0):
    a,b=[np.array(centers[x]) for x in ('A','B')];u=(a-b)/np.linalg.norm(a-b)
    shapes=[]
    for name,p in [('A',a),('B',b)]:
        # Join to the side of the parent plate; round ends/transitions.
        root=np.array([math.copysign(67,p[0]),p[1]])
        raw=LineString([p,root]).buffer(width/2,quad_segs=64)
        cut=Point(p).buffer(hole/2,quad_segs=64) if name=='A' else LineString([p-u*(slot_length-hole)/2,p+u*(slot_length-hole)/2]).buffer(hole/2,quad_segs=64)
        shapes.append((raw,cut))
    return shapes

def draw_geom(ax,g,**kw):
    if g.is_empty:return
    for p in getattr(g,'geoms',[g]):
        if p.geom_type=='Polygon':ax.add_patch(Patch(np.array(p.exterior.coords),**kw))

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    measurements=read('canon/measurements.json');layout=measurements['active_locating_layout']
    assert measurements['revision']=='R006'
    baseline=read('canon/fit_trial_design.json');m=baseline['main'];resolved=read('data/derived/resolved.json')
    # Equal cover bores are a photo/manufacturer-informed working hypothesis,
    # not a newly accepted lower-bore measurement.
    accepted={r['id']:r['value_mm'] for r in measurements['measurements'] if r['status']=='user-confirmed'}
    cover_d=accepted['M06-OD'];ud=accepted['M12-UD'];ld=ud
    lower_y=-cover_d/2+accepted['M06-YN']+ld/2
    upper_y=lower_y+accepted['M12-G']+(ud+ld)/2
    inner_upper_y=accepted['M02-H']/2-accepted['M11-UC']
    itc=np.array([0,upper_y-inner_upper_y])
    centers={k:(np.array(p)+itc).tolist() for k,p in layout['outline_centered_xy_up_mm'].items()}
    source_alignment=read('deliverables/current/fabrication/control-registration/registration_trial.json')
    targets=np.array(source_alignment['cases'][0]['control_cap_targets_xy_mm'])
    reference=np.array([[0,lower_y],[0,upper_y]])
    Q,t=rigid(reference,targets)
    transform={'inner_outline_to_cover_xy_up':{'row_rotation':np.eye(2).tolist(),'translation_mm':itc.tolist()},
       'cover_to_installed_xy_up':{'row_rotation':Q.tolist(),'translation_mm':t.tolist(),'determinant':float(np.linalg.det(Q))},
       'cover_opening_working_centers_mm':reference.tolist(),
       'fit_residual_mm':np.linalg.norm(reference@Q+t-targets,axis=1).tolist(),
       'basis':'Rigid fit to prior diagnostic control-cap picks, source scan unchanged; loose cover edge dimensions with equal lower bore and horizontally centered openings as working assumptions. Inner upper opening registers to upper cover opening. No physical concentricity or final pose claimed.',
       'front_view':'A upper-right, B lower-left; no reflection',
       'mounting_centers_in_cover_frame_mm':centers}
    ap=rr(m['aperture_width_mm'],m['aperture_height_mm'],m['aperture_radius_mm'])
    circle=Point(0,0).buffer(m['outer_diameter_mm']/2,quad_segs=256);plain=circle.difference(ap)
    tabsets={name:tab_shapes(centers,15,di,di+3) for name,di in [('tight',6.4),('balanced',7.0),('generous',8.0)]}
    shapes={'PLAIN':plain}
    for name,tabs in tabsets.items():
        p=plain
        for raw,cut in tabs:p=p.union(raw).difference(cut)
        # Round inward junction roots without touching the already rounded bores.
        p=p.buffer(1.5,quad_segs=32).buffer(-1.5,quad_segs=32)
        shapes[name]=p
    v,f=load_capture();tris=v[f]
    mn=tris.min(1);mx=tris.max(1)
    mask=(mx[:,0]>-120)&(mn[:,0]<125)&(mx[:,1]>-80)&(mn[:,1]<155)
    tris=tris[mask]
    opening=Polygon(next(x['contour_mm'] for x in resolved['features'] if x['id']=='OPEN-MAIN'))
    slice_cases=[('sweep_from_wall',0,80),('sweep_1mm_bedding',1,80),('seated_wall',0,1.524),('seated_1mm_bedding',1,2.524),('seated_2mm_bedding',2,3.524)]
    checks=[];draw=[]
    for name,lo,hi in slice_cases:
        pieces=slice_project(tris,lo,hi)
        full=unary_union(pieces)
        hardware=full.intersection(opening)  # no 3 mm erosion
        border=full.difference(opening)
        entry={'case':name,'z_interval_mm':[lo,hi],'clipped_triangles':len(pieces),'parts':{}}
        for kind,p in shapes.items():
            placed=affine_transform(p,coeff(Q,t));inside=placed.intersection(hardware);outside=placed.intersection(border)
            added=placed.difference(affine_transform(plain,coeff(Q,t)))
            conflict=added.intersection(full)
            entry['parts'][kind]={'opening_surface_overlap_mm2':inside.area,'outside_opening_contact_mm2':outside.area,
                'added_tab_overlap_mm2':conflict.area,'added_tab_conflict_bounds_mm':list(conflict.bounds) if not conflict.is_empty else [],
                'overlap_interpretation':'Captured-surface projection in stated Z range; outside opening may be intended stone support/stand-off contact. Not a solid or hidden-geometry proof.'}
        if name in ['sweep_1mm_bedding','seated_1mm_bedding']:
            inv=Q.T;draw.append((name,affine_transform(full,coeff(inv,-t@inv))))
        checks.append(entry)
    # Full damage contours, not just a single worst trace.
    coverage=[]
    for feature in resolved['features']:
        if feature.get('include_in_coverage') and feature.get('contour_mm'):
            points=np.asarray(feature['contour_mm']);coverage.append({'feature':feature['id'],'visual_outer_margin_mm':float(m['outer_diameter_mm']/2-np.linalg.norm(points-t,axis=1).max()),'meaning':'Projected trace margin, not verified sound support'})
    div=np.array(resolved['diverter_tip_mm'][:2]);gap=float(np.linalg.norm(div-t)-(m['outer_diameter_mm']+baseline['diverter']['outer_diameter_mm'])/2)
    comparison=[]
    for label,point in centers.items():
        comparison.append({'hole':label,'center_mm':point,'inside_plain_aperture':ap.contains(Point(point)),
            'center_to_boundary_mm':ap.boundary.distance(Point(point)),
            'factory_bore_entirely_in_opening':ap.covers(Point(point).buffer(layout['diameters_mm'][label]/2))})
    report={'study':'FT02 locator evaluation','measurement_revision':'R006','transforms':transform,'layout':layout,
      'candidate_geometry':{'round_at':'A','slot_at':'B','slot_axis_unit_B_to_A':((np.array(centers['A'])-centers['B'])/layout['center_distance_mm']).tolist(),
        'tab_width_mm':15,'root_radius_mm':1.5,'candidates':{'tight':{'diameter_width_mm':6.4,'slot_length_mm':9.4},'balanced':{'diameter_width_mm':7,'slot_length_mm':10},'generous':{'diameter_width_mm':8,'slot_length_mm':11}}},
      'plain_hole_locations':comparison,'full_capture_checks':checks,'coverage':coverage,'pair_gap_nominal_mm':gap,
      'sources_sha256':{p:sha(p) for p in ['canon/measurements.json','data/derived/registration.json','data/derived/resolved.json','deliverables/current/fabrication/control-registration/registration_trial.json','data/extracted/shower-hole-valve-polycam/10_14_2026.obj','src/analysis/fit_trial_release.py']},
      'decision':'PENDING interpretation of actual conflict views; nothing released',
      'limits':['Capture surface only; unobserved back surfaces not reconstructed','Z=0 nominal tile plane; stone topography retained','XY working registration is not measured final cover pose','Present rods not virtually shortened; changes require a distinct physical state','Opening boundary not eroded; low surfaces included from Z=0']}
    (OUT/'locator_evaluation.json').write_text(json.dumps(report,indent=2)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(12,7))
    for ax,(name,captured) in zip(axes,draw):
        draw_geom(ax,plain,facecolor='#d5e7eb',edgecolor='#1d5260')
        draw_geom(ax,ap,facecolor='white',edgecolor='#1d5260')
        for raw,cut in tabsets['balanced']:
            draw_geom(ax,raw.intersection(ap).difference(cut),facecolor='#e5bc72',edgecolor='#9e6b28')
            draw_geom(ax,cut,facecolor='white',edgecolor='#4f5559')
        conflict=shapes['balanced'].difference(plain).intersection(captured)
        draw_geom(ax,conflict,facecolor='#be3433',edgecolor='none')
        for k,p in centers.items():ax.plot(*p,'k+');ax.annotate(k,p,xytext=(7,8),textcoords='offset points')
        ax.set_title(name.replace('_',' '));ax.set_aspect('equal');ax.set(xlim=(-80,80),ylim=(-90,90),xlabel='Cover-local X (mm)',ylabel='Cover-local Y (mm)');ax.grid(alpha=.15)
    fig.suptitle('R006 measured layout: new rounded tabs, round hole A / aligned slot B')
    fig.text(.5,.025,'Amber: added tab metal. Red: full captured-surface interference in the stated depth range.\nIncludes low hardware and opening boundary; source mesh remains unchanged. Working registration, not proven physical fit.',ha='center',fontsize=10)
    fig.tight_layout(rect=[0,.08,1,.95]);fig.savefig(OUT/'locator_evaluation.png',dpi=160);plt.close(fig)
    print(json.dumps({'transform':transform,'hole_geometry':comparison,'checks':checks,'coverage_min':min(x['visual_outer_margin_mm'] for x in coverage),'gap':gap},indent=2))

if __name__=='__main__':run()
