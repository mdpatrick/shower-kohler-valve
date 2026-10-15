"""Independent triangle clipping check of the captured forward insertion envelope."""
from pathlib import Path
import json,numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'deliverables/current/fabrication/F005'
def run():
 d=json.loads((ROOT/'canon/fabrication_designs.json').read_text());r=json.loads((ROOT/'data/derived/resolved.json').read_text());reg=json.loads((ROOT/'data/derived/registration.json').read_text());T=np.array(reg['raw_to_installed_mm'])
 v=np.load(ROOT/'data/derived/shower-hole-valve-polycam-vertices.npy')@T[:3,:3].T+T[:3,3]
 fs=[]
 for line in (ROOT/'data/extracted/shower-hole-valve-polycam/10_14_2026.obj').open():
  if line.startswith('f '):
   ids=[int(s.split('/')[0])-1 for s in line.split()[1:]]
   fs.extend((ids[0],ids[i],ids[i+1]) for i in range(1,len(ids)-1))
 tri=v[np.array(fs)];region=Polygon(next(f['contour_mm'] for f in r['features'] if f['id']=='OPEN-MAIN')).buffer(-3);b=region.bounds
 keep=(tri[:,:,2].max(1)>=.5)&(tri[:,:,0].max(1)>=b[0])&(tri[:,:,0].min(1)<=b[2])&(tri[:,:,1].max(1)>=b[1])&(tri[:,:,1].min(1)<=b[3]);tri=tri[keep]
 ap=Polygon(d['aperture']['base_convex_polygon_installed_mm']).buffer(d['aperture']['outward_radius_mm'],quad_segs=128)
 conflicts=[];considered=0
 for tr in tri:
  poly=[]
  for i,p in enumerate(tr):
   q=tr[(i+1)%3];a=p[2]>=.5;c=q[2]>=.5
   if a:poly.append(p)
   if a!=c:poly.append(p+(.5-p[2])/(q[2]-p[2])*(q-p))
  if len(poly)<3:continue
  p=Polygon([(q[0],q[1]) for q in poly])
  if p.area<1e-9:continue
  if not p.is_valid:p=p.buffer(0)
  clip=p.intersection(region)
  if clip.area<1e-9:continue
  considered+=1;outside=clip.difference(ap)
  if outside.area>1e-7:conflicts.append(outside)
 union=unary_union(conflicts)
 result={'status':'PASS in captured surface' if not conflicts else 'CONFLICT in captured surface','forward_triangles_considered':considered,'triangles_outside_aperture':len(conflicts),'union_projected_conflict_area_mm2':union.area,'method':'Clip every primary mesh triangle to Z >= 0.5 mm, project XY, clip to OPEN-MAIN eroded 3 mm; compare to exact design aperture generating polygon plus 1.75 mm arc offset (128-segment analysis approximation).','limits':'Excludes wall edge by explicit mask; no hidden geometry or physically bounded scale; applies only to axial insertion at/outside Z=0.5. Physical fit remains unresolved.','conflict_bounds_mm':list(union.bounds) if not union.is_empty else None}
 (OUT/'mesh_path_check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
 return result
if __name__=='__main__':run()
