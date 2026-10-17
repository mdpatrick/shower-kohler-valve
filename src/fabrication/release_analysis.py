"""Scoped completion checks and reference assets for the selected fit-trial release."""
from pathlib import Path
import json, math, sys, hashlib
import numpy as np
import cadquery as cq
from shapely.geometry import Point,Polygon
from shapely.affinity import translate,rotate,affine_transform
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.fabrication.fit_trial import run as profiles,rr
from src.analysis.fit_trial_release import load_capture,slice_project,run as locator,read
from src.analysis.registration_trial import coeff

def dump(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n')
def run():
 d=read('canon/fit_trial_design.json');out=ROOT/d['output_directory'];locator();profiles(d,out)
 report=json.loads((out/'design_report.json').read_text());study=json.loads((out/'engineering/locator_evaluation.json').read_text())
 study['decision']=d['locator_decision']
 # This is a clearance budget, not an uncertainty certificate. Source shafts remain unchanged.
 study['allowance_budget']={
  'nominal_stud_major_mm':4.826,'basis':'1038645 identified as #10-24; nominal #10 thread crest 0.190 inch. Actual thread envelope is not measured.',
  'factory_radial_play_mm':(5.66-4.826)/2,
  'hole_candidates':[{'diameter_mm':x,'slot_length_mm':x+3,'custom_radial_play_mm':(x-4.826)/2,'custom_plus_factory_radial_play_mm':(x-4.826)/2+(5.66-4.826)/2,'requested_metal_cut_profile_mm':.13,'nominal_extra_foam_land_mm':1} for x in [6.4,7,8]],
  'plane_and_angle':'Factory hole plane is on a formed plate, forward of the new sheet. Its offset depends on compressed foam and bedding; source shafts vary with Z. No measured normal-axis relation permits exact XY copying.',
  'normal_disassembly':'Removing nuts/trim and retracting or removing studs can eliminate the enlarged-end insertion conflict. That is an ordinary plumber operation, not simulated evidence. Seated A-shaft overlap remains in the tested reference placement.',
  'alternative_anchor':'Swapping round and slot does not provide transverse relief along arbitrary pose differences. Enlarging/lengthening both sacrifices centering; final survey and old 112.05 mm spacing are retained separately.',
  'rotation_bound_example_deg':math.degrees(math.asin(min(1,((7-4.826)+.834)/113.213455914))),
  'limit':'Worst translation from summed hole play is a conservative geometric opportunity for motion, not an observed error. Combined translation/rotation is not claimed simultaneous. Rounded 15 mm tabs with 7 mm holes leave 4 mm side ligaments; structurally plausible in metal, but pose and landing dominate. Acrylic is brittle and no tab load/forced fitting is accepted.',
  'retention':'Tabs do not clamp in Z. Plain plate also needs sound support and correct factory clamping; positioning aid is removed. No permanent custom threaded or wall attachment.'}
 v,f=load_capture();tri=v[f];div=np.array(read('data/derived/resolved.json')['diverter_tip_mm'][:2])
 local=tri.copy();local[:,:,:2]-=div
 mask=(np.linalg.norm(local[:,:,:2],axis=2).min(1)<43)&(local[:,:,2].max(1)>0)
 polys=slice_project(local[mask],1,80);full=unary_union(polys)
 # Use the original raw contour for the diverter; distinguish stone contact outside from central swept hardware.
 aperture=Point(0,0).buffer(40,quad_segs=256)
 # All surface inside the 40 mm opening is cleared by definition. Inspect source protrusions outside separately.
 exterior=full.difference(aperture)
 study['diverter_assessment']={'selected_aperture_mm':80,'factory_cover_mm':98.425,'nominal_cover_overlap_mm':9.2125,
  'scoped_source_pieces':len(polys),'surface_outside_aperture_z1_to80_area_mm2':exterior.area,
  'interpretation':'Outside-aperture captured material is not automatically hardware: this neighborhood contains stone. The source scan does not show the removed rear factory plate or its gasket.',
  'factory_reference':'1190382-2-A steps 8-9 show a rear plate assembly attached to valve with screws, then a larger cover with bottom notch. Exterior OBJ contains cover and handles only. Do not treat cover overlap as measured seal support.',
  'assembly_path':'Remove cover/handle/rear plate as necessary; slip custom ring over exposed valve; reinstall factory rear plate on top. The rear flange need NOT pass through the 80 mm aperture.',
  'decision':'Keep 124/80 as sacrificial trial nominal. No dimensioned rear-contact evidence establishes a known clash; actual full rear contact and screw engagement are explicit trial checks. If its contact crosses the aperture edge, do not seal: mark the overlap and revise aperture locally or smaller, checking the captured valve. Do not enlarge blindly.',
  'remaining_checks':['Rear contact fully lands on custom metal','Ring clears installed body and permits screw/tool access','No rocking or loss of factory support','Gap to main remains positive without offsetting covers']}
 ap=rr(d['main']['aperture_width_mm'],d['main']['aperture_height_mm'],d['main']['aperture_radius_mm']);foam=d['foam']
 fo=rr(foam['outer_width_mm'],foam['outer_height_mm'],foam['outer_corner_radius_mm']);fi=rr(foam['outer_width_mm']-12,foam['outer_height_mm']-12,foam['outer_corner_radius_mm']-6)
 itc=study['transforms']['inner_outline_to_cover_xy_up']['translation_mm'];band=translate(fo.difference(fi),*itc)
 sensitivity=[]
 for dx,dy,angle in [(0,0,0),(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(1,1,1)]:
  moved=translate(rotate(band,angle,origin=(0,0)),dx,dy)
  overlap=ap.intersection(moved).area
  sensitivity.append(dict(relative_offset_mm=[dx,dy],rotation_deg=angle,foam_area_over_opening_mm2=overlap,scope='Scenario only; no measured bound or accepted alignment tolerance'))
 study['gasket_sensitivity']=sensitivity
 study['measurement_policy']='R006 planar owner selections govern; support approximations from credible local evidence. No new owner measurement requested. Installed tip distances remain 3D. Remaining observations belong to the physical fit trial.'
 vendor=d.get('vendor_variant')
 if vendor:
  baseline=vendor['baseline_metal_thickness_mm']
  study['vendor_thickness_check']={
   'variant':vendor['id'],'nominal_mm':d['stocks'][0]['thickness_mm'],
   'baseline_mm':baseline,'nominal_delta_mm':d['stocks'][0]['thickness_mm']-baseline,
   'metal_range_mm':vendor['metal_stock_range_mm'],'clear_range_mm':vendor['clear_stock_range_mm'],
   'added_depth_delta_vs_baseline_mm':{k:[x-baseline for x in vendor[k+'_stock_range_mm']] for k in ['metal','clear']},
   'metal_relative_bending_stiffness_same_alloy':[float((t/baseline)**3) for t in vendor['metal_stock_range_mm']],
   'clearance_scope':'The full-source plain-aperture sweep Z=1..80 includes the entire sheet thickness range 1.27..1.73 at the illustrative 1 mm stand-off. It has no projected in-opening conflict. Z=0 seating still encounters captured boundary topography; actual stable support controls bedding. No fixed tabs exist to change interference.',
   'gasket_and_XY':'Finished XY geometry is unchanged: full nominal 6 mm foam width plus 1 mm inward reserve. Thickness does not fix an unverified actual footprint or centering. Separate acrylic kerf paths target the same finished XY.',
   'engagement_and_support':'No handle engagement allowance has been measured. The selected 1.52 mm metal is 0.004 mm below the 1.524 mm baseline, but delivered thickness and bedding must be checked with the factory hubs. Acrylic can differ from steel by up to 0.37 mm using the two catalog extremes. Thin acrylic is only a contact/clearance aid, not a stiffness or water test.'}
 dump(out/'engineering/locator_evaluation.json',study)
 report['complete_local_checks']='engineering/locator_evaluation.json';report['measurement_revision']='R006'
 report['selected_main']='PLAIN_WITH_REMOVABLE_CONCENTRIC_GUIDE';report['current_placement']=study['transforms']
 report['readiness']={'fabrication_fit_trial_files':'See audit.json and docs/validation/adversarial_review_FT02.json for current export and handoff checks','private_ponoko_quotes':'AUTHORIZED selected custom files only','purchase':'NOT AUTHORIZED','physical_fit':'NOT PERFORMED','permanent_use':'NOT ESTABLISHED'}
 # Measured reference update: correct TWO mounting bores and accepted local centers.
 layout=read('canon/measurements.json')['active_locating_layout'];ref=out/'reference';ref.mkdir(exist_ok=True)
 w,h,r=foam['outer_width_mm'],foam['outer_height_mm'],foam['outer_corner_radius_mm'];depth=15.44-6
 def outline(w,h,r,z):
  return cq.Workplane('XY').rect(w-2*r,h-2*r).vertices().circle(r) if False else cq.Workplane('XY').rect(w,h).extrude(z).edges('|Z').fillet(r-1e-6)
 outer=outline(w,h,r,depth)
 cavity=outline(w-8,h-8,r-4,depth-1)
 plate=outer.cut(cavity)
 upper=[0,40.32];lower=[0,40.32-80.04]
 for center,diam in [(upper,48.46),(lower,50),*[(p,5.66) for p in layout['outline_centered_xy_up_mm'].values()]]:
  plate=plate.cut(cq.Workplane('XY').center(*center).circle(diam/2).extrude(depth+2).translate((0,0,-1)))
 for ext in ['step','stl']:cq.exporters.export(plate,str(ref/('R006_FACTORY_INNER_REFERENCE.'+ext)))
 dump(ref/'R006_FACTORY_INNER_REFERENCE.json',{'NOT_FOR_MANUFACTURING':True,'measurement_revision':'R006','mounting_holes':layout['outline_centered_xy_up_mm'],'hole_diameter_mm':5.66,'control_centers_mm':{'U':upper,'L':lower},'limits':'Outer width/height and upper opening from owner. R40, 1 mm web, 4 mm rim, lower D50 and position remain reconstructed form, not a new factory part. Overall metal envelope 9.44 is derived from uncompressed stack minus approximate 6 mm foam. Exact mounting plane depth is NOT measured. Two small holes only. Reference coordinates outline-centered; transform to cover recorded separately.'})
 report['sources_sha256'].update({str((ref/'R006_FACTORY_INNER_REFERENCE.json').relative_to(ROOT)):hashlib.sha256((ref/'R006_FACTORY_INNER_REFERENCE.json').read_bytes()).hexdigest(),'src/fabrication/release_analysis.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
 dump(out/'design_report.json',report)
 print('Selected FT02 profiles and bounded completion study generated.')
if __name__=='__main__':run()
