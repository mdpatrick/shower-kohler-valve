"""Captured full-resolution surface points inside provisional measured-reference solids."""
from pathlib import Path
import json,numpy as np,cadquery as cq
from shapely.geometry import Polygon
from shapely import contains_xy
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'deliverables/current/fabrication/F005'
def run():
 r=json.loads((ROOT/'data/derived/resolved.json').read_text());reg=json.loads((ROOT/'data/derived/registration.json').read_text());T=np.array(reg['raw_to_installed_mm']);v=np.load(ROOT/'data/derived/shower-hole-valve-polycam-vertices.npy')@T[:3,:3].T+T[:3,3]
 region=Polygon(next(f['contour_mm'] for f in r['features'] if f['id']=='OPEN-MAIN')).buffer(-3);v=v[contains_xy(region,v[:,0],v[:,1])];rows=[]
 for id,foam in [('REF-INNER',6),('REF-INNER',5),('REF-INNER',4),('REF-INNER',3),('REF-COVER',None)]:
  shape=cq.Shape.importBrep(str(ROOT/'data/derived/fabrication_F005'/f'{id}.brep'))
  pos=np.array([*r['inner_center_mm'],2.524+foam]) if foam is not None else np.array([0,39.95,2.524]);q=v-pos;bb=shape.BoundingBox();mask=(q[:,0]>=bb.xmin)&(q[:,0]<=bb.xmax)&(q[:,1]>=bb.ymin)&(q[:,1]<=bb.ymax)&(q[:,2]>=bb.zmin)&(q[:,2]<=bb.zmax);s=q[mask]
  hits=np.array([p for p in s if shape.isInside(cq.Vector(*p),1e-6)])
  installed=hits+pos if len(hits) else np.empty((0,3))
  features=[('SW stud',r['studs_mm'][0]),('NE stud',r['studs_mm'][1]),('Lower control',r['controls_mm'][0]),('Upper control',r['controls_mm'][1])]
  groups={name:[] for name,_ in features}
  for point in installed:
   name,_=min(features,key=lambda f:np.linalg.norm(point[:2]-np.array(f[1][:2])))
   groups[name].append(point.tolist())
  zones={name:{'count':len(points),'bounds_mm':[np.min(points,axis=0).tolist(),np.max(points,axis=0).tolist()] if points else None} for name,points in groups.items()}
  rows.append({'reference':id,'foam_trial_mm':foam,'sampled_vertices':len(s),'vertices_inside_reference_solid':len(hits),'nearest_feature_zones':zones,'example_installed_points_mm':installed[:5].tolist(),'interpretation':'Provisional shape conflict' if len(hits) else 'No sampled penetration, NOT a physical-fit pass'})
 result={'design_revision':'F005','status':'CONDITIONAL reference-shape study','method':'Exact OCCT inside-solid test of full-resolution captured vertices at the trial SS060 surface. No legacy valve cylinders used.','rows':rows,'limitations':['Local stamped profile/nut-seat depth and rear cavity are not measured.','Inside-solid sample is not a complete triangle/volume collision proof.','Foam trial values are sensitivity scenarios, not allowed compression specifications.','Stud axes differ from tip coordinates; scan scale and hidden surfaces remain unresolved.']}
 (OUT/'reference_fit_check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'rows':[{k:v for k,v in x.items() if k!='example_installed_points_mm'} for x in rows]}))
 return result
if __name__=='__main__':run()
