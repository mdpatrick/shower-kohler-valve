"""FS02 actual cropped scan side views plus RF05 CAD previews, no fabricated evidence."""
from pathlib import Path
import bpy,json,math
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];BUILD=ROOT/'build/FS02';OUT=ROOT/'deliverables/current/analysis/tab-shafts-FS02'
CFG=json.loads((ROOT/'canon/tab_shaft_trial_FS02.json').read_text());r=json.loads((OUT/'analysis.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
mapping=Matrix(((.001,0,0,0),(0,0,-.001,0),(0,.001,0,0),(0,0,0,1)))

def setup(name):
    s=bpy.data.scenes.new(name);bpy.context.window.scene=s;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
    s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='OBJECT';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH'
    s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new(name+' world');s.world.color=(.9,.94,.95);s.view_settings.view_transform='Standard'
    s.render.resolution_x=1400;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
    cam=bpy.data.objects.new(name+' camera',bpy.data.cameras.new(name+' camera'));s.collection.objects.link(cam);s.camera=cam;cam.data.type='ORTHO'
    return s,cam

def view(s,c,pos,target,scale,path):
    c.location=pos;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=scale;s.render.filepath=str(path);bpy.ops.render.render(write_still=True)

meta=[]
for name in ['with_formwork','without_inner_plate']:
    for k in 'AB':
        s,c=setup(name+' | '+k+' shaft');src=BUILD/(name+'_'+k+'_context.ply');bpy.ops.wm.ply_import(filepath=str(src));o=bpy.context.object;o.matrix_world=mapping;o.color=(.48,.55,.58,1);o.name='OBSERVED '+name+' '+k+' | nuts retained for context ONLY'
        o['source']='FS01 transformed raw capture' if name=='with_formwork' else 'Primary original capture in FT02 working pose';o['scope']='Cropped original triangles, not remeshed; end hardware excluded from every fit calculation.'
        q=r['shaft_fits'][k][name]['at_tab_middle'];target=Vector((q[0]/1000,-.008,q[1]/1000))
        # Exactly edge-on along +X; the image shows canonical Y against depth Z.
        view(s,c,target+Vector((.2,0,0)),target,.042,OUT/(name+'_'+k+'_edge.png'))
        s['read_first']='Gray mesh is source evidence; end nut is context only. See FS02 HTML for the inferred 3 mm tab band and separate fit calculations.'
        meta.append({'scene':s.name,'source_crop':str(src.relative_to(ROOT)),'vertices':len(o.data.vertices),'edge_on_axis':'canonical +X; Y versus depth Z'})

s,c=setup('RF05 | optional tighter CAD forms')
g=json.loads((ROOT/'deliverables/current/fabrication/FT02/tight-form-RF05/geometry_checks.json').read_text());candidate=[]
for row,dx in zip(g['parts'],[-.135,.135]):
    stl=next(f for f in row['files'] if f['path'].endswith('.stl'));path=ROOT/'deliverables/current/fabrication/FT02/tight-form-RF05'/stl['path'];d=row['diameter_mm']
    bpy.ops.wm.stl_import(filepath=str(path));o=bpy.context.object;o.name='RF05 '+str(d)+' | actual CAD export, experimental';o.scale=(.001,)*3;o.location=(dx-d/2000,-d/2000,0);o.color=(.12,.45,.52,1);o['CAD_sha256']=stl['sha256'];candidate.append(o)
view(s,c,(.25,-.65,.62),(0,0,.01),.57,OUT/'candidate_forms.png')
s['status']=CFG['status'];s['physical_fit_tested']=False;s['nuts']='Absent from candidate geometry. Remove physical end nuts before trying form.'
sf,cf=setup('RF05 | front locator layout')
path=ROOT/'deliverables/current/fabrication/FT02/tight-form-RF05'/g['parts'][0]['files'][0]['path']
bpy.ops.wm.stl_import(filepath=str(path));front=bpy.context.object
front.matrix_world=mapping @ Matrix(((1,0,0,-120),(0,-1,0,120),(0,0,-1,0),(0,0,0,1)))
front.name='RF05 front | actual CAD, experimental';front.color=(.12,.45,.52,1)
view(sf,cf,(0,-.8,0),(0,0,0),.26,OUT/'candidate_front.png')
bpy.context.window.scene=s
# Save a compact inspection file with independent actual-scan scenes and CAD scene.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'shaft_inspection_FS02.blend'))
(OUT/'blender_check.json').write_text(json.dumps({'revision':'FS02','scenes':meta,'candidate_solid_exports':2,'geometry_from_CAD':True,'source_scans_modified':False},indent=2)+'\n')
