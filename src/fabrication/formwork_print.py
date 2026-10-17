"""RF03: isolated temporary-tool CAD, portable print formats and numeric audit."""
from pathlib import Path
import sys, json, math, hashlib, zipfile
import xml.etree.ElementTree as ET
import numpy as np
import cadquery as cq
import trimesh
from shapely.geometry import Point, LineString, shape
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.fabrication.repair_form import cap
from src.fabrication.fit_trial import rr
from src.analysis.tab_refinement import load_local, slice_project

OUT=ROOT/'deliverables/current/fabrication/FT02/formwork-print'
PACK=OUT/'SEND_TO_PRINTER'
BUILD=ROOT/'build/FT02/formwork_print'
CFG=json.loads((ROOT/'canon/formwork_print_RF03.json').read_text())
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,o):Path(p).write_text(json.dumps(o,indent=2)+'\n')

def tab_shapes():
    tabs=[];holes=[]
    for s in CFG['slots'].values():
        p=np.array(s['center_mm']);side=np.sign(p[0]);inner=p-[side*2,0];root=np.array([side*67,p[1]])
        tabs.append(LineString([root,inner]).buffer(8,quad_segs=128))
        holes.append(LineString([p- [2,0],p+[2,0]]).buffer(4,quad_segs=128))
    return unary_union(tabs),unary_union(holes)

def make_form(var):
    dep=var['depth_mm'];z=CFG['forming_plane_installed_z_mm'];t=CFG['panel_thickness_mm']
    w,h=CFG['collar_outer_front_mm'];dr=dep*math.tan(math.radians(CFG['draft_deg']))
    outer=cq.Solid.makeLoft([cap(w-2*dr,h-2*dr,z-dep).val(),cap(w,h,z).val()])
    inner=cq.Solid.makeLoft([cap(w-4-2*dr,h-4-2*dr,z-dep-.02).val(),cap(w-4,h-4,z+.02).val()])
    collar=cq.Workplane('XY').newObject([outer.cut(inner)])
    if var['rear_reliefs']:
        for x0,y0,x1,y1 in CFG['rear_relief_boxes_xy_mm']:
            cutter=cq.Workplane('XY',origin=((x0+x1)/2,(y0+y1)/2,z-dep-1)).rect(x1-x0,y1-y0).extrude(dep-12+1).edges('|Z').fillet(2)
            collar=collar.cut(cutter)
    panel=cq.Workplane('XY',origin=(0,0,z)).circle(120).extrude(t).cut(cap(w-4,h-4,z-1).extrude(t+2))
    obj=panel.union(collar)
    for s in CFG['slots'].values():
        p=np.array(s['center_mm']);side=np.sign(p[0]);inner=p-[side*2,0];root=np.array([side*67,p[1]])
        obj=obj.union(cq.Workplane('XY',origin=(0,0,z+t-3)).center(*(root+inner)/2).slot2D(abs(root[0]-inner[0])+16,16).extrude(3))
    for s in CFG['slots'].values():
        obj=obj.cut(cq.Workplane('XY',origin=(0,0,z+t-4)).center(*s['center_mm']).slot2D(12,8).extrude(5))
    return obj.clean()

