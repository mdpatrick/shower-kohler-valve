"""Recompute the explicit uniform-scale wall registration, never nonuniform fitting."""
from pathlib import Path
import json,numpy as np
ROOT=Path(__file__).resolve().parents[2]

def run():
    a=json.loads((ROOT/'canon/scan_annotations.json').read_text())
    vp=ROOT/'data/derived/shower-hole-valve-polycam-vertices.npy'
    if vp.exists(): v=np.load(vp)
    else:
        with (ROOT/'data/extracted/shower-hole-valve-polycam/10_14_2026.obj').open() as f:
            v=np.array([[float(x) for x in l.split()[1:4]] for l in f if l.startswith('v ')])
        vp.parent.mkdir(parents=True,exist_ok=True);np.save(vp,v)
    extent=a['raw_view']['ortho_scale']; mid=a['raw_view']['center'];res=a['raw_view']['pixels']
    regions=[]
    for x0,y0,x1,y1 in a['plane_regions_px']:
        xmin=(x0/res-.5)*extent+mid[0];xmax=(x1/res-.5)*extent+mid[0]
        ymax=(.5-y0/res)*extent+mid[1];ymin=(.5-y1/res)*extent+mid[1]
        regions.append(v[(v[:,0]>xmin)&(v[:,0]<xmax)&(v[:,1]>ymin)&(v[:,1]<ymax)])
    allp=np.vstack(regions);p=allp.copy()
    for _ in range(5):
        c=p.mean(0);ev,U=np.linalg.eigh(np.cov(p.T));n=U[:,0];n=n if n[2]>0 else -n
        rr=(p-c)@n;p=p[np.abs(rr)<np.quantile(np.abs(rr),.95)]
    y=np.array([0.,1.,0.]);y=y-n*np.dot(y,n);y/=np.linalg.norm(y);x=np.cross(y,n);R=np.stack([x,y,n])
    low=np.array(a['landmarks_raw']['AXIS-LOWER-TIP']['point'])
    high=np.array(a['landmarks_raw']['AXIS-UPPER-TIP']['point'])
    origin=low-n*np.dot(low-c,n)
    measurements=json.loads((ROOT/'canon/measurements.json').read_text())
    confirmed={m['id']:m for m in measurements['measurements'] if m['status']=='user-confirmed'}
    # A verified scale observation replaces the nominal scale anchor without moving the raw scan.
    scale_measurement=confirmed.get('M01')
    nominal=a['provisional_scale_anchor_mm']
    separation=np.linalg.norm(high-low)
    scalar=(scale_measurement['value_mm'] if scale_measurement else nominal)/separation
    T=np.eye(4);T[:3,:3]=R*scalar;T[:3,3]=-R@origin*scalar
    B=np.array([[.001,0,0,0],[0,0,-.001,0],[0,.001,0,0],[0,0,0,1.]])
    def point(p):return (T@np.r_[p,1])[:3].tolist()
    data={'schema_version':1,'units':'mm','source_units':'OBJ unit unspecified',
        'state':'as_observed_at_capture','installed_frame':'+X right, +Y up, +Z out of wall',
        'origin':'orthogonal projection of AXIS-LOWER-TIP onto fitted intact-tile plane',
        'orientation_note':'Y is scan Y projected into fitted plane. Grout appears near vertical; true plumb is not verified. Valve pose is preserved, not straightened.',
        'scale_status':'user-confirmed scale input; independent cross-check still required' if scale_measurement else 'inferred conditional scale; NOT physically calibrated',
        'scale_anchor':'M01' if scale_measurement else 'user-identified K-T14489-4 nominal 3-1/8 inch control spacing; actual spacing unmeasured',
        'scale_anchor_mm':scale_measurement['value_mm'] if scale_measurement else nominal,
        'uniform_mm_per_source_unit':scalar,'source_separation_units':separation,
        'raw_to_installed_mm':T.tolist(),'installed_mm_to_blender_m':B.tolist(),
        'raw_to_blender_m':(B@T).tolist(),'raw_to_installed_determinant':float(np.linalg.det(T[:3,:3])),
        'plane':{'raw_origin':c.tolist(),'raw_normal':n.tolist(),'regions_px':a['plane_regions_px'],
            'points_count':len(allp),'fit_retained':len(p),'method':'5 iterations PCA plane with 95% residual retention per iteration',
            'all_selected_rms_mm':float(np.sqrt(np.mean(((allp-c)@n)**2))*scalar),
            'all_selected_p95_abs_mm':float(np.quantile(np.abs((allp-c)@n),.95)*scalar),
            'note':'Residual is local consistency of selected stone patches, not absolute scan accuracy or stone soundness.'},
        'landmarks_installed_mm':{k:dict(info,point_mm=point(info['point'])) for k,info in a['landmarks_raw'].items()},
        'secondary_registration':{'SCAN-PLATE-1':'excluded from dimensional registration due severe warp; no correspondence asserted','SCAN-PLATE-2':'excluded from dimensional registration due severe warp; no correspondence asserted'}}
    out=ROOT/'data/derived/registration.json';out.write_text(json.dumps(data,indent=2)+'\n')
    print('Registration:',data['scale_status'],round(scalar,3),'mm/source unit; plane RMS',round(data['plane']['all_selected_rms_mm'],3),'mm')
    return data

if __name__=='__main__':run()
