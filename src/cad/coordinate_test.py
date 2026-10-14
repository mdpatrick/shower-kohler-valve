from pathlib import Path
import json,math
import cadquery as cq
import trimesh
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'build/coordinate_test';OUT.mkdir(parents=True,exist_ok=True)
profile=[(0,0),(100,0),(100,50),(90,60),(0,60)]
part=cq.Workplane('XY').polyline(profile).close().extrude(4).cut(cq.Workplane('XY').center(20,15).circle(5).extrude(4))
cq.exporters.export(part,str(OUT/'test.step'))
cq.exporters.export(part,str(OUT/'test.stl'),tolerance=.02,angularTolerance=.08)
re=cq.importers.importStep(str(OUT/'test.step'));bb=re.val().BoundingBox()
assert re.val().isValid() and len(re.solids().vals())==1
assert all(abs(a-b)<1e-6 for a,b in zip([bb.xlen,bb.ylen,bb.zlen],[100,60,4]))
assert not re.val().isInside(cq.Vector(20,15,2),1e-7)
assert re.val().isInside(cq.Vector(70,45,2),1e-7)
assert not re.val().isInside(cq.Vector(99,59,2),1e-7)
circles=[e for e in re.edges().vals() if e.geomType()=='CIRCLE']
assert len(circles)==2
for e in circles:
    c=e.arcCenter();assert abs(c.x-20)<1e-6 and abs(c.y-15)<1e-6 and abs(e.radius()-5)<1e-6
mesh=trimesh.load(OUT/'test.stl');assert max(abs(mesh.extents-[100,60,4]))<1e-5
report={'status':'PASS','units':'mm','part_bounds':[100,60,4],'hole_center':[20,15],'hole_diameter':10,
        'marker':'NE corner clipped from (100,50) to (90,60)','STEP_reimport_valid':True,
        'hole_position_and_radius_reimported':True,'STL_bounds_verified':True,'tessellation_linear_tolerance_mm':.02,
        'blender_mapping':'(X,-Z,Y)/1000 meters','browser_mapping':'(X,Y,Z)/1000 meters'}
(OUT/'cad_check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
