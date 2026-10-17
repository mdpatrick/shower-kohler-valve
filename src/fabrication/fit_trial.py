"""FT01: simple, manufacturable fit-trial profiles and decision evidence.

The existing factory parts are retained. No scan point becomes a mounting hole.
"""
from pathlib import Path
import json, math, hashlib, os, sys
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'deliverables/current/fabrication/fit-trial'
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'build/fit_trial/matplotlib'))
import cadquery as cq
import ezdxf
import trimesh
import numpy as np
from shapely.geometry import Point,box,Polygon,LineString
from shapely.affinity import translate,affine_transform,scale
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Polygon as PP,Rectangle,FancyArrowPatch
sys.path.insert(0,str(ROOT))
from src.fabrication.fit_trial_spec import validate_design, values

def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rr(w,h,r):
    if abs(w/2-r)<1e-8:return LineString([(0,-h/2+r),(0,h/2-r)]).buffer(r,quad_segs=256)
    return box(-w/2+r,-h/2+r,w/2-r,h/2-r).buffer(r,quad_segs=256)
def make_main(d,t,locators=None):
    """Exact source geometry. Optional tabs are an engineering test, not selected."""
    m=d['main'];w,h=m['aperture_width_mm'],m['aperture_height_mm'];y=(h-w)/2
    cutter=(cq.Workplane('XY').moveTo(-w/2,-y).lineTo(-w/2,y)
            .threePointArc((0,h/2),(w/2,y)).lineTo(w/2,-y)
            .threePointArc((0,-h/2),(-w/2,-y)).close().extrude(t+2).translate((0,0,-1)))
    part=cq.Workplane('XY').circle(m['outer_diameter_mm']/2).extrude(t).cut(cutter)
    if locators:
        a,b=[locators[k] for k in ('A','B')]
        angle=math.degrees(math.atan2(a[1]-b[1],a[0]-b[0]))
        for p in [a,b]:
            root=math.copysign(67,p[0]);length=abs(root-p[0])+15
            tab=cq.Workplane('XY').center((root+p[0])/2,p[1]).slot2D(length,15,0).extrude(t)
            part=part.union(tab)
        part=part.edges('|Z').fillet(1.5)
        part=part.cut(cq.Workplane('XY').center(*a).circle(3.5).extrude(t+2).translate((0,0,-1)))
        part=part.cut(cq.Workplane('XY').center(*b).slot2D(10,7,angle).extrude(t+2).translate((0,0,-1)))
    return part
