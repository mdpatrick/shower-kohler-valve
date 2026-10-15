"""ALIGN02: rigid placement and user-caliper scale sensitivity, never canon edits."""
from pathlib import Path
import json
import math
import os
import hashlib
import sys
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'deliverables/current/fabrication/control-registration'
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'build/aperture_access/matplotlib'))
import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.affinity import affine_transform, translate, scale
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon as PatchPolygon


def read(path):
    return json.loads((ROOT/path).read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def rr(w, h, radius, center):
    return translate(box(-w/2+radius, -h/2+radius, w/2-radius, h/2-radius).buffer(radius, quad_segs=128), *center)


def rigid(old, target):
    u, _, vt = np.linalg.svd((old-old.mean(0)).T @ (target-target.mean(0)))
    Q = u @ np.diag([1, np.linalg.det(u@vt)]) @ vt
    t = target.mean(0)-old.mean(0)@Q
    assert np.allclose(Q.T@Q, np.eye(2)) and np.linalg.det(Q) > .999999
    return Q, t


def coeff(Q, t):
    return [Q[0, 0], Q[1, 0], Q[0, 1], Q[1, 1], *t]


def clipped_capture(r):
    path = ROOT/'build/aperture_access/captured_forward_display.stl'
    dt = np.dtype([('normal', '<f4', (3,)), ('v', '<f4', (3, 3)), ('attr', '<u2')])
    tris = np.fromfile(path, dtype=dt, offset=84)['v'].astype(float)
    mask = Polygon(next(f['contour_mm'] for f in r['features'] if f['id']=='OPEN-MAIN')).buffer(-3)
    pieces = []
    for tri in tris:
        vertices = []
        for i, p in enumerate(tri):
            q = tri[(i+1)%3]; a, b = p[2] >= .5, q[2] >= .5
            if a:
                vertices.append(p)
            if a != b:
                vertices.append(p+(.5-p[2])/(q[2]-p[2])*(q-p))
        if len(vertices) < 3:
            continue
        poly = Polygon([(p[0], p[1]) for p in vertices])
        if poly.area < 1e-9:
            continue
        if not poly.is_valid:
            poly = poly.buffer(0)
        part = poly.intersection(mask)
        if part.area >= 1e-9:
            pieces.append(part)
    assert len(pieces) == read('deliverables/current/fabrication/aperture-access/analysis.json')['captured_surface']['triangles_considered']
    return pieces, path


def plot(r, report, geometry):
    fig, axes = plt.subplots(1, 3, figsize=(15, 8.5))
    colors = ['#7c8890', '#2d8192', '#006e9b']
    for ax, case, (ap, outer, foam, conflicts) in zip(axes, report['cases'], geometry):
        center = case['main_center_installed_mm']; s = case['scan_scale_trial']
        ax.add_patch(Circle(center, 110, facecolor='#dfedf0', edgecolor='#387989'))
        ax.add_patch(PatchPolygon(np.array(ap.exterior.coords), facecolor='white', edgecolor='#247e8f', lw=1.7))
        ax.plot(*outer.exterior.xy, color='#ad7b2d', lw=1)
        for f in r['features']:
            if not f.get('include_in_coverage'):
                continue
            xy=np.asarray(f['contour_mm'])*s
            ax.plot(xy[:, 0], xy[:, 1], color='#b54230', lw=1, alpha=.6)
        for hole, tip, diameter in zip(case['placed_reference_hole_centers_mm'], case['control_cap_targets_xy_mm'], [50, 48.46]):
            ax.add_patch(Circle(hole, diameter/2, fill=False, edgecolor='#855da0', ls='--' if diameter==50 else '-', lw=1.8))
            ax.plot(*tip, '+', color='#007eb5', ms=8, mew=1.8)
        for geom in getattr(conflicts, 'geoms', [conflicts]):
            if geom.geom_type == 'Polygon' and not geom.is_empty:
                ax.add_patch(PatchPolygon(np.array(geom.exterior.coords), color='#d33724'))
        ax.set_aspect('equal');ax.grid(alpha=.12)
        ax.set(xlim=(-116,117),ylim=(-74,157),xlabel='Installed X (mm)')
        ax.set_title(case['short_label'],fontsize=12,pad=16)
    axes[0].set_ylabel('Installed Y (mm)')
    fig.suptitle('Centering the plate references on the captured controls',fontsize=18,y=.96)
    fig.text(.5,.045,'Purple: unchanged factory-opening reference pattern • Blue +: estimated cap centers • Red: captured damage / aperture conflicts',ha='center',fontsize=10)
    fig.text(.5,.016,'ALIGN02 is a placement/scale trial. Lower opening position, shaft axes, support and physical fit remain unverified.',ha='center',fontsize=10)
    fig.subplots_adjust(left=.06,right=.985,top=.88,bottom=.28,wspace=.13)
    for ax, case in zip(axes, report['cases']):
        b=ax.get_position();item=case['coverage'][0]
        fig.text(b.x0+b.width/2,b.y0-.085,
                 f'Circle-center residual: {max(case["reference_center_residual_mm"]):.2f} mm\n'
                 f'Ø220 damage margin: {item["minimum_margin_mm"]:.2f} mm\n'
                 f'Captured triangles outside aperture: {case["capture_conflict_triangles"]}',
                 va='top',ha='center',fontsize=10,linespacing=1.6)
    fig.savefig(OUT/'registration_comparison.png',dpi=155);plt.close(fig)


def page(report):
    rows=''.join('<tr><td>'+c['short_label']+'</td><td>'+f'{c["scan_scale_trial"]:.6f}'+'</td><td>'+f'{max(c["reference_center_residual_mm"]):.3f}'+'</td><td>'+f'{c["capture_conflict_triangles"]}'+'</td><td>'+f'{c["coverage"][0]["minimum_margin_mm"]:.3f}'+'</td></tr>' for c in report['cases'])
    comparisons=''.join('<tr><td>'+p['pair']+'</td><td>'+f'{p["reported_3d_mm"]:.2f}'+'</td><td>'+f'{p["old_pick_distance_mm"]:.2f}'+'</td><td>'+f'{p["control_cap_xy_scaled_trial_distance_mm"]:.2f}'+'</td><td>'+p['role']+'</td></tr>' for p in report['caliper_comparison'])
    content='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Control registration trial | ALIGN02</title><style>body{margin:0;background:#eef3f4;color:#203e48;font:17px/1.55 system-ui}main{max-width:1220px;margin:auto;padding:28px}section{background:white;padding:24px;margin:22px 0;border-radius:9px}img{width:100%;height:auto}a{color:#006d87}h1{line-height:1.2}.flag{border-left:5px solid #ac6827;padding:16px;background:#fff2df}table{width:100%;border-collapse:collapse}td,th{padding:9px;text-align:left;border-bottom:1px solid #dbe3e5}.scroll{overflow-x:auto}@media(max-width:700px){main{padding:14px}section{padding:15px}}</style><main><a href="../aperture-access/index.html#control-alignment">← Why the original centers were wrong</a><h1>Reconcile the whole factory assembly</h1>
<p class="flag"><b>Three explicit model states, no accepted physical correction.</b> The original scan and numeric measurements stay unchanged. These trials show how inferred centering affects coverage and insertion; they do not approve fit or manufacture.</p>
<section><h2>What changes in the trials</h2><p>The second view applies one rigid transform to the existing factory-opening pattern and the complete main trim/backing arrangement. Neither individual opening is independently moved. The third view first uses your 80 mm 3D control-tip-center reading to calibrate a separate, uniformly scaled scan trial, then rigidly places the same unscaled factory parts. Both use the cap-center estimates from ALIGN01 and retain the old tip Z values as a depth sensitivity assumption.</p><img src="registration_comparison.png" alt="Original, rigid-centering and caliper-conditioned uniform-scale trials with unchanged factory-hole shapes and damage outlines"><div class="scroll"><table><tr><th>State</th><th>Scan scale factor</th><th>Max circle-center residual (mm)</th><th>Conflicting captured triangles</th><th>Ø220 damage margin (mm)</th></tr>'''+rows+'''</table></div>
<p>The lower reference opening's position and diameter are still unmeasured. A small fit residual against that assumed pattern is not an independent proof of factory alignment. The caliper-conditioned state uses the 80 mm reading as an input; matching it is not a validation test.</p>
<p>The hardware check uses the same 51,929 triangle projections as AP01, clipped above the provisional 0.5 mm plane and inside the observed opening eroded by 3 mm. Those boundaries scale with the separate scan trial. It excludes the stone edge and hidden hardware; zero conflicts applies only to that captured subset.</p></section>
<section><h2>What this means for knob access</h2><p>The purple circles represent the factory inner-plate openings: the upper diameter is measured at 48.46 mm; the lower 50 mm diameter and its position remain assumptions. The upright custom aperture surrounds these circles with about 11.0 mm of extra space at the upper opening and 10.9 mm at the lower one. Those margins stay the same when the factory pattern and backing move together.</p><p>This supports clearance through the custom backing for a coaxial rearward-reaching profile no wider than the corresponding circle, subject to actual shape, tilt and placement. It does not prove clearance through the factory opening itself. If the passing connection is almost the same diameter as that opening, even a small center error can matter. The complete visible knob diameter also does not establish the size or depth of its rear connection. Confirm the actual axes, profiles and axial engagement with the real parts.</p><p><b>The closest captured hardware is tighter than these opening circles:</b> the separate analytic check finds only about '''+f'{report["capture_aperture_minimum_clearance_mm"]["CALIPER"]:.2f}'+''' mm to the aperture in the caliper-conditioned trial. That is a model gap before unknown scan, axis, placement and manufacturing errors. It is not an accepted clearance allowance or machining tolerance.</p></section>
<section><h2>The other five readings remain checks, with uncertain scan endpoints</h2><div class="scroll"><table><tr><th>Tip pair</th><th>Your 3D reading</th><th>Old surface picks</th><th>Scaled cap-center trial</th><th>Role</th></tr>'''+comparisons+'''</table></div><p>All dimensions mm. Only the U/L XY points are replaced with diagnostic cap-center estimates in this comparison; stud endpoints and tip depths remain the original provisional picks. The remaining discrepancies must not become machining tolerances. Corrected stud-axis/end-face identification and actual depth are still needed.</p></section>
<section><h2>Do not shift only the factory inner plate</h2><p>In the unscaled rigid trial, leaving the custom backing fixed while moving the inner plate removes support from approximately '''+f'{report["factory_plate_only_foam_overlap_mm2"]:.0f}'+''' mm² of the nominal foam band. Its inward overhang reaches about '''+f'{report["factory_plate_only_max_overhang_mm"]:.2f}'+''' mm. Moving the backing aperture with the factory plate preserves their nominal 1 mm additional land under the same assumed foam/corner geometry, but changes insertion clearance and wall coverage.</p><p>These are projected model results. They do not establish sound stone, actual foam shape/compression, a continuous surface seal, or concealed waterproofing.</p></section>
<section><h2>What determines the next physical placement</h2><p>Use the real rigid inner plate and the actual adapter/handle interfaces to register both controls and mounting studs together. Confirm the lower factory opening diameter and its edge-to-edge spacing from the measured upper opening. Check the rearward-reaching connection profiles and thickness-correct engagement. Once that placement is established, recalculate the custom aperture, foam landing, outer damage margins and diverter gap together.</p><p><a href="registration_trial.json">All transforms, per-feature margins and source hashes</a>. AP01 cutting files are unchanged local shapes, still draft. No fabrication package has been released.</p></section></main></html>'''
    validation=OUT/'blender_validation.json'
    if validation.exists():
        check=json.loads(validation.read_text())
        current=hashlib.sha256(json.dumps(report['cases'],sort_keys=True).encode()).hexdigest()
        if check.get('placement_inputs_sha256')==current and (OUT/'control_registration_ALIGN02_DRAFT.blend').exists():
            section='''<section><h2>Blender: three separate placement states</h2><p><a href="control_registration_ALIGN02_DRAFT.blend">Open the saved ALIGN02 Blender comparison</a>. It opens to the 80 mm scale trial; the original and rigid-only states remain separate scenes. The source display crop is unchanged in the original state. Actual CAD parts retain their measured/draft sizes in every state.</p><img src="registration_caliper_front.png" alt="Repositioned plate references and separate caliper-conditioned scan trial; estimated cap centers appear near reference opening centers"><p>Blue crosses identify the estimated tip-cap centers. Purple rings are opening references, not measured knob profiles. Foam outlines are projected from the removed plate; this is not an installed-foam view.</p></section>'''
            content=content.replace('</main>',section+'</main>')
    (OUT/'index.html').write_text(content)


def attach_panel():
    for folder in ['aperture-access','concentric-border-study']:
        path=ROOT/'deliverables/current/fabrication'/folder/'index.html'
        if not path.exists():
            continue
        content=re.sub(r'<!-- ALIGN02 BEGIN -->.*?<!-- ALIGN02 END -->','',path.read_text(),flags=re.S)
        panel='''<!-- ALIGN02 BEGIN --><section class="panel" id="registration-trial"><h2>Next: the plate references recentered as a rigid assembly</h2><p>ALIGN02 compares the original placement, rigid recentering, and a separate scan-scale trial using your 80 mm control-center reading. Both revised placements clear all 51,929 captured triangle projections. The Ø220 option retains about 7.0 mm projected damage margin in the caliper-conditioned trial; Ø214.15 retains about 4.1 mm. Physical fit and actual center registration remain unverified.</p><p><a href="../control-registration/index.html">Open the placement comparison and updated Blender model</a>. Source scan, factory dimensions and AP01 cutting shapes remain preserved; these are unselected diagnostic states.</p></section><!-- ALIGN02 END -->'''
        if '<!-- ALIGN01 END -->' in content:
            content=content.replace('<!-- ALIGN01 END -->','<!-- ALIGN01 END -->'+panel,1)
        else:
            content=content.replace('<main>','<main>'+panel,1)
        path.write_text(content)


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    r=read('data/derived/resolved.json');a=read('deliverables/current/fabrication/aperture-access/control_alignment.json')
    evidence=read('docs/physical_checks/installed_center_distances_2026-10-15.json')
    center=np.asarray(r['inner_center_mm'])
    holes=np.array([c['reference_opening_center_xy_mm'] for c in a['controls']])
    targets=np.array([c['diagnostic_cap_center_xy_mm'] for c in a['controls']])
    z=np.array(r['controls_mm'])[:,2]
    ul=next(p['value_mm'] for p in evidence['observations'] if {p['feature_a'],p['feature_b']}=={'U','L'})
    calibration=ul/math.sqrt(np.sum((targets[1]-targets[0])**2)+(z[1]-z[0])**2)
    aperture=rr(116.35,151.1,33,center);outer=rr(130.35,165.1,40,center)
    foam=outer.difference(rr(118.35,153.1,34,center))
    pieces,crop=clipped_capture(r);cases=[];geometry=[];capture_margins={}
    projected_vertices=[]
    for p in pieces:
        for g in getattr(p,'geoms',[p]):
            if g.geom_type=='Polygon':projected_vertices.extend(g.exterior.coords)
    projected_vertices=np.unique(np.asarray(projected_vertices),axis=0)
    for name,label,s,Q,t in [('ORIGINAL','Original provisional placement',1,np.eye(2),np.zeros(2)),
                           ('RIGID','Rigid recentering only',1,*rigid(holes,targets)),
                           ('CALIPER','Rigid + 80 mm scale trial',calibration,*rigid(holes,targets*calibration))]:
        c=center@Q+t;ap=affine_transform(aperture,coeff(Q,t));out=affine_transform(outer,coeff(Q,t));ff=affine_transform(foam,coeff(Q,t))
        bad=[];count=0
        for p in pieces:
            q=scale(p,s,s,origin=(0,0)) if s!=1 else p
            excess=q.difference(ap)
            if excess.area>1e-7:
                count+=1;bad.append(excess)
        conflict=unary_union(bad)
        # Analytic convex rounded-rectangle check, independent of polygon differences.
        # Every clipped polygon lies inside when its vertices do; the smallest
        # boundary margin is attained on that polygon's boundary vertices.
        local=(projected_vertices*s-c)@Q.T
        delta=np.abs(local)-[116.35/2-33,151.1/2-33]
        signed=np.linalg.norm(np.maximum(delta,0),axis=1)+np.minimum(delta.max(axis=1),0)-33
        capture_margins[name]=float(-signed.max())
        coverage=[]
        for d,div_d in [(220,120),(214.15,128.425)]:
            margins=[]
            for f in r['features']:
                if f.get('include_in_coverage'):
                    # Trace allowance is in source-scan units; scale it with that evidence.
                    margin=d/2-np.linalg.norm(np.asarray(f['contour_mm'])*s-c,axis=1).max()-s*f.get('trace_allowance_mm_at_R001',0)
                    margins.append(dict(feature=f['id'],margin_mm=float(margin)))
            worst=min(margins,key=lambda x:x['margin_mm'])
            coverage.append(dict(main_diameter_mm=d,diverter_diameter_mm=div_d,per_feature=margins,minimum_margin_mm=worst['margin_mm'],limiting_feature=worst['feature'],diverter_gap_mm=float(np.linalg.norm(c-np.asarray(r['diverter_tip_mm'][:2])*s)-d/2-div_d/2)))
        opening_clearance=[dict(control=k,reference_diameter_mm=d,extra_aperture_margin_mm=float(Point(h).distance(ap.boundary)-d/2),diameter_status='measured' if k=='U' else 'assumed',placement_status='unverified rigid reference') for k,h,d in zip(['L','U'],holes@Q+t,[50,48.46])]
        cases.append(dict(id=name,short_label=label,scan_scale_trial=float(s),rigid_row_rotation=Q.tolist(),rigid_translation_mm=t.tolist(),rotation_deg=float(np.degrees(np.arctan2(Q[0,1],Q[0,0]))),main_center_installed_mm=c.tolist(),placed_reference_hole_centers_mm=(holes@Q+t).tolist(),control_cap_targets_xy_mm=(targets*s).tolist(),reference_center_residual_mm=np.linalg.norm(holes@Q+t-targets*s,axis=1).tolist(),reference_opening_aperture_margins=opening_clearance,coverage=coverage,capture_triangles_checked=len(pieces),capture_conflict_triangles=count,capture_conflict_area_mm2=float(conflict.area),foam_overlap_area_mm2=float(ff.intersection(ap).area)))
        assert ff.intersection(ap).area<1e-7
        geometry.append((ap,out,ff,conflict))
        print(name,'captured conflicts',count,flush=True)
    Q,t=rigid(holes,targets);unsupported=affine_transform(foam,coeff(Q,t)).intersection(aperture)
    points=[]
    for g in getattr(unsupported,'geoms',[unsupported]):
        if g.geom_type=='Polygon':points.extend(g.exterior.coords)
    maxover=max(Point(p).distance(aperture.boundary) for p in points)
    old=dict(zip(['L','U','SW','NE'],np.array(r['controls_mm']+r['studs_mm'])));new={k:v.copy() for k,v in old.items()}
    new['L'][:2]=targets[0];new['U'][:2]=targets[1];comparisons=[]
    for p in evidence['observations']:
        x,y=p['feature_a'],p['feature_b'];n=float(np.linalg.norm(new[x]-new[y])*calibration)
        comparisons.append(dict(pair=x+'–'+y,reported_3d_mm=p['value_mm'],old_pick_distance_mm=float(np.linalg.norm(old[x]-old[y])),control_cap_xy_scaled_trial_distance_mm=n,trial_minus_reported_mm=n-p['value_mm'],role='Calibration input; not a check' if {x,y}=={'U','L'} else 'Held out; scan endpoints still provisional'))
    result=dict(id='ALIGN02',date='2026-10-15',status='DRAFT_NOT_FOR_FABRICATION',selected=False,previous_goal_turn='PROGRESS: commit 9bc94aa established the cap-center discrepancy; this turn tests dependent registration and clearance.',cases=cases,capture_aperture_minimum_clearance_mm=capture_margins,caliper_comparison=comparisons,factory_plate_only_foam_overlap_mm2=unsupported.area,factory_plate_only_max_overhang_mm=maxover,
                source_frame='Preserved installed frame. Uniform scale applies only to a separate hypothetical source-scan state; actual part dimensions and original registration are unchanged.',
                cap_depth_assumption='Keep old U/L tip Z values while replacing their XY with ALIGN01 cap fits. No measured end-face plane or shaft axis.',
                capture_scope='Same 51,929 baseline clipped triangle projections. Z floor 0.5 mm and OPEN-MAIN eroded-3-mm mask both scale with the hypothetical source scan; excludes stone edges and unobserved hardware.',
                limits=['Lower inner opening position/diameter, plate horizontal datums and rear profiles remain provisional','User measurement uncertainty is unknown; calibration is not independent validation','Rigid fit does not fix holes independently, infer shaft tilt or verify axes at the plate plane','Circular trim/backing centers remain assumed equal to the inner-reference center','Stud endpoints and physical body surfaces remain uncertain','Nominal foam overlap is not validated continuous support or water sealing'],
                input_sha256={p:sha(ROOT/p) for p in ['data/derived/resolved.json','deliverables/current/fabrication/aperture-access/control_alignment.json','docs/physical_checks/installed_center_distances_2026-10-15.json','src/analysis/registration_trial.py']},physical_fit='UNPERFORMED',fabrication_release='HOLD')
    result['input_sha256'][str(crop.relative_to(ROOT))]=sha(crop)
    (OUT/'registration_trial.json').write_text(json.dumps(result,indent=2)+'\n')
    plot(r,result,geometry);page(result);attach_panel()
    print(json.dumps({c['id']:{'center':c['main_center_installed_mm'],'residual':c['reference_center_residual_mm'],'conflicts':c['capture_conflict_triangles'],'margins':[(x['main_diameter_mm'],x['minimum_margin_mm']) for x in c['coverage']]} for c in cases},indent=2))


if __name__=='__main__':
    run()
