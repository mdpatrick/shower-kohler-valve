"""RF05 optional aggressive locator print; retain all RF03/RF04 source bytes."""
from pathlib import Path
import sys,json,math,hashlib,zipfile
import numpy as np
import cadquery as cq
import trimesh
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.fabrication.formwork_print import write_3mf,read_3mf_mesh
CFG=json.loads((ROOT/'canon/tab_shaft_trial_FS02.json').read_text());BASE=json.loads((ROOT/'canon/formwork_print_RF03.json').read_text())
OUT=ROOT/'deliverables/current/fabrication/FT02/tight-form-RF05';BUILD=ROOT/'build/FS02';PACK=OUT/'PRINT_ONE_SIZE'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def build():
    PACK.mkdir(parents=True,exist_ok=True);BUILD.mkdir(parents=True,exist_ok=True)
    src=ROOT/'deliverables/current/fabrication/FT02/formwork-print/SEND_TO_PRINTER/CAD_REFERENCE/RF03_D24_RELIEVED_mm.step'
    original=cq.importers.importStep(str(src)).translate((-120,-120,-8.05)).rotate((0,0,0),(1,0,0),180)
    obj=original
    for s in BASE['slots'].values():
        # Refill only the previous opening, across the existing 3 mm tab.
        fill=cq.Workplane('XY',origin=(*s['center_mm'],5.05)).slot2D(12,8).extrude(3)
        obj=obj.union(fill)
    a=np.array(CFG['trial']['A']['center_cover_xy_mm']);b=np.array(CFG['trial']['B']['center_cover_xy_mm']);angle=math.degrees(math.atan2(*(a-b)[::-1]))
    for k in 'AB':
        s=CFG['trial'][k];wp=cq.Workplane('XY',origin=(*s['center_cover_xy_mm'],4.05))
        wp=wp.circle(s['diameter_mm']/2) if s['type']=='round' else wp.slot2D(s['length_mm'],s['width_mm'],angle)
        obj=obj.cut(wp.extrude(5))
    obj=obj.clean();assert obj.val().isValid() and len(obj.val().Solids())==1
    # Only local tab opening material is allowed to differ.
    rois=[]
    for s in BASE['slots'].values():rois.append(cq.Workplane('XY',origin=(*s['center_mm'],5.049)).circle(11).extrude(3.002).val())
    roi=rois[0].fuse(rois[1]);delta=obj.val().cut(original.val()).fuse(original.val().cut(obj.val()))
    outside=delta.cut(roi).Volume();assert outside<.001
    rows=[]
    for d in CFG['trial']['outer_diameters_mm']:
        current=obj if d==240 else obj.intersect(cq.Workplane('XY',origin=(0,0,-30)).circle(d/2).extrude(50))
        p=current.rotate((0,0,0),(1,0,0),180).translate((d/2,d/2,8.05))
        name='RF05_EXPERIMENTAL_'+str(d).replace('.','p')+'_D24_RELIEVED_TIGHT_LOCATORS_mm'
        folder=PACK/('FULL_240' if d==240 else 'SMALL_192p55');folder.mkdir(exist_ok=True)
        stl=folder/(name+'.stl');step=folder/(name+'.step');mf=folder/(name+'.3mf')
        cq.exporters.export(p,str(step));cq.exporters.export(p,str(stl),tolerance=.01,angularTolerance=.03)
        m=trimesh.load(stl,force='mesh');write_3mf(m,mf,'RF05 experimental '+str(d)+' mm temporary form')
        rb=cq.importers.importStep(str(step)).val();mm=read_3mf_mesh(mf)
        assert rb.isValid() and len(rb.Solids())==1 and abs(rb.Volume()-p.val().Volume())<.01
        assert m.is_watertight and m.is_winding_consistent and len(m.split())==1 and m.volume>0
        assert mm.is_watertight and len(mm.split())==1 and np.allclose(mm.bounds,m.bounds,atol=1e-5)
        assert np.allclose(m.extents,[d,d,32],atol=.02) and abs(m.bounds[0,2])<.001
        rows.append({'diameter_mm':d,'overall_height_mm':32,'collar_max_depth_mm':24,'bounds_mm':m.bounds.tolist(),'solid_volume_mm3':rb.Volume(),
                     'STEP_valid_solids':1,'STL_closed_components':1,'3MF_mm_components':1,'volume_mesh_vs_STEP_fraction':abs(m.volume-rb.Volume())/rb.Volume(),
                     'files':[{'path':str(x.relative_to(OUT)),'sha256':sha(x),'bytes':x.stat().st_size} for x in [stl,mf,step]]})
    data={'revision':'RF05','status':CFG['status'],'source_baseline_sha256':sha(src),'protected_outside_tab_regions_difference_mm3':outside,
          'changed_volume_mm3':delta.Volume(),'lower_slot_angle_deg':angle,'parts':rows,'physical_fit_tested':False,'risk':CFG['risk']}
    (OUT/'geometry_checks.json').write_text(json.dumps(data,indent=2)+'\n')
    guide='''RF05 — EXPERIMENTAL TIGHT LOCATORS / TEMPORARY REPAIR FORM

Print ONE size, not all file formats.
FULL: diameter 240 mm, height 32 mm. About 250 x 250 mm usable bed with 5 mm brim.
SMALL: diameter 192.55 mm, height 32 mm. About 203 x 203 mm usable bed with 5 mm brim.
Both have the same 24 mm maximum relieved collar, 8 mm face and 3 mm tabs.

WHAT CHANGED
Upper-right A: round 6.5 mm hole.
Lower-left B: 9 x 6.5 mm slot along the line between the rods.
Tab bodies, control opening, collar, draft and rear reliefs match RF03/RF04.
This is a separate optional experiment; the existing PS01 files remain baseline.

PRINT
Use geometry-only 3MF (explicit mm) or STL (import as mm). STEP is CAD reference.
Do not scale to fit the bed. Files rest flat on the bed; collar points upward.
Use the printer's established unfilled PETG profile, 0.4 mm nozzle, 0.2 mm layers,
5 walls, 1.2 mm top/bottom skins, 25% infill and 5 mm brim as the PS01 starting setup.
Supports/raft off; inspect the slicer preview. G-code is printer-specific and absent.
Keep both small holes clean of brim and first-layer flare. Do not resize them in advance.

TRY IT
Remove the removable end nuts. The tabs fit around the shafts, never over the nuts.
Offer the form by hand. A tight print that binds is a failed trial: do not pull it
in with nuts. Keep the older loose-slot form available. Usual full-face seating,
independent padded bracing and removal checks still precede any repair material.
No new caliper survey is requested. Feedback can simply be which tab binds or is loose.

RISK
The owner accepts a 25–30% chance of a failed experiment. That is permission to
risk a remake, not a measured probability. Scans and actual print tolerances can
consume the small calculated gaps. This is not a permanent escutcheon, liner or
waterproofing approval. A successful dry fit does not establish shower-water sealing.
'''
    (PACK/'READ_FIRST.txt').write_text(guide)
    with zipfile.ZipFile(OUT/'RF05_EXPERIMENTAL_TIGHT_FORMS_BOTH_SIZES.zip','w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(PACK.rglob('*')):
            if path.is_file():z.write(path,str(path.relative_to(OUT)))
    print(json.dumps(data,indent=2))

if __name__=='__main__':build()