def run(design=None, output=None):
    global OUT
    d=validate_design(design or read('canon/fit_trial_design.json'))
    OUT=Path(output) if output is not None else ROOT/d.get('output_directory','deliverables/current/fabrication/fit-trial')
    resolved=read('data/derived/resolved.json');m=d['main'];f=d['foam'];parts=[]
    (OUT/'cad').mkdir(parents=True,exist_ok=True)
    # Remove only superseded generator-owned stock variants in this release.
    # Earlier releases and owner annotations remain untouched.
    active_ids={f'{d["revision"]}_{kind}_{od:g}_{stock["id"]}_FIT_TRIAL'
        for kind,od in [('MAIN',m['outer_diameter_mm']),('DIV',d['diverter']['outer_diameter_mm'])]
        for stock in d['stocks']}
    for previous in (OUT/'cad').glob(d['revision']+'_*'):
        if not any(previous.name.startswith(ident+'.') or previous.name==ident+'_preview.png' for ident in active_ids):
            previous.unlink()
    for kind,od in [('MAIN',m['outer_diameter_mm']),('DIV',d['diverter']['outer_diameter_mm']),('DIV-FALLBACK',d['diverter']['fallback_outer_diameter_mm'])]:
        if 'selected_parts' in d and kind not in d['selected_parts']:continue
        for stock in d['stocks']:
            t=stock['thickness_mm'];solid=cq.Workplane('XY').circle(od/2).extrude(t)
            if kind=='MAIN':
                w,h=m['aperture_width_mm'],m['aperture_height_mm'];y=(h-w)/2
                cutter=(cq.Workplane('XY').moveTo(-w/2,-y).lineTo(-w/2,y)
                        .threePointArc((0,h/2),(w/2,y)).lineTo(w/2,-y)
                        .threePointArc((0,-h/2),(-w/2,-y)).close().extrude(t+2).translate((0,0,-1)))
                innerarea=m['aperture_width_mm']*m['aperture_height_mm']-(4-math.pi)*m['aperture_radius_mm']**2
            else:
                ir=d['diverter']['aperture_diameter_mm']/2
                cutter=cq.Workplane('XY').circle(ir).extrude(t+2).translate((0,0,-1));innerarea=math.pi*ir**2
            part=make_main(d,t) if kind=='MAIN' else solid.cut(cutter);s=part.val()
            ident=f'{d["revision"]}_{kind}_{od:g}_{stock["id"]}_FIT_TRIAL'
            files={x:OUT/'cad'/(ident+'.'+x) for x in ['step','stl','dxf']}
            cq.exporters.export(s,str(files['step']))
            cq.exporters.export(s,str(files['stl']),tolerance=.02,angularTolerance=.05)
            wires=part.faces('>Z').wires().translate((0,0,-t))
            cq.exporters.export(wires,str(files['dxf']),exportType='DXF')
            doc=ezdxf.readfile(files['dxf']);doc.units=ezdxf.units.MM;doc.saveas(files['dxf'])
            back=cq.importers.importStep(str(files['step'])).val()
            dxfsolid=cq.importers.importDXF(str(files['dxf'])).wires().toPending().extrude(t).val()
            mesh=trimesh.load(files['stl'],force='mesh')
            volume=(math.pi*(od/2)**2-innerarea)*t
            assert s.isValid() and back.isValid() and len(back.Solids())==1
            assert abs(back.Volume()-volume)<.01 and abs(dxfsolid.Volume()-volume)<.02
            assert mesh.is_watertight and len(mesh.split())==1 and len(wires.vals())==2
            assert np.max(np.abs(mesh.extents-[od,od,t]))<.06
            parts.append({'id':ident,'kind':kind,'diameter_mm':od,'thickness_mm':t,'stock':stock['id'],
                'volume_mm3':volume,'plastic_solid_mass_g_at_1_27':volume*.00127,'steel_mass_g_at_8':volume*.008,
                'files':{k:str(v.relative_to(OUT)) for k,v in files.items()},'sha256':{k:sha(v) for k,v in files.items()},
                'checks':'Valid single STEP solid, analytic volume, DXF mm/two loops/volume, STL watertight/bounds PASS'})
    ap=rr(m['aperture_width_mm'],m['aperture_height_mm'],m['aperture_radius_mm'])
    fw,fh,fr,band=f['outer_width_mm'],f['outer_height_mm'],f['outer_corner_radius_mm'],f['width_mm']
    outer=rr(fw,fh,fr);foamin=rr(fw-2*band,fh-2*band,fr-band)
    foam=outer.difference(foamin)
    assert foam.intersection(ap).area<1e-6
    nominal_land=ap.boundary.distance(foamin.boundary)
    align=read('deliverables/current/fabrication/control-registration/registration_trial.json')
    cb=read('deliverables/current/fabrication/concentric-border-study/analysis.json')
    sys.path.insert(0,str(ROOT))
    from src.analysis.registration_trial import clipped_capture,coeff
    pieces,_=clipped_capture(resolved)
    cases=[]
    for c in align['cases']:
        item=c['coverage'][0]
        placed=affine_transform(ap,coeff(np.array(c['rigid_row_rotation']),c['main_center_installed_mm']))
        ps=[scale(p,xfact=c['scan_scale_trial'],yfact=c['scan_scale_trial'],origin=(0,0)) for p in pieces]
        conflicts=[p.difference(placed) for p in ps if not placed.covers(p)]
        assert sum(p.area for p in conflicts)<1e-7
        # The same circle center and traced features are retained. Changing a
        # radius changes every projected margin by exactly the radius delta.
        main_delta=(m['outer_diameter_mm']-item['main_diameter_mm'])/2
        separation=item['diverter_gap_mm']+(item['main_diameter_mm']+item['diverter_diameter_mm'])/2
        cases.append({'state':c['id'],'main_margin_after_trace_mm':item['minimum_margin_mm']+main_delta,
                      'gap_main_diverter_mm':separation-(m['outer_diameter_mm']+d['diverter']['outer_diameter_mm'])/2,
                      'gap_main_fallback_mm':separation-(m['outer_diameter_mm']+d['diverter']['fallback_outer_diameter_mm'])/2,
                      'center_separation_mm':separation,
                      'main_center_mm':c['main_center_installed_mm'],
                      'triangles_checked':len(ps),'conflict_triangles':len(conflicts),
                      'minimum_projected_hardware_clearance_mm':min(placed.boundary.distance(p) for p in ps),
                      'limit':'Prior primary-scan placement hypothesis, not a registered result from the newly attached capture'})
    controls=[]
    for name,opening in zip(['L','U'],resolved['inner_control_openings']):
        footprint=Point(opening['center_local_mm']).buffer(opening['diameter_mm']/2,quad_segs=256)
        controls.append({'control':name,**opening,'extra_custom_clearance_mm':ap.boundary.distance(footprint),
                         'inside_custom_aperture':ap.covers(footprint)})
    v=values(d,resolved)
    rlo=f['evaluated_outer_corner_radius_range_mm'][0]
    rhi=min(f['evaluated_outer_corner_radius_range_mm'][1],fw/2,fh/2)
    radii=sorted({rlo,rhi,*np.arange(math.ceil(rlo/5)*5,rhi,5)})
    report={'revision':d['revision'],'status':d['status'],'parts':parts,'design':d,'placement_scenarios':cases,
      'nominal_foam_extra_land_mm':nominal_land,
      'diverter_damage_margin_original_pose_mm':cb['variants'][0]['minimum_diverter_margin_mm']+(v['div_od']-cb['variants'][0]['diverter_diameter_mm'])/2,
      'diverter_nominal_cover_overlap_radial_mm':v['div_overlap'],
      'diverter_visible_border_mm':v['div_border'],
      'main_visible_border_mm':v['main_border'],
      'inner_opening_envelopes':controls,
      'geometric_check_scope':f'Capsule profile checked against {len(pieces):,} primary captured projected triangle pieces in each of {len(cases)} recorded placement hypotheses. Z >= 0.5 mm, inside OPEN-MAIN eroded 3 mm; excludes stone border/hidden geometry. No new attached-plate insertion proof; inner plate must be removed to install backing.',
      'foam_corner_sensitivity':[{'outer_radius_mm':float(rad),'extra_land_mm':ap.boundary.distance(rr(fw-2*band,fh-2*band,rad-band).boundary),'aperture_foam_overlap_mm2':ap.intersection(rr(fw,fh,rad).difference(rr(fw-2*band,fh-2*band,rad-band))).area} for rad in radii],
      'new_scan':'attached_scan_assessment.json',
      'tolerance_budget':{'metal_requested_profile_mm':v['metal_tolerance'],'minimum_nominal_foam_extra_land_mm':nominal_land,
                         'remaining_nominal_land_after_profile_target_mm':nominal_land-v['metal_tolerance'],
                         'scan_shape_placement_foam_errors':'not bounded; remaining nominal land is not an accepted tolerance'},
      'physical_checks':'Not performed; on-site checklist governs permanent installation.',
      'sources_sha256':{p:sha(ROOT/p) for p in ['src/fabrication/fit_trial.py','src/fabrication/fit_trial_spec.py','canon/fit_trial_design.json','canon/measurements.json','data/derived/resolved.json','deliverables/current/fabrication/control-registration/registration_trial.json','deliverables/current/fabrication/concentric-border-study/analysis.json','data/raw/polycam/polycam-inner-plate-attached.zip']}}
    (OUT/'design_report.json').write_text(json.dumps(report,indent=2)+'\n')
    figures(report,ap,outer,foamin,resolved)
    print(f'{d["revision"]}: {len(parts)} valid STEP/STL/DXF part sets; no integral mounting tabs; report and figures saved.')