def write_3mf(mesh,path,name):
    ET.register_namespace('',NS)
    root=ET.Element('{'+NS+'}model',{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    ET.SubElement(root,'{'+NS+'}metadata',{'name':'Title'}).text=name
    resources=ET.SubElement(root,'{'+NS+'}resources')
    obj=ET.SubElement(resources,'{'+NS+'}object',{'id':'1','type':'model','name':name})
    node=ET.SubElement(obj,'{'+NS+'}mesh');verts=ET.SubElement(node,'{'+NS+'}vertices');faces=ET.SubElement(node,'{'+NS+'}triangles')
    for v in mesh.vertices:ET.SubElement(verts,'{'+NS+'}vertex',{k:format(float(x),'.9g') for k,x in zip(('x','y','z'),v)})
    for f in mesh.faces:ET.SubElement(faces,'{'+NS+'}triangle',{k:str(int(x)) for k,x in zip(('v1','v2','v3'),f)})
    ET.SubElement(ET.SubElement(root,'{'+NS+'}build'),'{'+NS+'}item',{'objectid':'1'})
    files={'[Content_Types].xml':b'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>',
      '_rels/.rels':b'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model"/></Relationships>',
      '3D/3dmodel.model':ET.tostring(root,encoding='utf-8',xml_declaration=True)}
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as zf:
        for n,b in files.items():
            zi=zipfile.ZipInfo(n,(2026,10,17,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zf.writestr(zi,b)

def read_3mf_mesh(path):
    with zipfile.ZipFile(path) as zf:
        assert zf.testzip() is None
        root=ET.fromstring(zf.read('3D/3dmodel.model'))
        assert root.get('unit')=='millimeter'
        objects=root.findall('{'+NS+'}resources/{'+NS+'}object')
        assert len(objects)==1 and objects[0].get('type')=='model'
        items=root.findall('{'+NS+'}build/{'+NS+'}item')
        assert len(items)==1 and items[0].get('objectid')==objects[0].get('id') and items[0].get('transform') is None
        verts=objects[0].findall('{'+NS+'}mesh/{'+NS+'}vertices/{'+NS+'}vertex')
        tris=objects[0].findall('{'+NS+'}mesh/{'+NS+'}triangles/{'+NS+'}triangle')
        return trimesh.Trimesh(vertices=[[float(v.get(k)) for k in ('x','y','z')] for v in verts],faces=[[int(t.get(k)) for k in ('v1','v2','v3')] for t in tris])

def mass_estimate(var,face_t):
    # Geometry integration, NOT a slicer. Five 0.45 mm wall paths, 1.2 mm skins.
    # Skins conservatively include any surface disappearing within 1.2 mm above/below.
    tabs,holes=tab_shapes();w,h=CFG['collar_outer_front_mm'];dz=.2
    base=Point(0,0).buffer(120,quad_segs=256).difference(rr(w-4,h-4,(w-4)/2))
    profiles=[]
    from shapely.affinity import translate
    reliefs=unary_union([translate(rr(x1-x0,y1-y0,2),xoff=(x0+x1)/2,yoff=(y0+y1)/2) for x0,y0,x1,y1 in CFG['rear_relief_boxes_xy_mm']])
    for zp in np.arange(.1,face_t+var['depth_mm'],dz):
        if zp<face_t:
            poly=base.union(tabs).difference(holes) if zp<3 else base
        else:
            depth=zp-face_t;dr=depth*math.tan(math.radians(1))
            poly=rr(w-2*dr,h-2*dr,(w-2*dr)/2).difference(rr(w-4-2*dr,h-4-2*dr,(w-4-2*dr)/2))
            if var['rear_reliefs'] and depth>12:poly=poly.difference(reliefs)
        profiles.append(poly)
    vol=0
    for i,p in enumerate(profiles):
        core=p.buffer(-2.25)
        for j in range(i-6,i+7):
            if j<0 or j>=len(profiles):core=Point().buffer(0);break
            core=core.intersection(profiles[j])
        vol+=(p.area-.75*core.area)*dz
    return {'method':'Approximate cross-section integration: 5 x 0.45 mm walls, 1.2 mm skins, 25% infill. No printer toolpath/timing simulation.', 'body_mm3':vol,'body_grams_at_1_30':vol/1000*1.30,'planning_range_grams_with_brim_purge':[math.floor(vol/1000*1.30*.9/10)*10, math.ceil((vol/1000*1.30*1.2+15)/10)*10]}

def build():
    PACK.mkdir(parents=True,exist_ok=True);BUILD.mkdir(parents=True,exist_ok=True)
    (PACK/'CAD_REFERENCE').mkdir(exist_ok=True);(PACK/'OPTIONAL_DEEPER').mkdir(exist_ok=True)
    parts=[]
    for var in CFG['variants']:
        obj=make_form(var);assert obj.val().isValid() and len(obj.val().Solids())==1
        raw=BUILD/('RF03_'+var['id']+'_installed.stl');cq.exporters.export(obj,str(raw),tolerance=.01,angularTolerance=.03)
        printobj=obj.rotate((0,0,0),(1,0,0),180).translate((120,120,8.05))
        stem='PRINT_ONE_RF03_D12' if var['recommended'] else 'PRINT_INSTEAD_RF03_D24_RELIEVED'
        dest=PACK if var['recommended'] else PACK/'OPTIONAL_DEEPER'
        stl=dest/(stem+'.stl');step=PACK/'CAD_REFERENCE'/('RF03_'+var['id']+'_mm.step');mf=dest/(stem+'.3mf')
        cq.exporters.export(printobj,str(stl),tolerance=.01,angularTolerance=.03)
        cq.exporters.export(printobj,str(step))
        mesh=trimesh.load(stl,force='mesh');assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1 and mesh.volume>0
        assert abs(mesh.bounds[0,2])<.001 and np.allclose(mesh.extents,[240,240,8+var['depth_mm']],atol=.02)
        rb=cq.importers.importStep(str(step)).val();assert rb.isValid() and len(rb.Solids())==1 and abs(rb.Volume()-obj.val().Volume())<.02
        write_3mf(mesh,mf,'RF03 '+var['id']+' temporary repair form; print one only')
        rm=read_3mf_mesh(mf);assert rm.is_watertight and len(rm.split())==1 and np.allclose(rm.bounds,mesh.bounds,atol=.00001)
        assert abs(rm.volume-mesh.volume)<.02
        oldp=ROOT/'deliverables/current/fabrication/FT02/tab-refinement'/('RF02_'+var['id']+'_TABBED_REMOVABLE_FORM_STUDY_NOT_RELEASED.step')
        old=cq.importers.importStep(str(oldp)).val();vol=rb.Volume()
        # The molding face and complete rear collar must be geometrically unchanged.
        rearhalf=cq.Workplane('XY',origin=(0,0,-40)).box(300,300,40.05,centered=(True,True,False)).val()
        a=old.intersect(rearhalf);b=obj.val().intersect(rearhalf)
        rear_delta=a.cut(b).Volume()+b.cut(a).Volume();assert rear_delta<.01
        row={'id':var['id'],'recommended':var['recommended'],'dimensions_mm':[240,240,8+var['depth_mm']], 'panel_mm':8,'collar_depth_mm':var['depth_mm'],'continuous_collar_mm':12,
          'solid_volume_mm3':vol,'solid_mass_upper_bound_g_at_density_1_30':vol/1000*1.30,'old_solid_volume_mm3':old.Volume(), 'CAD_volume_reduction_percent':100*(1-vol/old.Volume()),
          'approximate_print':mass_estimate(var,8),'old_12mm_face_same_print_settings_estimate':mass_estimate(var,12),
          'STEP_valid_connected_solids':1,'STL_watertight_connected_components':1,'3MF_valid_connected_components':1,'3MF_unit':'millimeter','3MF_has_machine_settings':False,
          'STEP_STL_volume_difference_percent':100*abs(vol-mesh.volume)/vol,'rear_collar_symmetric_difference_mm3':rear_delta,
          'files':[{ 'path':str(p.relative_to(PACK)),'sha256':sha(p),'bytes':p.stat().st_size} for p in [stl,mf,step]], 'triangles':len(mesh.faces)}
        parts.append(row)
    dump(OUT/'geometry_checks.json',{'revision':'RF03','scope':'Geometry/export checks; not physical fit or mechanical certification','parts':parts,'config_sha256':sha(ROOT/'canon/formwork_print_RF03.json')})
    print(json.dumps(parts,indent=2))

def check_capture():
    prev,v,f=load_local();alltri=v[f];mn,mx=alltri.min(1),alltri.max(1)
    local=alltri[(mx[:,0]>-125)&(mn[:,0]<125)&(mx[:,1]>-125)&(mn[:,1]<125)]
    mask=np.zeros(len(local),dtype=bool);visible=[]
    prior=ROOT/'build/FT02/tab_refinement'
    # Recreate diagnostic cache only when needed. No accepted source is rewritten.
    if not (prior/'footprints.json').exists():
        from src.analysis.tab_refinement import probe
        probe()
    foot=json.loads((prior/'footprints.json').read_text());probe=json.loads((prior/'probe.json').read_text())
    for k,p in prev['centers'].items():
        m=np.all(np.linalg.norm(local[:,:,:2]-p,axis=2)<11,axis=1);mask|=m
        visible.extend(slice_project(local[m],0,probe['rods'][k]['shaft_only_z_mm'][1]))
    bare=unary_union(slice_project(local[~mask],0,80)+visible+[shape(foot[k]['envelope']) for k in ['A','B']])
    tabs,holes=tab_shapes();inside=rr(114.35,141.10,57.175);added=tabs.difference(holes).intersection(inside)
    checks=[]
    for label,surf in [('new_tabs_seated_z5_05_to8_05',unary_union(slice_project(local,5.05,8.05))),('nut_removed_forward_path_5mm_conditional_envelope',bare)]:
        hit=added.intersection(surf)
        checks.append({'case':label,'overlap_mm2':hit.area});assert hit.area<.01
    result={'revision':'RF03','checks':checks,'status':'PASS_IN_CAPTURED_SCOPE',
      'limits':['Rod-end nuts must be removed before insertion.','Hidden rod region uses inferred 5 mm diagnostic envelope, not a measured diameter or error bound.','Full forming-face seating, stiffness under actual bracing, unseen geometry and release remain physical checks.','Rear collars match RF02 exactly; RF02 diagnostic collar checks still apply; no claim of global attached-scan registration.'],
      'source':{'RF02_analysis_sha256':sha(ROOT/'deliverables/current/fabrication/FT02/tab-refinement/analysis.json'),'registration_sha256':sha(ROOT/'data/derived/registration.json')}}
    dump(OUT/'capture_checks.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':
    if '--capture' in sys.argv:check_capture()
    else:build()
