"""Preserve and inspect direct attached-plate evidence; no primary registration edits."""
from pathlib import Path
import json, sys, shutil, zipfile
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.ingest import members,cached_member_ok,sha
OUT=ROOT/'deliverables/current/fabrication/fit-trial'
CACHE=ROOT/'build/attached_scan'

def run():
    OUT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(parents=True,exist_ok=True)
    src=ROOT/'data/raw/polycam/polycam-inner-plate-attached.zip'
    root=ROOT/'data/extracted/polycam-inner-plate-attached'
    assert not root.is_symlink()
    with zipfile.ZipFile(src) as z:
        entries=members(z)
        assert shutil.disk_usage(ROOT).free>sum(e['size_bytes'] for e in entries)+100000000
        root.mkdir(parents=True,exist_ok=True)
        for e in entries:
            dest=root/e['name']
            assert not dest.is_symlink() and dest.resolve().is_relative_to(root.resolve())
            dest.parent.mkdir(parents=True,exist_ok=True)
            if not cached_member_ok(dest,e,root):
                with z.open(e['name']) as a,dest.open('wb') as b:shutil.copyfileobj(a,b)
            assert cached_member_ok(dest,e,root)
    with (root/'10_15_2026.obj').open() as f:
        v=np.array([list(map(float,l.split()[1:4])) for l in f if l.startswith('v ')])
    np.save(CACHE/'raw_vertices.npy',v)
    regions=[[425,530,530,690],[440,900,535,1000],[985,580,1040,750],[980,950,1030,1050]]
    patches=[]
    for x0,y0,x1,y1 in regions:
        a=(np.array([x0,x1])/1500-.5)*3.2;b=(.5-np.array([y1,y0])/1500)*3.2+1.52
        patches.append(v[(v[:,0]>a[0])&(v[:,0]<a[1])&(v[:,1]>b[0])&(v[:,1]<b[1])])
    allp=np.vstack(patches);p=allp.copy()
    for _ in range(5):
        c=p.mean(0);_,u=np.linalg.eigh(np.cov(p.T));n=u[:,0];n*=1 if n[2]>0 else -1
        d=(p-c)@n;p=p[np.abs(d)<np.quantile(abs(d),.95)]
    y=np.array([0,1.,0]);y-=n*(y@n);y/=np.linalg.norm(y);x=np.cross(y,n)
    R=np.array([x,y,n]);T=np.eye(4);T[:3,:3]=R;T[:3,3]=-R@c
    wall={'raw_to_wall_frame_units':T.tolist(),'regions_raw_front_px':regions,'plane_residual_rms_raw':float(np.sqrt(np.mean(((allp-c)@n)**2))),'points':len(allp),'scale_status':'inspection frame; not aligned to primary scan'}
    (CACHE/'wall_frame.json').write_text(json.dumps(wall,indent=2))
    v=v@R.T-R@c;np.save(CACHE/'plane_vertices.npy',v)
    target=(T@np.array([0,1.63,0,1]))[:3];target[2]=0
    view={'center':target.tolist(),'span':1.4,'pixels':1800}
    (CACHE/'plane_view.json').write_text(json.dumps(view))
    pts={};factor=1.4/1800
    for name,px in {'U':[897,565],'L':[884,1157],'hub_U':[888,591],'hub_L':[880,1184]}.items():
        xy=target[:2]+np.array([px[0]-900,900-px[1]])*factor
        j=np.argmin(np.linalg.norm(v[:,:2]-xy,axis=1))
        pts[name]={'pixels':px,'zero_based_vertex':int(j),'point_wall_units':v[j].tolist()}
    scale=80/np.linalg.norm(np.array(pts['U']['point_wall_units'])-pts['L']['point_wall_units'])
    # Local diagnostic frame only: origin at projected L cap, wall Z=0.
    S=np.eye(4);S[:3,:3]*=scale
    S[:2,3]=-scale*np.array(pts['L']['point_wall_units'][:2])
    report={'id':'ATTACHED01','source_sha256':sha(src),'state':'inner plate attached; successful fit not established',
      'view':view,'plane':wall,'manual_visual_picks':pts,'uniform_mm_per_raw_unit':float(scale),
      'raw_to_local_diagnostic_mm':(S@T).tolist(),
      'calibration':'80 mm user U-L tip distance. Manually selected cap centers. This is not an independent accuracy check or global registration.',
      'checks_mm':{'outline_width_approx':988*factor*scale,'outline_height_approx':1220*factor*scale,'caliper_width':130.35,'caliper_height':165.1,'estimated_stem_above_hub_center':[26*factor*scale,27*factor*scale]},
      'conclusions':['Actual stems appear above visible hub centers in wall-normal projection. Do not force concentricity in the evidence.',
        'Reflective-metal/hub contours are warped. Width cross-check differs from caliper by about 4 mm; retain physical dimensions for CAD.',
        'New scan is useful direct assembly evidence, not a source for precision mounting holes or hidden engagement.'],
      'not_established':['shaft/hub axis alignment','physical handle engagement','cover center','foam support/compression','water performance'],
      'CAD_effect':'No aperture shrink or fixed mounting pattern inferred. Keep a broad upright trial opening and adjustable placement.',
      'primary_scan_or_transform_modified':False}
    (OUT/'attached_scan_assessment.json').write_text(json.dumps(report,indent=2)+'\n')
    for f in ['raw_front.png','plane_front.png']:
        if (CACHE/f).exists():shutil.copy2(CACHE/f,OUT/f)
    print('ATTACHED01: preserved archive extracted/CRC verified; diagnostic plane and scale recorded.')
if __name__=='__main__':run()
