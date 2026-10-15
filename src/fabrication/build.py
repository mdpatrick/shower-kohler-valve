"""F005 prototype/quote geometry. Read-only canon; preserve installed scan and R004 evidence."""
from pathlib import Path
import json,math,hashlib,csv
import numpy as np
import cadquery as cq
import ezdxf,trimesh
from shapely.geometry import Polygon,Point,MultiPoint,LineString,box
from shapely.affinity import translate
from shapely import contains_xy
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'deliverables/current/fabrication/F005'
CACHE=ROOT/'data/derived/fabrication_F005'
STATUS='DRAFT_NOT_FOR_FABRICATION'
def read(p):return json.loads((ROOT/p).read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def rect2(w,h,r,c=(0,0)):
 return translate(box(-w/2+r,-h/2+r,w/2-r,h/2-r).buffer(r,quad_segs=128),*c)
def rect3(w,h,r,t):return cq.Workplane('XY').rect(w,h).extrude(t).edges('|Z').fillet(r)
def shape2(p):
 c=p['center_mm']
 return Point(*c).buffer(p['diameter_mm']/2,quad_segs=256) if p['shape']=='circle' else rect2(p['width_mm'],p['height_mm'],p['radius_mm'],c)
def export_solid(id,solid,folder,meta,**extra):
 s=solid.val() if isinstance(solid,cq.Workplane) else solid
 assert s.isValid() and len(s.Solids())==1,id
 bb=s.BoundingBox()
 stem=f'{id}_F005_{STATUS}';step=folder/(stem+'.step');stl=folder/(stem+'.stl')
 cq.exporters.export(s,str(step));cq.exporters.export(s,str(stl),tolerance=.025,angularTolerance=.05)
 s.exportBrep(str(CACHE/(id+'.brep')))
 re=cq.importers.importStep(str(step)).val();rb=re.BoundingBox()
 assert re.isValid() and abs(re.Volume()-s.Volume())<.01
 assert max(abs(a-b) for a,b in zip([bb.xlen,bb.ylen,bb.zlen],[rb.xlen,rb.ylen,rb.zlen]))<1e-5,(id,[bb.xlen,bb.ylen,bb.zlen],[rb.xlen,rb.ylen,rb.zlen])
 mesh=trimesh.load(stl,force='mesh');assert mesh.is_watertight,id
 assert max(abs(a-b) for a,b in zip(mesh.extents,[bb.xlen,bb.ylen,bb.zlen]))<.06
 meta.append(dict(id=id,step=str(step.relative_to(OUT)),stl=str(stl.relative_to(OUT)),bounds_mm=[[bb.xmin,bb.ymin,bb.zmin],[bb.xmax,bb.ymax,bb.zmax]],volume_mm3=s.Volume(),step_reimport='PASS',stl_watertight=True,**extra))
 return s

def build():
 for p in [OUT/'cad',OUT/'reference',OUT/'views',CACHE]:p.mkdir(parents=True,exist_ok=True)
 d=read('canon/fabrication_designs.json');r=read('data/derived/resolved.json');reg=read('data/derived/registration.json')
 if d['evidence_revision']!=r['revision']:raise ValueError('F005 evidence revision stale; reconcile design canon before rebuilding')
 T=np.array(reg['raw_to_installed_mm']);v=np.load(ROOT/'data/derived/shower-hole-valve-polycam-vertices.npy')@T[:3,:3].T+T[:3,3]
 opening=Polygon(next(f['contour_mm'] for f in r['features'] if f['id']=='OPEN-MAIN'))
 base=Polygon(d['aperture']['base_convex_polygon_installed_mm']);ap=base.buffer(d['aperture']['outward_radius_mm'],quad_segs=128)
 parts={};meta=[];checks=[]
 for p in d['parts']:
  c=np.array(p['center_mm']);outline=shape2(p);hole=ap if p.get('aperture')=='AP-MAIN' else Point(*c).buffer(p['aperture_diameter_mm']/2,quad_segs=256)
  # Local coordinates at each custom outline center, Z=0 rear face.
  coords=np.array(d['aperture']['base_convex_polygon_installed_mm'])-c
  for stock in d['stock_options']:
   t=stock['thickness_mm'];raw=cq.Workplane('XY').circle(p['diameter_mm']/2).extrude(t) if p['shape']=='circle' else rect3(p['width_mm'],p['height_mm'],p['radius_mm'],t)
   cut=cq.Workplane('XY').polyline([tuple(x) for x in coords]).close().offset2D(d['aperture']['outward_radius_mm']).extrude(t+2).translate((0,0,-1)) if p.get('aperture')=='AP-MAIN' else cq.Workplane('XY').circle(p['aperture_diameter_mm']/2).extrude(t+2).translate((0,0,-1))
   solid=raw.cut(cut);id=p['id']+'-'+stock['id'];parts[id]=export_solid(id,solid,OUT/'cad',meta,role='custom part',stock=stock,center_installed_mm=p['center_mm'],position_z_mm=d['seal_display_thickness_mm'])
   if stock['id']=='SS060':
    fn=OUT/'cad'/f"{p['id']}_F005_CUT_ONLY_{STATUS}.dxf"
    top=solid.faces('>Z').wires().translate((0,0,-t));cq.exporters.export(top,str(fn),exportType='DXF')
    doc=ezdxf.readfile(fn);doc.units=ezdxf.units.MM;doc.saveas(fn)
    entities=list(doc.modelspace());allowed={'LINE','ARC','CIRCLE','LWPOLYLINE','SPLINE'};assert all(e.dxftype()in allowed for e in entities)
    rebuilt=cq.importers.importDXF(str(fn)).wires().toPending().extrude(t)
    assert rebuilt.val().isValid() and abs(rebuilt.val().Volume()-solid.val().Volume())<.02
    assert len(top.vals())==2
    checks.append(dict(id=p['id']+'-DXF',status='PASS',contours=2,apertures=1,annotations=0,units='mm',entity_count=len(entities),entity_types=sorted({e.dxftype() for e in entities}),volume_difference_mm3=abs(rebuilt.val().Volume()-solid.val().Volume())))
  p['computed']={'area_mm2':outline.area-hole.area,'cut_length_mm':outline.length+hole.length,'aperture_bounds_installed_mm':list(hole.bounds),'aperture_area_mm2':hole.area}
 # Measured reference plate: free envelope retained. Local formed regions are explicitly illustrative.
 a=r['assumptions'];ic=np.array(r['inner_center_mm']);height=a['inner_formed_depth_mm'];sheet=1.5
 inner=rect3(a['inner_width_mm'],a['inner_height_mm'],a['inner_corner_radius_mm'],height)
 inner=inner.cut(rect3(a['inner_width_mm']-3,a['inner_height_mm']-3,a['inner_corner_radius_mm']-1.5,height-sheet+.1).translate((0,0,-.1)))
 for op in r['inner_control_openings']:
  x,y=op['center_local_mm'];inner=inner.cut(cq.Workplane('XY').center(x,y).circle(op['diameter_mm']/2).extrude(30).translate((0,0,-1)))
 for hole in r['inner_slots']:
  x,y=np.array(hole['center_mm'])-ic
  # Recessed fastener seats are photo-informed, depths provisional.
  inner=inner.cut(cq.Workplane('XY').center(x,y).circle(8).extrude(30).translate((0,0,-1)))
  cup=cq.Workplane('XY').center(x,y).circle(6.5).workplane(offset=height-sheet).circle(8.7).loft()
  void=cq.Workplane('XY').center(x,y).circle(5).workplane(offset=height-sheet).circle(7.2).loft().translate((0,0,sheet))
  cup=cup.cut(void).cut(cq.Workplane('XY').center(x,y).circle(hole['width_mm']/2).extrude(30).translate((0,0,-1)))
  inner=inner.union(cup)
 inner_shape=export_solid('REF-INNER',inner,OUT/'reference',meta,role='Kohler reference only',limitation='Measured front envelope; uniform dish, recessed fastener-seat Z, sheet/corners/lower bore/NE bore and rear lands provisional')
 # Explicit outer-cover scenario. Equal lower bore is NOT an accepted reading.
 scenario=d['outer_photo_scenario'];ud=scenario['upper_bore_mm'];ld=scenario['lower_bore_mm'];cc=scenario['gap_mm']+(ud+ld)/2
 yl=-184.15/2+scenario['bottom_gap_mm']+ld/2;yu=yl+cc
 radius=184.15/2
 profile=[(0,16),(60,16),(71,13),(radius-2,13),(radius,11),(radius,0),(radius-1.5,0),(radius-1.5,10),(radius-3,11.5),(71,11.5),(60,14.5),(0,14.5)]
 cover=cq.Workplane('XZ').polyline(profile).close().revolve(360,(0,0),(0,1))
 for y,di in [(yl,ld),(yu,ud)]:cover=cover.cut(cq.Workplane('XY').center(0,y).circle(di/2).extrude(40).translate((0,0,-2)))
 cover=cover.cut(cq.Workplane('XY').box(4,8,2,centered=(True,True,False)).translate((0,-radius+2,0)))
 cover_shape=export_solid('REF-COVER',cover,OUT/'reference',meta,role='Kohler reference only',limitation='OD and upper bore measured. Equal lower bore and inside-edge gaps scenario. Rear cavity and notch size unmeasured.')
 foam3=rect3(130.35,165.1,40,6).cut(rect3(118.35,153.1,34,8).translate((0,0,-1)))
 export_solid('REF-FOAM-SCENARIO',foam3,OUT/'reference',meta,role='Foam footprint scenario only',limitation='6 mm approximate width/free thickness; outline assumed flush to metal perimeter, NOT measured rear path.')
 # Nonfused CAD assembly in unchanged installed coordinates, with diagnostics retained.
 for pair in ['A','B']:
  assembly=cq.Assembly(name=f'F005_PAIR_{pair}_OBSERVED_HARDWARE_CONFLICT')
  t=d['stock_options'][0]['thickness_mm'];nw=t+d['seal_display_thickness_mm']
  for p in d['parts']:
   if not p['id'].endswith(pair):continue
   assembly.add(parts[p['id']+'-SS060'],name=p['id'],loc=cq.Location(cq.Vector(*p['center_mm'],1)))
  assembly.add(inner_shape,name='REF_INNER_FREE',loc=cq.Location(cq.Vector(*ic,nw+6)))
  assembly.add(cover_shape,name='REF_COVER_ASSUMED_CAVITY',loc=cq.Location(cq.Vector(0,-yl,nw)))
  for id in ['STUD-SW','STUD-NE','VALVE-LOWER','VALVE-UPPER']:
   old=next(x for x in read('data/derived/cad/parts.json')['parts'] if x['id']==id)
   s=cq.Shape.importBrep(str(ROOT/old['brep']));assembly.add(s,name=id,loc=cq.Location(cq.Vector(*old['location_mm'])))
  path=OUT/'reference'/f'PAIR-{pair}_F005_DIAGNOSTIC_ASSEMBLY_{STATUS}.step';assembly.export(str(path))
  re=cq.importers.importStep(str(path));assert len(re.solids().vals())==8
  checks.append(dict(id='ASSEMBLY-'+pair,status='PASS',separate_solids=8,physical_fit='CONFLICT / UNRESOLVED',limitation='Simple valve cylinders retained only as labeled legacy reference envelopes, not collision authority. Irregular scan supplied in Blender.'))
 # Read-only analysis of conditional geometry.
 feats=[f for f in r['features'] if f.get('include_in_coverage')]
 coverage=[]
 for p in d['parts'][:2]:
  out=shape2(p)
  for f in feats:
   q=Polygon(f['contour_mm']);margin=q.distance(out.boundary) if out.covers(q) else -q.difference(out).hausdorff_distance(out.boundary)
   coverage.append(dict(part=p['id'],feature=f['id'],contains=out.covers(q),outer_margin_mm=margin,after_trace_allowance_mm=margin-f.get('trace_allowance_mm_at_R001',1.5),physical_sound_land='UNRESOLVED'))
 pts=np.array(d['diverter_damage_trace']['pixels_outline']);divtrace=np.column_stack(((pts[:,0]-900)*620/1800,40+(900-pts[:,1])*620/1800))
 d['diverter_damage_trace']['contour_installed_mm']=divtrace.tolist();dq=Polygon(divtrace)
 divcov=[dict(part=p['id'],contains=shape2(p).covers(dq),outer_margin_mm=dq.distance(shape2(p).boundary),after_trace_allowance_mm=dq.distance(shape2(p).boundary)-2,physical_fit='UNRESOLVED') for p in d['parts'][2:]]
 gaps=[]
 for pair in ['A','B']:
  p=next(p for p in d['parts'] if p['id']=='MAIN-'+pair);q=next(p for p in d['parts'] if p['id']=='DIV-'+pair)
  gaps.append(dict(pair=pair,gap_mm=shape2(p).distance(shape2(q)),parts_overlap_area_mm2=shape2(p).intersection(shape2(q)).area))
 sw,ne=np.array(r['studs_mm']);dist=np.linalg.norm(ne[:2]-sw[:2]);expect=106.39+5.66
 fit={'conditional_hole_center_distance_mm':expect,'condition':'NE hole same 5.66 mm as measured SW','scan_tip_center_distance_mm':float(dist),'mismatch_mm':float(expect-dist),'best_rigid_registration_error_per_hole_mm':float(abs(expect-dist)/2),'assumed_stud_diameter_mm':5,'available_radial_clearance_mm':(5.66-5)/2,'model_result':'FAIL under equal-hole / normal-axis / 5 mm stud assumptions; not a proven actual mounting defect','scale_factor_to_force_match':expect/dist,'scale_not_applied':True}
 samples=v[(v[:,2]>=d['aperture']['floor_z_mm'])&contains_xy(opening.buffer(-3),v[:,0],v[:,1])]
 inside=contains_xy(ap,samples[:,0],samples[:,1]);minclear=min(ap.boundary.distance(Point(*p)) for p in Polygon(MultiPoint(samples[:,:2]).convex_hull).exterior.coords)
 fitmesh={'full_resolution_forward_vertices':len(samples),'outside_aperture_vertices':int((~inside).sum()),'min_projected_vertex_clearance_mm':minclear,'method':'All captured forward vertex positions in eroded main opening, not just at final plate slice','limitations':['Scan surface not complete physical volume','Opening erosion masks stone border','Unbounded physical scale/registration/occlusion errors remain','Cartridge tool access requires backing plate removal']}
 foam=[]
 for inset in d['foam_scenarios']['insets_mm']:
  outer=rect2(130.35-2*inset,165.1-2*inset,40-inset,ic);inner2=outer.buffer(-6);band=outer.difference(inner2)
  overlap=band.intersection(ap).area
  foam.append(dict(inset_mm=inset,aperture_cuts_band_mm2=overlap,conditional_continuous_land=overlap<1e-6,min_gap_to_inner_band_mm=ap.distance(inner2.boundary) if inner2.covers(ap) else None))
 # Test actually sampled profile at each reference sheet height; do not reuse 60 mm cylinders.
 section=[]
 for label,i in [('lower',0),('upper',1)]:
  c=np.array(r['controls_mm'][i][:2]);rad=np.linalg.norm(v[:,:2]-c,axis=1)
  for z in [6,10,14,18,22,26]:
   use=(abs(v[:,2]-z)<.5)&(rad<33);rr=rad[use]
   section.append(dict(control=label,z_mm=z,vertices=int(use.sum()),max_local_radius_mm=float(rr.max()) if len(rr) else None))
 depth=[]
 for st in d['stock_options']:
  nw=st['thickness_mm']+1
  depth.append(dict(stock=st['id'],trial_surface_z_mm=nw,stud_tip_minus_assumed_local_cover_rear_mm=[float(sw[2]-(nw+14.5)),float(ne[2]-(nw+14.5))],upper_tip_projection_from_trial_surface_mm=float(r['controls_mm'][1][2]-nw),warning='14.5 mm cavity is a central placeholder, not measured at studs. Positive excess flags interference; no adjustment length specified.'))
 result={'design_revision':'F005','evidence_revision':r['revision'],'status':STATUS,'parts':meta,'export_checks':checks,'coverage':coverage,'diverter_coverage':divcov,'neighbor_gaps':gaps,'mounting_fit':fit,'swept_aperture':fitmesh,'foam_sensitivity':foam,'sampled_control_sections':section,'depth_scenarios':depth,'outer_photo_scenario':{'center_distance_mm':cc,'versus_nominal_mm':cc-79.375,'lower_center_local_mm':[0,yl],'upper_center_local_mm':[0,yu],'lower_aligned_upper_axis_error_mm':float(np.linalg.norm(np.array([0,cc])-np.array(r['controls_mm'][1][:2]))),'assumptions':scenario},'readiness':{'CAD_export_integrity':'PASS','physical_fit':'UNRESOLVED','water_performance':'NOT TESTED','manufacturing_release':'HOLD','design_selection':'A and B unselected alternatives'}}
 # Extract actual manufacturer mesh components without altering them; convert inch CAD frame to installed mm.
 compmeta=[]
 for f in ['T14489-4','T14491-4']:
  m=trimesh.load(ROOT/f'data/evidence/kohler-{f}.obj',force='mesh',process=True);e=m.edges_unique
  graph=coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(len(m.vertices),)*2);n,labels=connected_components(graph,directed=False)
  for i in range(n):
   mask=labels[m.faces[:,0]]==i;chunk=m.submesh([np.flatnonzero(mask)],append=True,repair=False)
   if len(chunk.faces)<20:continue
   chunk.vertices=np.column_stack((chunk.vertices[:,0],chunk.vertices[:,2],-chunk.vertices[:,1]))*25.4
   file=CACHE/f'KOHLER-{f}-{i}.stl';chunk.export(file)
   compmeta.append(dict(model=f,index=i,stl=str(file.relative_to(ROOT)),bounds_installed_local_mm=chunk.bounds.tolist(),face_count=len(chunk.faces),role='Official nominal exterior; not hidden mating authority'))
 result['manufacturer_components']=compmeta
 write(OUT/'analysis.json',result);write(CACHE/'design.json',d);write(CACHE/'analysis.json',result)
 with (OUT/'cad'/'main_aperture_generating_coordinates_F005.csv').open('w') as f:
  writer=csv.writer(f);writer.writerow(['vertex','X_installed_mm','Y_installed_mm','outward_offset_mm'])
  for i,p in enumerate(d['aperture']['base_convex_polygon_installed_mm'],1):writer.writerow([i,*p,d['aperture']['outward_radius_mm']])
 print('F005: exported',len(meta),'validated separate solids; gaps',gaps,'; aperture sample clearance',round(minclear,3))
 print('Foam sensitivity',foam)
 from mesh_check import run as mesh_check
 mesh_check()
 return result
if __name__=='__main__':build()
