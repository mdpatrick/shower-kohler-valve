"""FS02: edge-on shaft assessment, explicitly excluding removable nuts.

Diagnostics preserve two separate coordinate frames. Local tab arcs are fitted
without shaft data; they are not used to warp or globally align either capture.
"""
from pathlib import Path
import sys,json,math,os,hashlib
import numpy as np
from scipy.optimize import least_squares
import trimesh
from shapely.geometry import Point,LineString,mapping
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
OUT=ROOT/'deliverables/current/analysis/tab-shafts-FS02';BUILD=ROOT/'build/FS02'
os.environ.setdefault('MPLCONFIGDIR',str(BUILD/'mpl'))
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.analysis.tab_refinement import load_local
CFG=json.loads((ROOT/'canon/tab_shaft_trial_FS02.json').read_text())
BASE=json.loads((ROOT/'canon/formwork_print_RF03.json').read_text())

def dump(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,default=lambda a:a.tolist())+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def xy(line,z):return np.array([z,1.])@np.asarray(line)
def hole(k):
    s=CFG['trial'][k];c=np.array(s['center_cover_xy_mm'])
    if s['type']=='round':return Point(c).buffer(s['diameter_mm']/2,quad_segs=256)
    u=np.array(CFG['trial']['A']['center_cover_xy_mm'])-c;u/=np.linalg.norm(u)
    d=u*(s['length_mm']-s['width_mm'])/2
    return LineString([c-d,c+d]).buffer(s['width_mm']/2,quad_segs=256)

