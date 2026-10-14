"""Axial relationships and exact intersections of the disclosed reference solids.

No captured hardware is adjusted. A CAD conflict is a result for the draft,
not proof of the dimensions or condition of the physical installation.
"""
from pathlib import Path
import json
import cadquery as cq
from rough_in import analyze_rough_in

ROOT=Path(__file__).resolve().parents[2]

def analyze_depth(d, manifest):
    parts={p['id']:p for p in manifest['parts']}
    shapes={id:cq.Shape.importBrep(str(ROOT/p['brep'])) for id,p in parts.items()}
    probes=['STUD-SW','STUD-NE','STUD-SW-NUT','STUD-NE-NUT','PLATE-INNER','VALVE-LOWER','VALVE-UPPER']
    cases={}
    for key,pose,label in [('factory','factory_location_mm','Original-wall trial'),('proposed','location_mm','Trial with added backing plate')]:
        placed={id:s.translate(tuple(parts[id][pose])) for id,s in shapes.items() if parts[id][pose] is not None}
        outer=placed['TRIM-OUTER'];rim=parts['TRIM-OUTER'][pose][2]
        ranges={id:[s.BoundingBox().zmin,s.BoundingBox().zmax] for id,s in placed.items()}
        collisions=[]
        for id in probes:
            volume=outer.intersect(placed[id]).Volume()
            collisions.append({'part':id,'against':'TRIM-OUTER','intersection_mm3':volume,
                'model_result':'FAIL' if volume>1e-6 else 'NO_SOLID_INTERSECTION',
                'physical_result':'UNRESOLVED','part_basis':parts[id]['evidence']})
        studs=[]
        for id,p in zip(['STUD-SW','STUD-NE'],d['studs_mm']):
            # Analytic line/solid intersection at the stud axis, not a bounding-box cavity.
            ray=cq.Edge.makeLine(cq.Vector(p[0],p[1],-100),cq.Vector(p[0],p[1],200))
            intervals=sorted([[e.BoundingBox().zmin,e.BoundingBox().zmax] for e in outer.intersect(ray).Edges()])
            roof=intervals[0][0] if intervals else None
            tip=ranges[id][1];nut=ranges[id+'-NUT']
            studs.append({'id':id,'axis_xy_mm':p[:2],'tip_z_mm':tip,'nut_z_mm':nut,
                'cover_material_on_axis_z_mm':intervals,'cover_rear_z_mm':roof,
                'local_cavity_from_rim_mm':roof-rim if roof is not None else None,
                'tip_to_cover_rear_clearance_mm':roof-tip if roof is not None else None,
                'nut_to_cover_rear_clearance_mm':roof-nut[1] if roof is not None else None,
                'note':'Signed axial gap at assumed axis; negative = overlap. Exact full-solid intersection is reported separately.'})
        cases[key]={'label':label,'cover_rim_z_mm':rim,'ranges_z_mm':ranges,'studs':studs,'collisions':collisions,
            'model_verdict':'FAIL' if any(c['model_result']=='FAIL' for c in collisions) else 'NO_REPORTED_SOLID_INTERSECTION',
            'physical_fit':'UNRESOLVED','captured_hardware_adjusted':False,
            'gasket_thickness_basis':'uncompressed placeholder; assembled compression and contact are unknown'}
    return {'revision':d['revision'],'units':'mm','datum':'Intact-stone fitted reference plane Z=0; +Z toward shower',
        'purpose':'Explain why the prior seated-cover visualization is not an assemblable repair',
        'cases':cases,'rough_in':analyze_rough_in(d),'factory_guide':{'source':'SRC-KOHLER-OLD-GUIDE p7; p8 adapter check; current guide steps8-12',
            'stud_max_from_finished_wall_mm':11.1125,'datum_confirmed_in_text':'finished wall, not front of yellow plate',
            'sequence':['Studs thread into valve','Inner plate and rear foam seat at finished wall','Nuts secure inner plate behind cover','Outer cover goes over inner plate with drain down','Handle assemblies secure cover via inner-plate hubs; correct adapters engage valve'],
            'applicability':'Applicable arrangement reference; actual installed revision and adjustment range must be checked. Added backing plate is not a manufacturer-approved detail.'},
        'limits':['All current Z values are conditional scan estimates or disclosed shape assumptions; no physical readings accepted.',
            'Foam compression, rear cavity shape, nut seats, valve collars and handle engagement remain unmeasured.',
            'A positive geometric gap is not a physical fit, support or water-performance pass.',
            'The captured scan, stud tip landmarks and valve pose remain unchanged. No shortening or relocation is specified.']}
