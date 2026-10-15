"""Credible exterior display from official Kohler CAD; custom meshes from F005 STEP master."""
from pathlib import Path
import bpy, json, math, sys
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'deliverables/current/fabrication/F005';CACHE=ROOT/'data/derived/fabrication_F005'
d=json.loads((CACHE/'design.json').read_text());a=json.loads((CACHE/'analysis.json').read_text());r=json.loads((ROOT/'data/derived/resolved.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/f"deliverables/current/blender/installation_{r['revision']}_DRAFT.blend"))
source=bpy.context.scene
scene=bpy.data.scenes.new('F005 | paired escutcheons');bpy.context.window.scene=scene
scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=40;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=6
scene.render.resolution_x=1250;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.world=bpy.data.worlds.new('F005 neutral studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.14,.17,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.3
C={}
def coll(name):
 if name not in C:
  c=bpy.data.collections.new('F005 '+name);scene.collection.children.link(c);C[name]=c
 return C[name]
def xyz(p):return Vector((p[0]/1000,-p[2]/1000,p[1]/1000))
def move(o,name):
 for old in list(o.users_collection):old.objects.unlink(o)
 coll(name).objects.link(o)
B=Matrix(((.001,0,0,0),(0,0,-.001,0),(0,.001,0,0),(0,0,0,1)))
def mat(name,color,metal=0,rough=.4):
 m=bpy.data.materials.new('F005 '+name);m.diffuse_color=(*color,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
 if metal:
  if 'Anisotropic IOR Level' in b.inputs:b.inputs['Anisotropic IOR Level'].default_value=.35
 return m
steel=mat('satin stainless concept',(.35,.39,.43),.9,.32);nickel=mat('Kohler BN color approximation',(.45,.41,.34),.85,.29);innerMat=mat('measured inner plate',(.48,.49,.48),.75,.42);foamMat=mat('foam approximate',(.16,.13,.16),0,.8);warning=mat('observed stud conflict',(.75,.06,.025),.1,.4)
def stl(path,name,where,pos=(0,0,0),material=None):
 bpy.ops.wm.stl_import(filepath=str(path),forward_axis='Y',up_axis='Z');o=bpy.context.object;o.name='F005 '+name;o.data.transform(B);o.location=xyz(pos);move(o,where)
 if material:o.data.materials.clear();o.data.materials.append(material)
 o['evidence']='CAD master F005' if not name.startswith('KOHLER') else 'Official Kohler exterior mesh; hidden interfaces unverified'
 for face in o.data.polygons:face.use_smooth=False
 return o
# Link preserved sources into this scene. No transform changes.
rawcoll=bpy.data.collections.get('00A_SOURCE_WALL_FULL');scene.collection.children.link(rawcoll)
observed=coll('Observed unchanged')
for o in bpy.data.collections['01_OBSERVED_WALL'].objects:observed.objects.link(o)
# A distinct cosmetic wall copy omits captured valve/stud triangles inside openings.
# The full scan is retained unchanged in Observed and source collections.
mainpoly=next(f['contour_mm'] for f in r['features'] if f['id']=='OPEN-MAIN');divpoly=d['diverter_damage_trace']['contour_installed_mm']
def inside(p,poly):
 x,y=p;hit=False
 for (x1,y1),(x2,y2) in zip(poly,poly[1:]+poly[:1]):
  if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:hit=not hit
 return hit
for source_obj in list(observed.objects):
 obj=source_obj.copy();obj.data=source_obj.data.copy();obj.name='F005 APPEARANCE wall only | captured hardware excluded';coll('Appearance wall only').objects.link(obj)
 import bmesh
 bm=bmesh.new();bm.from_mesh(obj.data);remove=[]
 for f in bm.faces:
  p=obj.matrix_world@f.calc_center_median();xy=(p.x*1000,p.z*1000)
  if inside(xy,mainpoly) or inside(xy,divpoly):remove.append(f)
 bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(obj.data);bm.free()
 obj['limitation']='Cosmetic derivative only: hardware hidden, not adjusted. Use Observed unchanged for actual captured condition.'
# Custom pairs in exact installed XY; low-depth SS060 is illustrated.
custom={}
for p in d['parts']:
 m=next(m for m in a['parts'] if m['id']==p['id']+'-SS060')
 o=stl(OUT/m['stl'],p['id'],'Pair '+p['id'][-1]+' custom',(*p['center_mm'],1),steel);o['CAD_source']=m['step'];o['assumed_seal_gap_mm']=1;custom[p['id']]=o
nw=2.524;angle=math.radians(r['trim_in_plane_rotation_deg']);trimcenter=r['trim_center_mm']
nominal=[]
for comp in a['manufacturer_components']:
 main=comp['model']=='T14489-4';pos=(*trimcenter,nw) if main else (*r['diverter_tip_mm'][:2],nw)
 o=stl(ROOT/comp['stl'],f"KOHLER {comp['model']} component {comp['index']}",'Official exterior appearance',pos,nickel)
 if main:o.rotation_euler[1]=-angle
 for f in o.data.polygons:f.use_smooth=True
 o['state']='Conditional corrected appearance; hardware adjustment and mating are NOT demonstrated';o['units_basis']='Official inch mesh *25.4 to mm; mm to Blender meters once';nominal.append((o,comp,main))
# Free measured inner reference and separate foam scenario.
mi=next(m for m in a['parts'] if m['id']=='REF-INNER');inner=stl(OUT/mi['stl'],'INNER measured envelope','Measured loose parts',(*r['inner_center_mm'],6),innerMat)
inner['status']=mi['limitation'];inner['overall_free_envelope_mm']=15.44
mc=next(m for m in a['parts'] if m['id']=='REF-COVER');cv=stl(OUT/mc['stl'],'COVER measured scenario','Measured loose cover',(0,39.95,0),nickel);cv['status']=mc['limitation']
# Foam comes from the actual front outline only as a transparent assumption in diagrams;
# physical footprint has not been measured. Build a curve band for exploded order.
def ring_mesh(name,points,width,height,pos,where,material):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='2D';cu.fill_mode='BOTH';cu.extrude=height/2000
 # Rounded-rectangle band generated with polyline outside and reversed inside.
 for coords in points:
  sp=cu.splines.new('POLY');sp.points.add(len(coords)-1)
  for v,p in zip(sp.points,coords):v.co=(p[0]/1000,p[1]/1000,0,1)
  sp.use_cyclic_u=True
 ob=bpy.data.objects.new(name,cu);coll(where).objects.link(ob);ob.rotation_euler[0]=math.pi/2;ob.location=xyz(pos);ob.data.materials.append(material);return ob
# Use an explicit foam scenario only in the exploded view; rear footprint remains unmeasured.
fm=next(m for m in a['parts'] if m['id']=='REF-FOAM-SCENARIO')
foam=stl(OUT/fm['stl'],'EXPLODED foam path UNKNOWN','Exploded A',(*r['inner_center_mm'],48),foamMat);foam['status']=fm['limitation']
# Exploded custom, measured plate, nuts, official cover, bonnets and handles.
for id in ['MAIN-A','DIV-A']:
 o=custom[id];cp=o.copy();cp.data=o.data;cp.name='F005 EXPLODED '+id;coll('Exploded A').objects.link(cp);cp.location.y-=.025;cp['display_offset_mm']=25
cp=inner.copy();cp.data=inner.data;cp.name='F005 EXPLODED measured inner';coll('Exploded A').objects.link(cp);cp.location.y-=.08;cp['display_offset_mm']=80
for id,point in zip(['SW','NE'],r['studs_mm']):
 old=bpy.data.objects['STUD-'+id+'-NUT'];cp=old.copy();cp.data=old.data;cp.name='F005 EXPLODED nut '+id;coll('Exploded A').objects.link(cp);cp.location=xyz((point[0],point[1],110));cp['status']='Illustrative nut; actual seat/height unmeasured'
for o,comp,main in nominal:
 cp=o.copy();cp.data=o.data;cp.name='F005 EXPLODED '+o.name;coll('Exploded A').objects.link(cp)
 idx=comp['index'];off=(140 if idx==0 else 195 if main and idx in [3,4] or not main and idx==1 else 245) if main else (100 if idx==0 else 150 if idx==1 else 190)
 cp.location.y-=off/1000;cp['display_offset_mm']=off
# As-found conflict overlays preserve captured tip coordinates.
for id in ['STUD-SW','STUD-NE']:
 old=bpy.data.objects[id];cp=old.copy();cp.data=old.data.copy();cp.name='F005 AS_FOUND '+id;coll('Depth diagnostic').objects.link(cp);cp.data.materials.clear();cp.data.materials.append(warning)
# Cameras and broad lights. Vertical order is scan-derived, not rearranged side by side.
def camera(name,loc,target,span):
 cd=bpy.data.cameras.new('F005 '+name);o=bpy.data.objects.new('F005 '+name,cd);coll('Cameras and lights').objects.link(o);o.location=xyz(loc);o.rotation_euler=(xyz(target)-o.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=span/1000;cd.clip_start=.001;cd.clip_end=20;return o
cams={'front':camera('Front pair',(0,-25,900),(0,-25,0),450),'oblique':camera('Oblique pair',(260,80,700),(0,-25,20),480),'exploded':camera('Exploded',(550,210,800),(0,-30,140),590),'depth':camera('As found side',(650,50,30),(0,50,30),265),'inner':camera('Inner measured',(0,40,600),(0,40,0),210),'cover':camera('Cover scenario',(0,40,600),(0,40,0),220)}
for loc,power,size in [((300,400,500),3,.45),((-300,100,250),1.2,.35),((0,-300,500),1.8,.5)]:
 ld=bpy.data.lights.new('F005 softbox','AREA');o=bpy.data.objects.new('F005 softbox',ld);coll('Cameras and lights').objects.link(o);o.location=xyz(loc);o.rotation_euler=(xyz((0,-20,0))-o.location).to_track_quat('-Z','Y').to_euler();ld.energy=power;ld.shape='DISK';ld.size=size
layers={'A round appearance':['Appearance wall only','Pair A custom','Official exterior appearance'], 'B rectangle appearance':['Appearance wall only','Pair B custom','Official exterior appearance'],'Observed unchanged':['Observed unchanged'],'Exploded A':['Observed unchanged','Exploded A'],'Depth diagnostic':['Observed unchanged','Depth diagnostic'],'Measured inner':['Measured loose parts'],'Measured cover':['Measured loose cover']}
first=scene.view_layers[0]
for i,(name,visible) in enumerate(layers.items()):
 vl=first if i==0 else scene.view_layers.new(name);vl.name=name
 for c in vl.layer_collection.children:c.exclude=c.name not in [C[x].name for x in visible+['Cameras and lights']]
 vl.use=False
for fname,layer,cam,note in [
 ('pair_A_front','A round appearance','front','A | CONDITIONAL APPEARANCE - hardware correction/fit unresolved'),
 ('pair_A_oblique','A round appearance','oblique','A | CONDITIONAL APPEARANCE - hardware correction/fit unresolved'),
 ('pair_B_front','B rectangle appearance','front','B | CONDITIONAL APPEARANCE - hardware correction/fit unresolved'),
 ('pair_B_oblique','B rectangle appearance','oblique','B | CONDITIONAL APPEARANCE - hardware correction/fit unresolved'),
 ('exploded_A','Exploded A','exploded','EXPLODED | Display offsets only. Foam/rear interfaces provisional.'),
 ('as_found_depth','Depth diagnostic','depth','AS FOUND | Captured hardware unchanged; no stud trimming or valve move'),
 ('measured_inner','Measured inner','inner','MEASURED ENVELOPE | Local formed depths and rear shape remain provisional'),
 ('measured_cover','Measured cover','cover','COVER SCENARIO | OD, upper bore, edge gaps measured; lower bore/cavity provisional')]:
 for vl in scene.view_layers:vl.use=vl.name==layer
 bpy.context.window.view_layer=scene.view_layers[layer];scene.camera=cams[cam]
 scene.render.use_stamp=True
 for prop in ['use_stamp_time','use_stamp_date','use_stamp_render_time','use_stamp_frame','use_stamp_filename','use_stamp_camera','use_stamp_scene','use_stamp_hostname','use_stamp_marker','use_stamp_memory','use_stamp_lens']:setattr(scene.render,prop,False)
 scene.render.use_stamp_note=True;scene.render.use_stamp_labels=False;scene.render.stamp_note_text=note;scene.render.stamp_font_size=16;scene.render.stamp_background=(.025,.06,.08,.9);scene.render.stamp_foreground=(1,1,1,1)
 scene.render.filepath=str(OUT/'views'/f'{fname}.png');bpy.ops.render.render(write_still=True);print('Rendered',fname,flush=True)
# Default is a conditional cosmetic view with explicit scene properties.
for vl in scene.view_layers:vl.use=vl.name=='A round appearance'
bpy.context.window.view_layer=scene.view_layers['A round appearance'];scene.camera=cams['oblique'];scene['readiness']='DRAFT / NOT FOR FABRICATION. Corrected appearance only; source hardware remains unchanged in Observed layer.'
scene['design_revision']=d['design_revision'];scene['evidence_revision']=d['evidence_revision'];scene['coordinate_conversion']='CAD (X,Y,Z) mm -> Blender (X,-Z,Y)/1000'
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.file.pack_all();path=OUT/'paired_escutcheons_F005_DRAFT.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(path));assert bpy.data.scenes.get('F005 | paired escutcheons');bpy.context.window.scene=bpy.data.scenes['F005 | paired escutcheons']
missing=[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file and not Path(bpy.path.abspath(i.filepath)).exists()];assert not missing
# Verify custom extents in mm against exact CAD exports, including orientation transform.
checked=[]
for p in d['parts']:
 o=bpy.data.objects['F005 '+p['id']];co=[o.matrix_world@Vector(c) for c in o.bound_box];bb=[max(v[i] for v in co)-min(v[i] for v in co) for i in range(3)];m=next(m for m in a['parts'] if m['id']==p['id']+'-SS060');b=m['bounds_mm'];ex=[b[1][0]-b[0][0],b[1][2]-b[0][2],b[1][1]-b[0][1]];assert max(abs(x*1000-y) for x,y in zip(bb,ex))<.06;checked.append(p['id'])
(OUT/'blender_validation.json').write_text(json.dumps({'saved_reopened':True,'missing_images':missing,'custom_CAD_dimensions_checked':checked,'source_scan_preserved':True,'official_CAD_components':len(nominal),'rendered_images':8,'status':'PASS - software only; physical fit unresolved'},indent=2)+'\n')
print('F005 saved and reopened',path,flush=True)