def figures(report,ap,outer,foamin,resolved):
    v=values(report['design'],resolved,report);od=v['main_od'];land=report['nominal_foam_extra_land_mm']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    fig,ax=plt.subplots(figsize=(8,8))
    ax.add_patch(Circle((0,0),od/2,facecolor='#b6d1d7',edgecolor='#1d5260',lw=1.5))
    ax.add_patch(PP(np.array(ap.exterior.coords),facecolor='white',edgecolor='#16768c',lw=2))
    for p in [outer,foamin]:ax.plot(*p.exterior.xy,color='#aa7624',lw=1.8)
    ax.add_patch(Circle((0,0),v['main_cover']/2,fill=False,ls='--',edgecolor='#58636a'))
    for o in report['inner_opening_envelopes']:
        x,y=o['center_local_mm'];r=o['diameter_mm']/2
        ax.add_patch(Circle((x,y),r,fill=False,edgecolor='#815fa1',lw=1.7))
        ax.text(x,y,o['control']+(': size provisional' if o['control']=='L' else ': factory opening'),ha='center',va='center',fontsize=9)
    ax.annotate(f'Vertical capsule opening\n{v["aperture_w"]:.2f} x {v["aperture_h"]:.2f}, end R{v["aperture_r"]:g}',xy=(v['aperture_w']*.45,40),xytext=(0,od/2+11),ha='center',arrowprops={'arrowstyle':'->','color':'#16768c'})
    ax.annotate(f'Approximate foam band\n{v["foam_width"]:g} mm wide, flush to edge',xy=(-v['inner_w']/2+2,5),xytext=(-od/2-2,-od/2-5),ha='left',arrowprops={'arrowstyle':'->','color':'#aa7624'})
    ax.annotate(f'{od:g} mm outer circle',xy=(od*.48,-26),xytext=(12,-od/2-9),arrowprops={'arrowstyle':'->','color':'#1d5260'})
    ax.set_aspect('equal');ax.set(xlim=(-od/2-17,od/2+17),ylim=(-od/2-20,od/2+25));ax.axis('off')
    fig.suptitle('Custom opening and provisional factory opening footprints',fontsize=15)
    fig.text(.5,.035,f'Gold is a nominal footprint, not a verified seal. {land:.2f} mm extra land inside the assumed foam.\nPurple circles belong to the factory inner plate; they are not extra holes cut in this part.',ha='center',fontsize=9)
    fig.savefig(OUT/'access.png',dpi=170);plt.close(fig)

    fig,axs=plt.subplots(1,2,figsize=(11.4,6.6))
    separation=report['placement_scenarios'][0]['center_separation_mm']
    for index,(ax,div) in enumerate(zip(axs,[v['div_od'],v['fallback_od']])):
        for cy,dia,cover in [(0,od,v['main_cover']),(-separation,div,v['div_cover'])]:
            ax.add_patch(Circle((0,cy),dia/2,facecolor='#8fb6bf',edgecolor='#326674'))
            ax.add_patch(Circle((0,cy),cover/2,facecolor='#dadcda',edgecolor='#69757a'))
        ax.text(0,0,f'MAIN\n{od:g} mm',ha='center',va='center',fontsize=13)
        ax.text(0,-separation,f'DIVERTER\n{div:g} mm',ha='center',va='center',fontsize=12)
        gap=separation-(od+div)/2
        ax.annotate(f'{gap:.2f} mm gap*',xy=(1,-od/2-gap/2),xytext=(70,-od/2-22),arrowprops={'arrowstyle':'->'},fontsize=10)
        ax.set_aspect('equal');ax.set(xlim=(-od/2-12,od/2+15),ylim=(-separation-div/2-15,od/2+15));ax.axis('off')
        ax.set_title('Recommended companion' if index==0 else 'Fallback companion',fontsize=12)
    fig.text(.5,.035,f'*Original placement estimate. Across recorded scenarios, selected-pair gap is {v["gap_min"]:.2f}-{v["gap_max"]:.2f} mm, not error bounds.\nIncreasing either diameter consumes half that increase from the gap. Verify with both real covers.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.1,1,.98]);fig.savefig(OUT/'sizes.png',dpi=165);plt.close(fig)

    fig,ax=plt.subplots(figsize=(11,4.8));ax.set(xlim=(-8,118),ylim=(-8,58));ax.axis('off')
    # Diagrammatic section: horizontal is outward depth; vertical is position around opening.
    colors=['#c9bfa9','#6c99a5','#b18b48','#b4b8b7','#d5d8d7']
    labels=['Travertine /\nsound support',f'Custom plate\n{v["thickness"]:g} mm',f'Factory foam\n{v["foam_depth"]:g} mm FREE','Factory\ninner plate','Factory cover\nand handle']
    for x,w,col,lab in zip([0,26,45,64,86],[13,5,8,8,10],colors,labels):
        ax.add_patch(Rectangle((x,12),w,30,facecolor=col,edgecolor='#4f646a'))
        ax.text(x+w/2,52,lab,ha='center',va='top',fontsize=10)
    ax.text(19,20,'Bedding /\nseal detail\nby expert',rotation=90,ha='center',va='center',fontsize=8)
    ax.add_patch(FancyArrowPatch((12,5),(97,5),arrowstyle='->',mutation_scale=15,color='#2c6070'))
    ax.text(57,0,'Toward shower / added thickness consumes engagement',ha='center',fontsize=11)
    ax.text(110,26,'Handle\nconnects\nfrom front',ha='center',fontsize=10)
    fig.suptitle('Keep the factory attachment and sealing sequence',fontsize=16)
    fig.text(.5,.025,'Exploded section, not to scale. Effective bedding height and foam compression are not yet specified.\nPreserve the factory bottom drain. The backing does not repair concealed waterproofing by itself.',ha='center',fontsize=10)
    fig.savefig(OUT/'stack.png',dpi=170);plt.close(fig)

if __name__=='__main__':run()