def generate():
    OUT.mkdir(parents=True,exist_ok=True);BUILD.mkdir(parents=True,exist_ok=True)
    if not (ROOT/'build/formwork_scan_FS01/vertices_mm.npy').exists():
        from src.analysis.formwork_scan import analyze
        analyze()
    v=np.load(ROOT/'build/formwork_scan_FS01/vertices_mm.npy');f=np.load(ROOT/'build/formwork_scan_FS01/faces.npy')
    _,old,of=load_local();old[:,2]-=8.05
    sources={'with_formwork':(v,f),'without_inner_plate':(old,of)}
    fit={};section_lines={};local={};allsections={}
    for k in 'AB':
        center=np.array(BASE['slots'][k]['center_mm']);fit[k]={};section_lines[k]={}
        for name,(vv,ff) in sources.items():
            m=(np.linalg.norm(vv[:,:2]-center,axis=1)<CFG['shaft_fit']['roi_radius_mm'])&(vv[:,2]>-7)&(vv[:,2]<30)
            zz=CFG['shaft_fit'][name+'_z_mm'][k];bins=[]
            for z in np.arange(zz[0],zz[1]+.01,1):
                p=vv[m&(abs(vv[:,2]-z)<CFG['shaft_fit']['sample_half_band_mm'])]
                if len(p)<CFG['shaft_fit']['minimum_points_per_band']:continue
                res=least_squares(lambda t:np.linalg.norm(p[:,:2]-t[:2],axis=1)-t[2],[*center,2],loss='soft_l1',f_scale=.2)
                bins.append({'z':z,'xy':res.x[:2].tolist(),'mesh_radius':float(res.x[2]),'points':len(p),'rms':float(np.sqrt(np.mean(res.fun**2)))})
            line=np.polyfit([b['z'] for b in bins],[b['xy'] for b in bins],1)
            fit[k][name]={'bands':bins,'line':line.tolist(),'fit_z':zz,'at_tab_middle':xy(line,-1.5).tolist(),
                          'lateral_drift_across_3mm_tab':float(np.linalg.norm(line[0])*3),'median_mesh_diameter':float(np.median([2*b['mesh_radius'] for b in bins])),
                          'tilt_from_front_normal_deg':float(math.degrees(math.atan(np.linalg.norm(line[0]))))}
            # Full visible context is retained for edge images ONLY. Evaluation
            # consumes fitted shaft bands and a separate nominal cylinder.
            ff2=ff[np.all(m[ff],axis=1)];mesh=trimesh.Trimesh(vv,ff2,process=False)
            section_lines[k][name]={}
            for axis,label in [(0,'horizontal'),(1,'vertical')]:
                n=np.zeros(3);n[1-axis]=1
                lines=trimesh.intersections.mesh_plane(mesh,n,np.r_[xy(line,-1.5),0])
                section_lines[k][name][label]=lines.tolist()
            # Mesh-only subset for real edge-on views; original full sources intact.
            mesh.remove_unreferenced_vertices();mesh.export(BUILD/(name+'_'+k+'_context.ply'))
    mesh=trimesh.Trimesh(v,f,process=False)
    for z in CFG['local_tab_fit']['sections_front_z_mm']:
        paths=mesh.section(plane_normal=[0,0,1],plane_origin=[0,0,z]).discrete
        allsections[str(z)]=[p.tolist() for p in paths]
    for k in 'AB':
        c=np.array(BASE['slots'][k]['center_mm']);side=np.sign(c[0]);expected=c-[side*2,0];rows=[]
        for z,paths in allsections.items():
            paths=[np.array(p) for p in paths]
            path=max((p for p in paths if np.max(np.abs(p[:,:2]))<90),key=len)
            p=path[:,:2];rad=np.linalg.norm(p-expected,axis=1)
            pts=p[(rad>6)&(rad<10)&((p[:,0]-expected[0])*side < -2.5)]
            fixed=least_squares(lambda t:np.linalg.norm(pts-t,axis=1)-8,expected,loss='soft_l1',f_scale=.15)
            free=least_squares(lambda t:np.linalg.norm(pts-t[:2],axis=1)-t[2],[*expected,8],loss='soft_l1',f_scale=.15)
            hc=fixed.x+[side*2,0];offset=xy(fit[k]['with_formwork']['line'],-1.5)-hc
            rows.append({'z':float(z),'points':len(pts),'arc_R8_center':fixed.x.tolist(),'inferred_current_slot_center':hc.tolist(),
                         'shaft_minus_local_slot_center':offset.tolist(),'fixed_radius_rms':float(np.sqrt(np.mean(fixed.fun**2))),
                         'free_circle_center_radius':free.x.tolist(),'free_radius_rms':float(np.sqrt(np.mean(free.fun**2))),
                         'fit_points':pts.tolist()})
        local[k]=rows
    checks=[]
    for k in 'AB':
        line=fit[k]['without_inner_plate']['line'];h=hole(k)
        for scope,zs in [('seated',[-3,0]),('visible_shaft_forward_of_tab_back',[max(-3,fit[k]['without_inner_plate']['fit_z'][0]),fit[k]['without_inner_plate']['fit_z'][1]]),('chosen_20mm_forward_sensitivity',[-3,20])]:
            # Tilted circular cylinder section is an ellipse, slightly wider than
            # a disk. Circumscribe it by r*sqrt(1+|slope|^2), conservatively.
            slope=np.array(line[0]);radius=2.5*math.sqrt(1+float(slope@slope))
            footprint=LineString([xy(line,zs[0]),xy(line,zs[1])]).buffer(radius,quad_segs=256)
            contained=h.covers(footprint)
            checks.append({'rod':k,'scope':scope,'z_front_mm':zs,'evaluation_diameter_mm':5,'tilt_inflated_radius':radius,
                           'contained':contained,'minimum_geometric_clearance_mm':h.boundary.distance(footprint) if contained else None,
                           'outside_area_mm2':footprint.difference(h).area,'footprint':mapping(footprint)})
    a=np.array(CFG['trial']['A']['center_cover_xy_mm']);b=np.array(CFG['trial']['B']['center_cover_xy_mm']);vec=a-b
    protect=['canon/measurements.json','canon/transforms.json','canon/formwork_selection.json','canon/formwork_print_RF03.json',
             'canon/formwork_small_bed_RF04.json','canon/fit_trial_design.json',
             'deliverables/current/fabrication/FT02/formwork-print/SEND_TO_PRINTER/CAD_REFERENCE/RF03_D24_RELIEVED_mm.step']
    r={'revision':'FS02 / RF05','status':CFG['status'],'nut_policy':CFG['nut_policy'],'risk':CFG['risk'],
       'frames':CFG['scan_frames'],'shaft_fits':fit,'local_printed_tabs':local,'trial':CFG['trial'],
       'lower_slot_angle_deg':math.degrees(math.atan2(vec[1],vec[0])),'locator_center_spacing_mm':float(np.linalg.norm(vec)),
       'geometric_checks':checks,'checks_scope':'Fixed historical working placement, inferred nominal 5 mm bare shaft. Numerical clearances are not printer/scanner error allowances. The 20 mm interval is a chosen sensitivity calculation, not a measured complete insertion sweep.',
       'new_scan_interpretation':'Nearby R8 tab arcs suggest both shafts lie about 1.6–1.7 mm above the existing slot centers in this captured placement. Local rounding changes this estimate; do not use the distorted overall form center to define new precision holes. This does not establish full seating.',
       'owner_measurements_requested':[],'protected_sha256':{p:sha(ROOT/p) for p in protect},
       'source_sha256':{p:sha(ROOT/p) for p in ['canon/tab_shaft_trial_FS02.json','deliverables/current/analysis/formwork-scan-FS01/analysis.json','deliverables/current/fabrication/FT02/tab-rethink/analysis.json']}}
    dump(OUT/'analysis.json',r);dump(BUILD/'edge_sections.json',section_lines);dump(BUILD/'tab_sections.json',allsections)
    plots(r,section_lines,allsections)
    print(json.dumps({'checks':[{key:val for key,val in c.items() if key!='footprint'} for c in checks], 'angle':r['lower_slot_angle_deg']},indent=2))

