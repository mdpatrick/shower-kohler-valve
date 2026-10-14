"""One-time provisional feature transcription. Does not run during normal build."""
from pathlib import Path
import json,numpy as np
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'canon/features.json'
if p.exists():raise SystemExit('Refusing to replace existing feature canon')
reg=json.loads((ROOT/'data/derived/registration.json').read_text());inv=np.linalg.inv(np.array(reg['raw_to_installed_mm']))
def raw(points):
    return [(inv@np.array([(x-1100)*280/2200,40+(1100-y)*280/2200,0,1]))[:3].tolist() for x,y in points]
features=[]
def add(id,name,kind,points,certainty='observed',note='',include=True):
    features.append({'id':id,'name':name,'component':'wall','state':'as_observed_at_capture','kind':kind,'status':'scan-derived' if certainty=='observed' else 'unknown',
      'source':'SCAN-WALL','source_view':'build/scan_inspection/wall_detail.png','view_revision':'R001',
      'annotation_pixels':points,'projected_contour_raw':raw(points),'geometry':'polygon' if kind not in ('grout','reference') else 'polyline',
      'include_in_coverage':include,'trace_allowance_mm_at_R001':1.5,'trace_basis':'approximately 12 pixels at conditional 280mm/2200px; edge blur/selection allowance only, not absolute scan accuracy',
      'depth_mm':None,'note':note or 'Visible projected boundary; concealed surfaces and soundness not established.'})
add('OPEN-MAIN','Irregular stacked-valve wall opening','opening',[(790,435),(980,425),(1190,442),(1385,452),(1500,475),(1585,562),(1650,610),(1690,750),(1680,945),(1680,1130),(1720,1225),(1800,1350),(1750,1450),(1620,1550),(1450,1710),(940,1710),(855,1670),(735,1590),(560,1410),(550,1380),(625,1280),(635,1120),(650,990),(690,805),(730,610)])
add('CUT-01','Top-left raised cut / missing arris','damage',[(778,435),(790,409),(818,382),(849,377),(870,404),(919,407),(902,431),(827,449)])
add('CUT-02','Upper horizontal overcut above opening','damage',[(1025,382),(1130,389),(1200,395),(1340,401),(1340,411),(1200,408),(1120,402),(1030,394)],'uncertain','Dark thin line may be a saw mark or texture/shadow; confirm at marked location.')
add('CUT-03','Top-right cut extension','damage',[(1385,443),(1483,455),(1588,471),(1595,488),(1515,492),(1450,471)])
add('CUT-04','Left lower overcut / chipped cusp','damage',[(575,1328),(550,1360),(540,1391),(560,1425),(602,1461),(623,1450),(572,1405),(580,1376)])
add('CUT-05','Right lower overcut / chipped cusp','damage',[(1730,1260),(1760,1297),(1807,1345),(1810,1373),(1772,1416),(1730,1445),(1715,1420),(1750,1371)])
add('CUT-06','Bottom missing / recessed stone edge','damage',[(838,1660),(947,1688),(1110,1687),(1260,1698),(1447,1680),(1454,1727),(1390,1765),(1260,1730),(1050,1725),(920,1736),(870,1710)])
add('CUT-07','Right edge line toward adjacent grout','damage',[(1792,1342),(1828,1328),(1824,1368),(1803,1386)],'uncertain','Possible cut/texture at grout; inspect rather than assume hidden damage ends at the opening.')
add('GROUT-01','Adjacent vertical grout recess','grout',[(1817,0),(1820,600),(1817,1200),(1810,1800),(1810,2200)],note='Grout joint crosses candidate outer land. Width/depth, soundness and compatible sealing unresolved.',include=False)
add('MARK-01','Former trim / residue arc below opening','reference',[(650,1570),(750,1740),(1000,1830),(1250,1855),(1530,1770),(1750,1560)],'uncertain','Visible arc is not automatically a gouge; excluded from required damage coverage pending physical identification.',False)
for id,info in reg['landmarks_installed_mm'].items():
    features.append({'id':id,'component':'valve','state':'as_observed_at_capture','kind':'landmark','source':'SCAN-WALL','status':'scan-derived','point_raw':info['point'],'uncertainty_mm':None,'note':info['purpose']})
features += [{'id':'OPEN-LOWER-AUX','component':'separate lower control','state':'as_observed_at_capture','kind':'context opening','source':'SCAN-WALL','status':'scan-derived','include_in_coverage':False,'note':'Separate lower opening/control visible in overview. Outside stacked-trim repair scope; retain as nearby obstruction/context, not the lower stacked control.'},
             {'id':'PLATE-INNER','component':'inner plate','state':'manufacturer_intended','kind':'reference reconstruction','status':'inferred','source':['SRC-KOHLER-OLD-GUIDE','SCAN-PLATE-1','SCAN-PLATE-2'],'note':'Form lead only. Plate scans cannot establish outline, back face, thickness or hole coordinates.'},
             {'id':'GASKET-01','component':'factory gasket','state':'manufacturer_intended','kind':'contact path','status':'unknown','source':'SRC-KOHLER-OLD-GUIDE','note':'Contact path/free thickness/notches/condition require inspection. Rendered capsule is an assumption.'},
             {'id':'TRIM-OUTER','component':'outer trim','state':'manufacturer_intended','kind':'reference reconstruction','status':'manufacturer nominal','source':'SRC-KOHLER-SPEC','note':'Candidate 7.25in diameter; actual identity not yet verified.'},
             {'id':'CUSTOM-01','component':'custom candidate','state':'proposed_provisional','kind':'design candidate','status':'inferred','note':'Diameter computed from traced damage + exploratory land. Aperture derived conservatively from visible protrusion envelope; requires gasket and service checks.'}]
p.write_text(json.dumps({'schema_version':1,'revision':'R001','trace_completeness':'First visible-feature inventory only. Faint/occluded cuts and post-scan changes unresolved; do not claim every physical defect has been captured.','features':features},indent=2)+'\n')
