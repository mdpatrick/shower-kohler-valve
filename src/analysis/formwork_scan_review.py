"""Readable FS01 evidence report; plots derive only from captured/CAD data."""
from pathlib import Path
import csv, html, json, math, os, shutil, sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.analysis.formwork_scan import OUT, CACHE, rotation
os.environ.setdefault('MPLCONFIGDIR', str(CACHE/'matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from shapely.geometry import LineString


def capsule(w, h):
    p = LineString([(0, -(h-w)/2), (0, (h-w)/2)]).buffer(w/2, quad_segs=128)
    return np.array(p.exterior.coords)


def make():
    r = json.loads((OUT/'analysis.json').read_text()); rows = r['comparison']; ck = r['form_cross_checks']
    # Keep the served review self-contained; the web root cannot reach raw repository paths.
    for source, name in [
        ('data/evidence/scan_quality/wall_detail_registered.png', 'without_inner_plate.png'),
        ('deliverables/current/fabrication/fit-trial/plane_front.png', 'with_inner_plate.png'),
    ]:
        shutil.copyfile(ROOT/source, OUT/name)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig, ax = plt.subplots(figsize=(11,5.7), facecolor='white')
    colors = ['#458695','#90713b','#8b5fac']
    for i,(k,title) in enumerate([('without_inner_plate_mm','Polycam without inner plate'),('with_inner_plate_mm','Polycam with inner plate'),('with_formwork_mm','Polycam with formwork')]):
        d = [p[k]-p['caliper_3d_mm'] for p in rows]
        ax.scatter(d,np.arange(6)+(i-1)*.18,label=title,color=colors[i],s=55)
    ax.axvline(0,color='#32424c',lw=1);ax.set_yticks(range(6),[p['pair'] for p in rows]);ax.invert_yaxis()
    ax.grid(axis='x',alpha=.18);ax.set_xlabel('Scan minus caliper (mm)');ax.set_title('The overall distances broadly agree; this is not a slot-fit check',pad=18)
    ax.legend(loc='lower right',fontsize=9);fig.subplots_adjust(bottom=.2,left=.09,right=.98,top=.85)
    fig.text(.09,.055,'Earlier scans: U–L = 80 mm sets their scale. New scan: Ø240 form sets its scale.\nPoints are estimates; no certified scan-error bound is available.',fontsize=10,color='#40535e')
    fig.savefig(OUT/'comparison.png',dpi=170);plt.close(fig)

    image = plt.imread(OUT/'scan_front.png')
    fig, ax = plt.subplots(figsize=(10,10));ax.imshow(image,extent=[-142.5,142.5,-142.5,142.5])
    for k,p in r['tip_points_form_frame_mm'].items():
        ax.plot(*p[:2],'o',mfc='white',mec='#087d90',ms=7,mew=2)
        ax.annotate(k,p[:2],xytext=(9,9),textcoords='offset points',weight='bold',color='white',bbox={'facecolor':'#123642','edgecolor':'none','pad':3})
    ax.add_patch(Circle((0,0),120,fill=False,color='#00b4c5',lw=1.5))
    p=capsule(114.35,141.10);ax.plot(*p.T,color='#00b4c5',lw=1.7)
    ax.set_xlim(-135,135);ax.set_ylim(-135,135);ax.set_axis_off();ax.set_title('New Polycam + ideal CAD outline at the same scale',pad=13)
    fig.text(.12,.02,'U/L = control tips. A = upper-right rod. B = lower-left rod.\nCyan = CAD profile; scan remains locally uneven. No surface was stretched to fit.',fontsize=10)
    fig.subplots_adjust(bottom=.08,top=.93,left=.03,right=.97);fig.savefig(OUT/'form_overlay.png',dpi=160);plt.close(fig)

    sections=json.loads((CACHE/'sections.json').read_text());scale=r['uniform_mm_per_raw_unit']
    fig,axs=plt.subplots(1,2,figsize=(12,5.8))
    for ax,(name,center) in zip(axs,[('A',np.array([59.,27.])),('B',np.array([-40.,-16.]))]):
        for z,color,label in [(-.005,'#997334','About 1 mm behind face'),(-.01,'#168a9a','About 2 mm behind face')]:
            used=False
            for path in sections[str(z)]:
                p=np.array(path)*scale
                if np.any(np.linalg.norm(p[:,:2]-center,axis=1)<11):
                    ax.plot(p[:,0]-center[0],p[:,1]-center[1],color=color,lw=1.8,label=label if not used else None);used=True
        ax.set_xlim(-13,13);ax.set_ylim(-13,13);ax.set_aspect('equal');ax.grid(alpha=.2)
        ax.set_xlabel('Local X (mm)');ax.set_ylabel('Local Y (mm)');ax.set_title(name+' — '+('upper-right rod tab' if name=='A' else 'lower-left rod tab'))
    axs[0].annotate('Small opening vanishes\nin the deeper section',xy=(-2,-2),xytext=(-11,-10),arrowprops={'arrowstyle':'->'},fontsize=10)
    axs[1].annotate('Only part of the slot\nremains visible',xy=(2,-2),xytext=(-12,-11),arrowprops={'arrowstyle':'->'},fontsize=10)
    axs[0].legend(fontsize=9,loc='upper left');fig.suptitle('The scan does not recover the complete 12 × 8 mm holes',fontsize=15)
    fig.subplots_adjust(bottom=.18,top=.85,wspace=.28);fig.text(.07,.035,'Contours are real mesh slices, not redesigned holes. Nuts, rods and smoothed plastic merge in the capture.\nMissing scan geometry is not evidence that the printed holes are missing or that the rods do not fit.',fontsize=10)
    fig.savefig(OUT/'slot_resolution.png',dpi=170);plt.close(fig)

    fig,axs=plt.subplots(1,2,figsize=(11,4.8))
    for ax,row in zip(axs,r['hypothetical_slot_play']):
        l,w=row['slot_length_mm'],row['slot_width_mm'];p=np.array(LineString([(-(l-w)/2,0),((l-w)/2,0)]).buffer(w/2,quad_segs=64).exterior.coords)
        ax.fill(*p.T,color='#def1f3');ax.plot(*p.T,color='#007f91',lw=2)
        ax.add_patch(Circle((0,0),r['nominal_rod_diameter_mm']/2,facecolor='#75838b',edgecolor='#233a46'))
        ax.set_aspect('equal');ax.set_xlim(-7,7);ax.set_ylim(-5,5);ax.set_axis_off()
        ax.set_title(f'{l} × {w} mm'+(' — existing' if l==12 else ' — hypothetical trial'))
        ax.text(0,-4.8,f"Centered clearance: ±{row['one_axis_centered_clearance_x_mm']:.2f} mm X / ±{row['one_axis_centered_clearance_y_mm']:.2f} mm Y",ha='center',fontsize=10)
    fig.suptitle('A 10 × 7 slot would remove 1 mm of X play and 0.5 mm of Y play per side',fontsize=13)
    fig.subplots_adjust(bottom=.22,top=.83);fig.text(.06,.065,'Illustration uses a straight Ø4.826 mm nominal rod, centered in each slot. Actual rod lean and two-slot constraints\nchange assembly movement. This is not a released 10 × 7 design; the scan cannot verify its smaller margins.',fontsize=10)
    fig.savefig(OUT/'slot_play.png',dpi=170);plt.close(fig)

    with (OUT/'measurement_comparison_mm.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    table=''.join(f"<tr><th><button class='pair' data-pair='{p['pair']}'>{p['pair']}</button></th><td>{p['caliper_3d_mm']:g}</td><td>{p['without_inner_plate_mm']:.1f}{'*' if p['pair']=='U-L' else ''}</td><td>{p['with_inner_plate_mm']:.1f}{'*' if p['pair']=='U-L' else ''}</td><td><b>{p['with_formwork_mm']:.1f}</b></td><td>{p['formwork_minus_caliper_mm']:+.1f}</td></tr>" for p in rows)
    sensitivity=''.join(f"<tr><th>{p['pair']}</th><td>{p['formwork_method_sensitivity_mm'][0]:.1f}–{p['formwork_method_sensitivity_mm'][1]:.1f}</td></tr>" for p in rows)
    points={k:[300+p[0]/285*600,300-p[1]/285*600] for k,p in r['tip_points_form_frame_mm'].items()}
    svglabels=''.join(f"<circle cx='{p[0]}' cy='{p[1]}' r='4' fill='white' stroke='#087d90' stroke-width='2'/><text x='{p[0]+10}' y='{p[1]-10}' fill='white' stroke='#123642' stroke-width='4' paint-order='stroke' font-size='17' font-weight='700'>{k}</text>" for k,p in points.items())
    css='''*{box-sizing:border-box}body{margin:0;background:#edf3f4;color:#17323c;font:17px/1.6 system-ui,sans-serif}main{max-width:1160px;margin:auto;padding:36px 24px 70px}h1{font-size:38px;line-height:1.15;max-width:900px}h2{font-size:25px;line-height:1.25;margin-top:38px}p{max-width:980px}.eyebrow{font-size:13px;letter-spacing:.13em;text-transform:uppercase;color:#52717d}.lead{font-size:21px}.card{background:white;border-radius:14px;padding:24px;margin:24px 0;box-shadow:0 1px 5px #1232}.two{display:grid;grid-template-columns:1fr 1fr;gap:24px}.three{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}img,svg{max-width:100%;display:block}figure{margin:0}figcaption,.note{font-size:14px;color:#526b76;line-height:1.5}figcaption{padding:10px 0}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:15px}th,td{padding:12px 10px;border-bottom:1px solid #dde6e9;text-align:right}th:first-child,td:first-child{text-align:left}thead{background:#e4eff2}a{color:#08788b}button{border:0;background:#dceef1;padding:7px 13px;color:#07596a;border-radius:5px;cursor:pointer;font-weight:bold}.selected{background:#087e91;color:white}.decision{border-left:5px solid #cf8d29;padding-left:20px}.metric{font-size:29px;font-weight:750;color:#067e90}.three img{width:100%;height:280px;object-fit:contain;background:#f0f4f5}details{padding:20px;background:white;border-radius:12px;margin-top:24px}summary{cursor:pointer;font-weight:700}code{font-size:14px;overflow-wrap:anywhere}li{margin:9px 0}@media(max-width:800px){.two,.three{grid-template-columns:1fr}h1{font-size:30px}main{padding:22px 15px}table{min-width:760px}.card{padding:17px}}@media print{body{background:white}main{padding:0}.card{box-shadow:none;break-inside:avoid}h2{break-after:avoid}button{background:none}details{display:block}a{color:inherit}}'''
    content=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Formwork scan comparison · FS01</title><style>{css}</style><main>
<div class="card decision"><b>Later same-day follow-up:</b> <a href="../tab-shafts-FS02/index.html">FS02 uses edge-on bare-shaft views and prepares optional tighter RF05 locators.</a> Removable nuts are excluded. The owner now accepts a possible failed tighter print; the recommendation below records the earlier conservative FS01 assessment. Baseline geometry remains unchanged.</div>
<div class="eyebrow">Shower repair · FS01 · 19 October 2026</div><h1>The new scan supports the overall layout.<br>It does not establish a close bolt fit.</h1>
<p class="lead">Your printed form is now a useful independent scale reference. The new tip-distance estimates are about <b>0.3–1.1 mm below your calipers</b>. That is encouraging for the broad layout, but the scan blurs the very small features needed to tighten the slots.</p>
<div class="card decision"><b>Recommendation:</b> keep the existing 12 × 8 mm slots and the current form as the baseline. If less play is useful, try <b>removable locating inserts or small gauges on this form</b> before buying another full print. This assessment requests no new caliper measurements and does not release a tighter form.</div>
<div class="three card"><figure><img src="../../../../data/evidence/scan_quality/wall_detail_registered.png" alt="Original installed Polycam without inner plate"><figcaption><b>Polycam without inner plate</b><br>Original capture; earlier primary registration remains unchanged.</figcaption></figure><figure><img src="../../fabrication/fit-trial/plane_front.png" alt="Polycam with Kohler inner plate attached"><figcaption><b>Polycam with inner plate</b><br>Separate diagnostic; reflective metal and hidden rod details limit comparison.</figcaption></figure><figure><img src="scan_front.png" alt="New scan of printed form on the shower"><figcaption><b>Polycam with formwork</b><br>Scale from the original Ø240 form, assuming your print matches the CAD exactly.</figcaption></figure></div>
<h2>Compare the same six 3D tip distances</h2><p>U is the upper control, L the lower control, A the upper-right rod and B the lower-left rod. Click a pair to highlight its endpoints. Each distance runs through 3D space; it is <b>not</b> a dimension in the plane of the form or factory plate.</p>
<div class="two card"><div><svg viewBox="0 0 600 600" role="img" aria-label="Measured tips on the new scan"><image href="scan_front.png" width="600" height="600"/><line id="pairline" stroke="#ffca61" stroke-width="4"/>{svglabels}</svg></div><div><h3 id="pairtitle">U–L: upper to lower control</h3><p id="pairinfo"></p><p class="note">The line is a front projection for identification. The calculation includes the endpoints’ different depths.</p><p><b>Caliper distinction:</b> your loose inner-plate measurements were coplanar and remain the stronger source for its hole layout. R006 gives a 113.21 mm planar separation between the factory holes; that must not be replaced by the 109.8 mm distance between projecting rod tips.</p></div></div>
<div class="card scroll"><table><thead><tr><th>Tip pair</th><th>Caliper<br>mm</th><th>Polycam without<br>inner plate</th><th>Polycam with<br>inner plate</th><th>Polycam with<br>formwork</th><th>New scan<br>minus caliper</th></tr></thead><tbody>{table}</tbody></table><p class="note">* Both earlier scans were scaled using U–L = 80 mm. Their 80.0 entries are calibration inputs, not independent checks. The formwork scan’s scale uses no caliper reading. Estimates are rounded to 0.1 mm for comparison, not a claim of 0.1 mm accuracy.</p></div>
<figure class="card"><img src="comparison.png" alt="Scan minus caliper differences for all six pairs"><figcaption>The original scan agrees within about 0.4 mm on the five distances not used for scale. The inner-plate scan differs by as much as 1.9 mm. The new formwork scan differs by as much as 1.1 mm. These are observed discrepancies, not machining tolerances.</figcaption></figure>
<h2>What the known print tells us about the scan</h2><p>Following your instruction, the print is assumed exact. Therefore the differences below belong to the scan, the fitted feature or the way its blurred edge is sampled. I have not stretched the scan differently in different directions to force agreement.</p>
<div class="two card"><figure><img src="form_overlay.png" alt="Measured scan with exact CAD outer and opening outlines"><figcaption>The cyan outline is the CAD at the form-derived scale. The print and scan are not silently warped to coincide.</figcaption></figure><div class="scroll"><table><thead><tr><th>Feature</th><th>CAD</th><th>Scan</th></tr></thead><tbody><tr><th>Outer circle, fitted</th><td>240 mm</td><td>240 mm*</td></tr><tr><th>Outer X / Y spans</th><td>240 / 240</td><td>{ck['outer_rim_xy_spans_mm'][0]:.1f} / {ck['outer_rim_xy_spans_mm'][1]:.1f}</td></tr><tr><th>Clear opening width</th><td>114.35</td><td>{ck['opening_width_scan_mm']:.1f}</td></tr><tr><th>Clear opening height</th><td>141.10</td><td>{ck['opening_height_scan_mm']:.1f}</td></tr><tr><th>Opening / outer-center offset</th><td>0</td><td>{ck['opening_center_offset_norm_mm']:.1f}</td></tr><tr><th>Slot size</th><td>12 × 8</td><td>Not recoverable</td></tr><tr><th>Face / maximum collar depth</th><td>8 / 24</td><td>Not verified</td></tr></tbody></table><p class="note">* Chosen scale reference. Dimensions are mm. The opening is the form’s clear opening, not the larger outside of its collar and not the FT02 escutcheon opening. A section about 2 mm behind the front face avoids the rounded lip. The rear collar is hidden.</p></div></div>
<p>The fitted front face has about <b>{ck['front_face_plane_rms_mm']:.2f} mm RMS</b> departure from a plane; the sampled outside rim has about <b>{ck['outer_rim_radial_rms_mm']:.2f} mm RMS</b> radial departure from a circle. These quantify this reconstruction only. They do not establish a maximum physical error.</p>
<h2>Why this cannot yet justify tighter locating holes</h2>
<p>The whole form can look convincing while the slots and rods remain poorly reconstructed. In the mesh, the visible rods are only about <b>{r['rod_mesh_diagnostics']['A']['median_mesh_diameter_mm']:.1f} mm at A and {r['rod_mesh_diagnostics']['B']['median_mesh_diameter_mm']:.1f} mm at B</b>, compared with the identified stud’s approximately 4.83 mm nominal major diameter. Treating those skinny scanned rods as real would create falsely generous clearance.</p>
<figure class="card"><img src="slot_resolution.png" alt="Real mesh cross sections showing one slot disappearing and another only partly reconstructed"><figcaption>The rod/nut covers part of each slot, and photogrammetry merges nearby surfaces. These sections cannot supply a reliable slot center or the complete shaft clearance at the 3 mm-thick tab.</figcaption></figure>
<p>Separately, the scan puts the opening’s center about 2.0 mm away from the outer circle’s center, although the exact CAD makes them concentric. Choosing one or the other as the alignment reference would move the inferred slot location by more than the clearance we are trying to remove. Averaging more decimal places would not resolve that conflict.</p>
<figure class="card"><img src="slot_play.png" alt="Existing 12 by 8 slot compared with an unreleased 10 by 7 candidate"><figcaption>A modest change still needs a local trial: 10 × 7 mm removes just 0.5 mm per side vertically, which this scan cannot reliably verify. Tip spacing alone also misses rod lean and the insertion path.</figcaption></figure>
<h2>The practical next step</h2><ol><li><b>Use the current form as the master trial.</b> Its placement on both rods is captured. Full seating, unforced removal and repeatability are separate physical checks.</li><li><b>If play matters, test small removable locators first.</b> A sacrificial insert/gauge can be tried against the actual rods and existing slots without paying for another complete face and collar. An insert concept still needs its own printable geometry and retention/release review.</li><li><b>Only then transfer the proven fit into a new form.</b> Keep the broad control opening and collar geometry unless an actual interference is found. Locator tabs remain alignment aids; repair loads need independent padded bracing.</li></ol><p>No full measurement survey is requested. This is a recommendation for the next dry-fit experiment, not a claim that the repair is sealed or ready for filling.</p>
<details><summary>Method, sensitivity and preserved evidence</summary><p>The raw ZIP is preserved unchanged and SHA-256 checked. A robust plane is fitted to the broad front annulus; a complete outer rim section sets one uniform scale. The opening is fitted separately with the two tabs excluded. Original scan registration and accepted calipers are untouched.</p><p>Controls use a 2 mm cap band. Rod tips use 1.5 mm: the upper-right 2 mm band reaches the enlarged nut and misleadingly improves agreement with your caliper. That larger-band result was deliberately not selected. This is feature selection, not a fit to your numbers.</p><p>Varying cap-band choices and the sampled rim section from roughly 2 to 6 mm behind the face produces the ranges below. The deeper rim merges toward the wall. These ranges are <b>method sensitivity, not confidence intervals or guaranteed bounds</b>.</p><table><thead><tr><th>3D pair</th><th>New-scan sensitivity, mm</th></tr></thead><tbody>{sensitivity}</tbody></table><p>Other limitations: a later capture may show a different end-nut surface or adjustment; hidden shaft axes and the complete insertion sweep are not recovered. The two loose reflective plate scans are component references, not additional installed tip measurements.</p><p><a href="analysis.json">Full calculations and source hashes</a> · <a href="measurement_comparison_mm.csv">Comparison CSV</a> · <a href="formwork_scan_FS01.blend">Separate Blender inspection</a> · <a href="../../../../data/raw/polycam/polycam-shower-with-formwork.zip">Preserved original Polycam ZIP</a> · <a href="audit.json">Executed audit</a></p><p>Rebuild: <code>./project assess-formwork-scan</code>. CAD and previous print packages remain unchanged.</p></details>
</main><script>const pts={json.dumps(points)}, rows={json.dumps(rows)};const names={{'U-L':'upper to lower control','A-B':'upper-right to lower-left rod','U-A':'upper control to upper-right rod','L-A':'lower control to upper-right rod','U-B':'upper control to lower-left rod','L-B':'lower control to lower-left rod'}};function select(pair){{let [a,b]=pair.split('-'),line=document.getElementById('pairline');['x1','y1','x2','y2'].forEach((k,i)=>line.setAttribute(k,[...pts[a],...pts[b]][i]));document.getElementById('pairtitle').textContent=pair+' — '+names[pair];let r=rows.find(r=>r.pair===pair);document.getElementById('pairinfo').innerHTML='<span class="metric">'+r.with_formwork_mm.toFixed(1)+' mm</span><br>Polycam with formwork<br><b>'+r.caliper_3d_mm+' mm</b> caliper';document.querySelectorAll('.pair').forEach(b=>b.classList.toggle('selected',b.dataset.pair===pair));}}document.querySelectorAll('.pair').forEach(b=>b.addEventListener('click',()=>select(b.dataset.pair)));select('U-L');</script></html>'''
    controls = '<p aria-label="Select a tip pair">' + ' '.join(
        f'<button class="pair" data-pair="{p["pair"]}">{p["pair"]}</button>' for p in rows
    ) + '</p>'
    content = content.replace('<div><h3 id="pairtitle">', '<div>'+controls+'<h3 id="pairtitle">')
    content = content.replace('../../../../data/evidence/scan_quality/wall_detail_registered.png', 'without_inner_plate.png')
    content = content.replace('../../fabrication/fit-trial/plane_front.png', 'with_inner_plate.png')
    content = content.replace('../../../../data/raw/polycam/polycam-shower-with-formwork.zip', 'https://github.com/mdpatrick/shower-kohler-valve/blob/main/data/raw/polycam/polycam-shower-with-formwork.zip')
    (OUT/'index.html').write_text(content)
    print('FS01: four evidence figures, comparison CSV and interactive local report generated.')


if __name__=='__main__':
    make()
