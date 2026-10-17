"""RF01 bounded removable form assessment; not a wall-strength certification."""
from pathlib import Path
import json,sys,math,hashlib,zipfile
import numpy as np
import cadquery as cq
import trimesh
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
from shapely.affinity import affine_transform,translate
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.analysis.fit_trial_release import load_capture,slice_project
from src.analysis.registration_trial import coeff
from src.fabrication.fit_trial import rr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PP,Rectangle

def read(p):return json.loads((ROOT/p).read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def cap(w,h,z):
 y=(h-w)/2
 return cq.Workplane('XY',origin=(0,0,z)).moveTo(-w/2,-y).lineTo(-w/2,y).threePointArc((0,h/2),(w/2,y)).lineTo(w/2,-y).threePointArc((0,-h/2),(-w/2,-y)).close()
def run():
 d=read('canon/fit_trial_design.json');s=read('canon/repair_form_design.json');out=ROOT/d['output_directory'];eng=out/'engineering';dest=out/'REPAIR_FORM_TRIAL';dest.mkdir(exist_ok=True)
 col=s['collar'];p=s['panel'];w,h=col['outer_width_mm'],col['outer_height_mm'];wall,dep,film=col['wall_mm'],col['depth_mm'],col['liner_mm'];draft=dep*math.tan(math.radians(col['draft_deg']));z=film
 # Drafted wall, narrower at rear. Face is independently flat; thin release
 # film is accounted for in the face datum and concrete-contact envelope.
 outer=cq.Solid.makeLoft([cap(w-2*draft,h-2*draft,z-dep).val(),cap(w,h,z).val()])
 inner=cq.Solid.makeLoft([cap(w-2*wall-2*draft,h-2*wall-2*draft,z-dep-.02).val(),cap(w-2*wall,h-2*wall,z+.02).val()])
 collar=cq.Workplane('XY').newObject([outer.cut(inner)])
 panel=cq.Workplane('XY',origin=(0,0,z)).circle(p['outer_diameter_mm']/2).extrude(p['thickness_mm']).cut(cap(w-2*wall,h-2*wall,z-1).extrude(p['thickness_mm']+2))
 tool=panel.union(collar).clean();assert tool.val().isValid() and len(tool.val().Solids())==1
 name='RF01_MAIN_REMOVABLE_FORM_PETG';paths=[]
 for ext in ['step','stl']:
  fp=dest/(name+'.'+ext);cq.exporters.export(tool,str(fp),tolerance=.02,angularTolerance=.05);paths.append(fp)
 rb=cq.importers.importStep(str(paths[0])).val();mesh=trimesh.load(paths[1],force='mesh');assert rb.isValid() and len(rb.Solids())==1 and mesh.is_watertight and len(mesh.split())==1
 # Entire local source, with no eroded mask. A conservative collar envelope
 # combines the largest outside and smallest inside over the whole depth.
 study=read(d['output_directory']+'/engineering/locator_evaluation.json');tf=study['transforms']['cover_to_installed_xy_up'];Q=np.array(tf['row_rotation']);t=np.array(tf['translation_mm'])
 v,f=load_capture();alltri=v[f];tri=alltri;xy=(tri[:,:,:2]-t)@Q.T
 mask=(xy[:,:,0].max(1)>-65)&(xy[:,:,0].min(1)<65)&(xy[:,:,1].max(1)>-85)&(xy[:,:,1].min(1)<85);tri=tri[mask]
 annulus=rr(w,h,w/2).difference(rr(w-2*wall-2*draft,h-2*wall-2*draft,w/2-wall-draft))
 results=[];surfaces={}
 for label,lo,hi in [('collar seated',-dep,film),('collar insertion and withdrawal',-dep,80),('front face aperture approach',film,80)]:
  surf=affine_transform(unary_union(slice_project(tri,lo,hi)),coeff(Q.T,-t@Q.T));surfaces[label]=surf
  test=annulus if label!='front face aperture approach' else rr(w,h,w/2).difference(rr(w-2*wall,h-2*wall,w/2-wall))
  results.append({'scope':label,'z_mm':[lo,hi],'source_intersection_area_mm2':surf.intersection(test).area,'local_source_triangles':len(tri)})
 # Check the complete face too, separately from the aperture lip. It is meant
 # to contact stone; above-plane source topography prevents a perfect-seat claim.
 broad=(xy[:,:,0].max(1)>-122)&(xy[:,:,0].min(1)<122)&(xy[:,:,1].max(1)>-122)&(xy[:,:,1].min(1)<122)
 face_surfaces=affine_transform(unary_union(slice_project(alltri[broad],film,80)),coeff(Q.T,-t@Q.T))
 face_area=Point(0,0).buffer(p['outer_diameter_mm']/2,quad_segs=128).difference(rr(w-2*wall,h-2*wall,w/2-wall))
 face_overlap=face_surfaces.intersection(face_area).area
 # Actual source control opening footprints fit the smaller rear opening as a
 # service-size proxy. This is NOT a wrench/cartridge swept-volume proof.
 inside=rr(w-2*wall-2*draft,h-2*wall-2*draft,w/2-wall-draft)
 openings=[]
 for label,cy,diam in [('U',40.09,48.46),('L',-39.95,50)]:
  bore=Point(0,cy).buffer(diam/2,quad_segs=128);openings.append({'id':label,'diameter_mm':diam,'basis':'upper owner opening / lower reference assumption','within_smallest_collar_opening':inside.covers(bore),'boundary_clearance_mm':inside.boundary.distance(bore)})
 # Modeling the lined as-cast front opening separately prevents conflating it
 # with the metal aperture. Upper collar edge shortens the cast hole.
 cast=rr(w+2*film,h+2*film,w/2+film)
 metal=rr(d['main']['aperture_width_mm'],d['main']['aperture_height_mm'],d['main']['aperture_radius_mm'])
 foam=d['foam'];fo=rr(foam['outer_width_mm'],foam['outer_height_mm'],foam['outer_corner_radius_mm']);fi=rr(foam['outer_width_mm']-12,foam['outer_height_mm']-12,foam['outer_corner_radius_mm']-6);band=translate(fo.difference(fi),0,study['transforms']['inner_outline_to_cover_xy_up']['translation_mm'][1])
 nominal=all(x['source_intersection_area_mm2']<.001 for x in results)
 decision=s['decision'] if nominal else 'RF01 remains a modeled assessment only: captured interference prevents tool release. Use supported local repair with individually removable shuttering after contractor inspection; plate quotes remain independent.'
 record={'revision':'RF01','plate_release':d['revision'],'decision':decision,'tool_nominal_path_pass':nominal,'capture_scope':results,'control_opening_proxy_checks':openings,
  'as_cast_front_opening_mm':[w+2*film,h+2*film],'as_cast_rear_opening_mm':[w-2*draft+2*film,h-2*draft+2*film],
  'smallest_tool_internal_mm':[w-2*wall-2*draft,h-2*wall-2*draft],
  'as_cast_foam_overlap_mm2':cast.intersection(band).area,'as_cast_vs_metal':'Cast hole is about 118.45 x145.20 at front; metal capsule remains116.35 x151.10. Sheet bridges about1.05 mm each side and reveals some repaired wall at top/bottom. Required factory opening footprints remain inside both. No plate dimension change is needed for this trial.',
  'comparison':'One-piece 12 mm face with drafted 2 mm collar avoids split seams, rear fasteners, undercuts and loose sacrificial pieces. Panel + two collar halves was considered; it permits inward release but introduces a joint under the repaired face and needs fasteners in narrow material. The current nominal straight withdrawal test does not require that complication. Do not use one-piece if the real dry trial cannot withdraw freely.',
  'specific_rejected_collar':'120.35 x155.10, 2 mm wall and12 mm depth intersects about79 mm2 of captured stone/hardware projection. Enlarging the repair collar to match arbitrary outlines is not permitted. RF01 is shorter and narrower, using a bounded search rather than tile alteration.',
  'full_face_diagnostic':{'projected_overlap_above_nominal_contact_plane_mm2':face_overlap,'scope':'Complete D240 front face outside its actual opening, source Z0.05..80. Includes intended stone contact/topography; not classified as all hardware. Full face seating is NOT established by the clear collar test. Rehearse on actual sound pads; do not force flat or alter tile.'},
  'physical_limits':['Scan error and hidden surfaces are not bounded','Full face seating at the nominal datum is not established; verify stable sound-pad contact and free withdrawal','Factory wrench/cartridge/stop service must be rehearsed with actual components before fill; bores are only proxies','Actual support/bond substrate and brace reaction require contractor inspection','No permanent plastic, plumbing burial or unapproved tile preparation','Coupon establishes liner release and temperature behavior; no certified form load rating'],
  'export_checks':{'valid_connected_solids':len(rb.Solids()),'stl_watertight':bool(mesh.is_watertight),'bounds_mm':[rb.BoundingBox().xlen,rb.BoundingBox().ylen,rb.BoundingBox().zlen],'volume_mm3':rb.Volume(),'face_z_mm':film,'rear_tip_z_mm':film-dep},
  'handoff_blocks':[['Use only where support is missing','Trial the two metal/acrylic plates first. If firm bearing is absent, contractor checks substrate and temporary brace before selecting this form. No new owner survey.'],['Different functions','The D240 form is temporary and12 mm thick. It is not the D220 escutcheon or a permanent liner. No casting until plumbing position and service access pass.'],['Cure and removal','Use REPAIR_FORM_SETUP for product conditions, front datum, protected rear filling and pull-forward removal. No one-hour strength claim is treated as automatic strip, seal or water readiness.']],
  'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['canon/repair_form_design.json','canon/fit_trial_design.json','src/fabrication/repair_form.py']}}
 dump(eng/'form_assessment.json',record)
 fig,axs=plt.subplots(1,3,figsize=(13,5));colors=['#dce6e8','#f5d49d','#438697']
 for ax,back in zip(axs[:2],[False,True]):
  ax.add_patch(PP(np.array(Point(0,0).buffer(120,quad_segs=128).exterior.coords),fc='#dce6e8',ec='#438697'))
  surf=surfaces['collar seated'];geoms=list(surf.geoms) if hasattr(surf,'geoms') else [surf]
  for poly in geoms:
   if poly.geom_type=='Polygon':ax.add_patch(PP(np.array(poly.exterior.coords),fc='#aaa79e',ec='none',alpha=.7))
  ax.plot(*cast.exterior.xy,color='#b47a30',lw=2,label='Lined cast opening')
  ax.plot(*inside.exterior.xy,color='#196779',lw=2,label='Smallest tool interior')
  ax.plot(*metal.exterior.xy,color='#941d63',ls='--',label='Metal aperture')
  for x,y in [(-60,90),(60,90),(0,-102)]:ax.add_patch(plt.Circle((x,y),5,fc='#8e704b'))
  ax.set_aspect('equal');ax.set(xlim=((-128,128) if not back else (128,-128)),ylim=(-128,128));ax.axis('off');ax.set_title('Front setup / datum pads' if not back else 'Rear view / fill OUTSIDE collar')
  if not back:ax.legend(fontsize=7,loc='lower center')
 ax=axs[2];ax.add_patch(Rectangle((-12,59.225),12,40,fc='#e5bb7d'));ax.add_patch(Rectangle((.05,57.175),12,55,fc='#438697'));ax.plot([.05,-11.95],[59.175,59.175-draft],color='#438697',lw=5)
 ax.axvline(0,color='#333',ls='--');ax.text(-11,86,'Supported\nrepair',fontsize=9);ax.text(15,83,'Front panel\n12 mm',fontsize=9);ax.annotate('Withdraw toward shower',xy=(27,66),xytext=(-8,66),arrowprops={'arrowstyle':'->'},fontsize=8);ax.text(-13,49,'No fill: valve / service space',fontsize=9);ax.set(xlim=(-16,47),ylim=(40,120),xlabel='Z outward (mm)',ylabel='X at side (mm)');ax.set_title('Side section / all tool removed later');ax.grid(alpha=.15)
 fig.suptitle('RF01 temporary forming tool — working geometry, physical dry trial required',fontsize=13);fig.tight_layout();fig.savefig(eng/'form_assessment.png',dpi=170);plt.close(fig)
 # Isolated actual exported-mesh preview, no fabricated wall evidence.
 fig=plt.figure(figsize=(10,4.5));from mpl_toolkits.mplot3d.art3d import Poly3DCollection
 polys=mesh.triangles
 shades=np.clip(.60+.35*np.abs(mesh.face_normals[:,2]),0,1)
 colors=np.array([.31,.62,.69])[None,:]*shades[:,None]
 for n,elev,title in [(121,35,'Front / rigid forming face'),(122,-35,'Rear / projecting draft collar')]:
  ax=fig.add_subplot(n,projection='3d');ax.add_collection3d(Poly3DCollection(polys,facecolors=colors,edgecolor='none'))
  ax.set(xlim=(-125,125),ylim=(-125,125),zlim=(-20,30));ax.set_box_aspect((1,1,.20));ax.view_init(elev,-55);ax.axis('off');ax.set_title(title,fontsize=11)
 fig.suptitle('RF01 / two views of the same exported temporary tool');fig.tight_layout();fig.savefig(dest/'RF01_isolated_preview.png',dpi=150);plt.close(fig)
 bom={'all_custom_parts_temporary':True,'printed_parts':[{'file':paths[0].name,'stl':paths[1].name,'quantity':1,'material':p['material'],'print_orientation':'Flat front face on build plate, collar grows upward; smooth and line molding surfaces. Verify no support scars on molding plane.'}],
 'site_supplies':['0.05 mm PE release film and three matched removable contact patches','Two broad padded front battens, contractor-supplied stable brace','Removable protective hardware cover, no adhesive on moving stems','Supported repair substrate/backing and compatible repair/waterproofing system, permanent only after inspection'],
 'not_included':'No valve parts, anchors, permanent liner, divider form or metal escutcheon in this tool package','quote':'No form price obtained; not suitable for ordinary flat laser cutting.'}
 dump(dest/'BOM.json',bom);dump(dest/'RF01_SPEC.json',s);dump(dest/'CHECKS.json',record)
 print('RF01 source intersection checks:',results)
if __name__=='__main__':run()