def plots(r,sections,tabsections):
    colors={'without_inner_plate':'#a76b1d','with_formwork':'#168795'}
    labels={'without_inner_plate':'Polycam without inner plate','with_formwork':'Polycam with formwork'}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    # Each scan keeps its own frame. Both edge axes shown; no total-tip metrics.
    for k in 'AB':
        fig,axs=plt.subplots(2,2,figsize=(13,8),layout='constrained')
        for row,name in enumerate(colors):
            line=r['shaft_fits'][k][name]['line'];mid=xy(line,-1.5)
            for col,(axis,label) in enumerate([(0,'horizontal'),(1,'vertical')]):
                ax=axs[row,col];zs=np.linspace(-3,20,100)
                for seg in sections[k][name][label]:
                    p=np.array(seg);ax.plot(p[:,2],p[:,axis]-mid[axis],color='#9eaaaf',lw=1)
                ax.axvspan(-3,0,color='#d4e7eb',label='3 mm tab band')
                upper=zs*np.array(line)[0,axis]+np.array(line)[1,axis]-mid[axis]
                ax.fill_between(zs,upper-2.5,upper+2.5,color=colors[name],alpha=.14)
                ax.plot(zs,upper,color=colors[name],lw=2,label='Inferred shaft axis')
                zz=r['shaft_fits'][k][name]['fit_z'];ax.axvspan(*zz,ymin=.015,ymax=.055,color=colors[name])
                ax.text(15,6.6,'Nut / end hardware\nexcluded from fit',ha='center',fontsize=10,color='#6c4850')
                ax.set(xlim=(-6,26),ylim=(-9,9),xlabel='Depth from front face (mm)',ylabel=('X' if axis==0 else 'Y')+' from shaft at mid-tab (mm)',title=labels[name]+' · '+label+' / depth')
                ax.set_aspect('equal',adjustable='box');ax.grid(alpha=.15)
        fig.suptitle(('Upper-right A' if k=='A' else 'Lower-left B')+' — inspect the shaft at the tab, not the removable nut',fontsize=16)
        fig.supxlabel('Gray: captured section. Color: fitted axis + 5 mm evaluation cylinder. Shaded band: tab location.\nThe new scan hides the shaft inside the tab; its nearby visible shaft is extrapolated through the 3 mm band.',fontsize=10)
        fig.savefig(OUT/('edge_sections_'+k+'.png'),dpi=160);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(12,6.8))
    fig.subplots_adjust(left=.07,right=.98,bottom=.22,top=.84,wspace=.22)
    for ax,k in zip(axs,'AB'):
        row=next(x for x in r['local_printed_tabs'][k] if x['z']==-1.5);c=np.array(row['inferred_current_slot_center']);rod=xy(r['shaft_fits'][k]['with_formwork']['line'],-1.5)
        for p in tabsections['-1.5']:
            p=np.array(p);ax.plot(p[:,0],p[:,1],color='#758891',lw=1.5)
        p=np.array(row['fit_points']);ax.scatter(*p.T,s=7,color='#d2922d',label='Visible R8 tab arc')
        h=LineString([c-[2,0],c+[2,0]]).buffer(4,quad_segs=128);ax.plot(*h.exterior.xy,'--',color='#718d2c',label='Known 12 × 8 slot, inferred pose')
        circ=Point(rod).buffer(2.5,quad_segs=128);ax.fill(*circ.exterior.xy,color='#168795',alpha=.45,label='5 mm shaft envelope')
        ax.scatter(*rod,marker='+',s=60,c='#084e57');ax.annotate(f"Shaft {row['shaft_minus_local_slot_center'][1]:.1f} mm above\nlocal slot center",xy=rod,xytext=(c[0]-12,c[1]+11),arrowprops={'arrowstyle':'->'},fontsize=11)
        ax.set(xlim=(c[0]-15,c[0]+15),ylim=(c[1]-12,c[1]+15),title='Upper-right A' if k=='A' else 'Lower-left B',xlabel='Front-frame X (mm)',ylabel='Front-frame Y (mm)');ax.set_aspect('equal');ax.grid(alpha=.15)
    axs[0].legend(loc='lower left',fontsize=8)
    fig.suptitle('Read shaft position from the nearby tab — the global scan outline is distorted',fontsize=15)
    fig.supxlabel('Section 1.5 mm behind the face. Dashed slot location is inferred from the visible tab arc, not recovered hole walls.\nBoth offsets concern the captured pose; no shaft, form or raw scan has been moved.',fontsize=10,y=.04)
    fig.savefig(OUT/'local_tab_positions.png',dpi=160);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(12,6),layout='constrained')
    for ax,k in zip(axs,'AB'):
        c=np.array(CFG['trial'][k]['center_cover_xy_mm']);base=np.array(BASE['slots'][k]['center_mm']);h=hole(k);old=LineString([base-[2,0],base+[2,0]]).buffer(4,quad_segs=128)
        ax.plot(*old.exterior.xy,'--',color='#9ba5aa',lw=2,label='Existing 12 × 8 opening')
        ax.fill(*h.exterior.xy,color='#bfe1e6',alpha=.7);ax.plot(*h.exterior.xy,color='#168795',lw=2,label='New RF05 opening')
        for row,col in [('chosen_20mm_forward_sensitivity','#e9b75d'),('seated','#116c78')]:
            from shapely.geometry import shape
            f=shape(next(x for x in r['geometric_checks'] if x['rod']==k and x['scope']==row)['footprint']);ax.fill(*f.exterior.xy,color=col,alpha=.5,label='Bare-axis 20 mm sensitivity' if row.startswith('chosen') else 'Shaft at tab thickness')
        ax.scatter(*c,s=20,color='#152d38');ax.set_aspect('equal');ax.set(xlim=(base[0]-8,base[0]+8),ylim=(base[1]-6,base[1]+6),xlabel='Working cover-frame X (mm)',ylabel='Working cover-frame Y (mm)',title='A: round Ø6.5 mm' if k=='A' else 'B: 9 × 6.5 mm slot, along A–B');ax.grid(alpha=.15)
    axs[0].legend(loc='lower left',fontsize=8)
    fig.suptitle('RF05 — a deliberately tight experiment, with removable nuts absent',fontsize=16)
    fig.supxlabel('Original-scan working placement and inferred 5 mm shafts. Only openings change; tab bodies, collar and control access stay the same.\nVery small calculated gaps leave little room for reconstruction and printing error. No numerical success probability is asserted.',fontsize=10)
    fig.savefig(OUT/'tight_locator_plan.png',dpi=160);plt.close(fig)

if __name__=='__main__':generate()
