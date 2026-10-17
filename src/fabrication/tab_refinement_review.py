"""Readable TR03/RF02 study handoff; generated from the actual checks and solids."""
from pathlib import Path
import os,sys,json,hashlib,html,re
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'build/FT02/mpl'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
from shapely.geometry import shape,Point
from shapely.geometry.polygon import orient
from src.analysis.tab_rethink import top_profile
from src.analysis.tab_refinement import slot_shape

OUT=ROOT/'deliverables/current/fabrication/FT02/tab-refinement'
def read(p):return json.loads((ROOT/p).read_text())
def poly(ax,g,**kwargs):
    for a in getattr(g,'geoms',[g]):
        if a.geom_type!='Polygon' or a.is_empty:continue
        a=orient(a,sign=1);vs=[];cs=[]
        for ring in [a.exterior,*a.interiors]:
            xy=np.asarray(ring.coords);vs.extend(xy);cs.extend([MPath.MOVETO]+[MPath.LINETO]*(len(xy)-2)+[MPath.CLOSEPOLY])
        ax.add_patch(PathPatch(MPath(vs,cs),**kwargs))
def run():
    r=json.loads((OUT/'analysis.json').read_text())
    pp=top_profile(ROOT/r['parts'][1]['files']['stl'])
    old=top_profile(ROOT/'build/FT02/tab_rethink/inward_2.stl')
    fp=read('build/FT02/tab_refinement/footprints.json')
    fig,axs=plt.subplots(1,3,figsize=(14,5.8),gridspec_kw={'width_ratios':[1.25,1,1]})
    ax=axs[0];poly(ax,pp,facecolor='#387e90',edgecolor='#20515d',linewidth=.5)
    ax.set(xlim=(-115,115),ylim=(-115,115),title='Revised plate: outer diameter unchanged');ax.set_aspect('equal');ax.axis('off')
    ax.text(0,-115,'Ø220 mm · opening 112.35 × 147.10 mm',ha='center',va='top',fontsize=10)
    for ax,k,label in zip(axs[1:],['A','B'],['Upper-right rod','Lower-left rod']):
        p=r['slots'][k]['center_mm'];poly(ax,old,facecolor='#e8e8e8',edgecolor='#888',linewidth=.6)
        poly(ax,pp,facecolor='#deb473',edgecolor='#7e5b2a',linewidth=1)
        poly(ax,shape(fp[k]['visible_shaft']),facecolor='#427b88',edgecolor='none')
        g=shape(fp[k]['envelope']);ax.plot(*g.exterior.xy,color='#155362',ls='--',linewidth=1.6)
        fc=r['slots'][k]['factory_center_mm'];g=Point(fc).buffer(2.83,quad_segs=96)
        ax.plot(*g.exterior.xy,color='#9c4c9c',ls=':',linewidth=1.5)
        ax.set(xlim=(p[0]-11,p[0]+11),ylim=(p[1]-11,p[1]+11),title=label+' / 12 × 8 slot')
        ax.set_aspect('equal');ax.set_xlabel('Cover X (mm)');ax.set_ylabel('Cover Y (mm)');ax.grid(alpha=.15)
    fig.suptitle('Smaller flat tabs — nuts removed before placement',fontsize=17)
    fig.text(.5,.025,'Teal: visible shaft sweep. Dashed: inferred 5 mm bare-rod envelope. Purple dots: measured factory bore footprint.\nGrey: earlier 18 × 10 slot study. Working placement; no scan-accuracy allowance or physical fit claim.',ha='center',fontsize=10)
    fig.tight_layout(rect=[0,.09,1,.95]);fig.savefig(OUT/'slot_comparison.png',dpi=160);plt.close(fig)
    labels={'A-B':'Two rod tips','U-A':'Upper control → upper-right rod','L-A':'Lower control → upper-right rod','U-B':'Upper control → lower-left rod','L-B':'Lower control → lower-left rod'}
    rows=[]
    for q in r['scan_comparison']:
        if q['pair']=='U-L':continue
        cal=q['owner_3d_mm'];a=q['original_refitted_80_anchor_3d_mm'];b=q['attached_visible_picks_3d_mm']
        rows.append(f'<tr><th>{labels[q["pair"]]}</th><td>{cal:g}</td><td>{a:.2f}<small>{a-cal:+.2f} vs caliper</small></td><td>{b:.2f}<small>{b-cal:+.2f} vs caliper</small></td></tr>')
    files=[]
    for p in r['parts']+r['forms']:
        links=' · '.join(f'<a href="{Path(v).name}">{k.upper()}</a>' for k,v in p['files'].items())
        files.append(f'<li><strong>{html.escape(p["name"])}</strong><br>{links} — one custom solid, mm.</li>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Smaller tabs and deeper formwork | TR03 / RF02</title>
<style>body{font:17px/1.6 system-ui,sans-serif;color:#173642;background:#f4f7f8;margin:0}main{max-width:1100px;margin:auto;padding:28px}h1{line-height:1.15;font-size:36px}h2{margin-top:42px;font-size:26px}a{color:#046a80}nav{display:flex;gap:24px;flex-wrap:wrap}figure{margin:0}img{max-width:100%;display:block}figcaption{font-size:15px;margin:8px 0 24px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.note{border-left:4px solid #217588;background:#e4eef1;padding:16px 20px}.status{font-size:14px;color:#815623}table{width:100%;border-collapse:collapse;font-size:15px}th,td{padding:13px 10px;border-bottom:1px solid #c9d8dc;text-align:left}th{font-weight:600}thead{background:#dce8ec}td{font-variant-numeric:tabular-nums}small{display:block;color:#465e66;font-size:13px}.scroll{overflow-x:auto}li{margin:15px 0;overflow-wrap:anywhere}button{font:inherit;padding:8px 14px;border:1px solid #52747c;border-radius:4px;background:#edf4f6;color:#173642;cursor:pointer}button[aria-pressed=true]{background:#245e6d;color:white}.controls{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0}.hidden{display:none}@media(max-width:700px){main{padding:18px}.grid{grid-template-columns:1fr}h1{font-size:29px}table{min-width:670px}}@media print{button,nav{display:none}body{background:white}main{padding:0}.hidden{display:block}.grid{break-inside:avoid}h2{break-after:avoid}}</style>
<main><nav><a href="../tab-rethink/index.html">Earlier narrated video</a><a href="#scans">Scan comparison</a><a href="#form">Formwork</a><a href="#files">Study CAD</a></nav>
<p class="status">17 October 2026 · TR03 / RF02 · Design study, not released · FT02 purchase files unchanged</p>
<p class="note"><strong>Friend-ready print now available:</strong> <a href="../formwork-print/index.html">RF03 print package</a> keeps these smaller slots and collars, with an 8 mm face to save material. Includes STL, 3MF, STEP, instructions and a cost allowance. Print one temporary form; the plate purchase files remain separate.</p>
<h1>Smaller slots. Tabbed formwork.<br>A deeper option with clearance cutouts.</h1>
<p>The end fitting is a removable nut, as you confirmed. The revised plate can therefore be tested over the bare rods with those nuts removed first. The proposed slots are <strong>12 × 8 mm</strong>, reduced from 18 × 10 mm, in 16 mm-wide flat tabs.</p>
<figure><img src="slot_comparison.png" alt="Actual CAD plate and enlarged slot comparisons showing the rod paths"><figcaption>The outer Ø220 circle stays the same. The aperture keeps the 2 mm of extra inward backing explored in TR02. Adding tabs does not move the foam.</figcaption></figure>
<div class="grid"><div><h2>Why these offsets?</h2><p>Both slots sit 2 mm inward from the measured factory-hole centers. The lower-left slot also sits 1 mm higher to accommodate the captured rod path. These are deliberate design offsets for a new flat sheet at a different depth; your factory plate measurements remain unchanged.</p><p>The captured shafts fit within these slots. A separate inferred 5 mm rod envelope, extended through the region hidden by the nuts, also fits in the working placement. The narrowest model gap is about 0.6 mm. That is a geometric remainder, <strong>not a guaranteed tolerance for the real installation</strong>.</p></div>
<div><h2>Keep the tabs flat</h2><p>The design does not rely on bending them. First remove the nuts, trial the plate, visually center the cover/border, and establish supported retention. The slots are guides, not precision pins. Do not use bending or tightening to pull interfering hardware into alignment.</p><p>The nominal foam band stays supported, with about 2.8 mm of extra inward reserve in this model. Rear handle/hub shapes and actual engagement still need the ordinary assembly trial. The full knobs attach from the front.</p></div></div>
<h2 id="scans">Which scan agrees with the caliper?</h2>
<p><strong>The polycam without inner plate agrees more closely.</strong> Its differences are roughly 0.1–0.4 mm. The polycam with inner plate differs by roughly 0.5–1.9 mm, depending on the pair. All numbers below are three-dimensional tip-to-tip distances, in mm.</p>
<div class="scroll"><table><thead><tr><th>Contacts measured</th><th>Caliper</th><th>Polycam without inner plate</th><th>Polycam with inner plate</th></tr></thead><tbody>SCAN_ROWS</tbody></table></div>
<p class="note">Both scan comparisons use the caliper’s <strong>80 mm between control tips to set scale</strong>. Their matching 80 mm is an input, not an independent accuracy check. Visible end picks, reflective surfaces and different attached hardware remain limitations. The loose inner-plate calipers are coplanar and remain the stronger basis for its hole layout. No original scan was moved or rescaled by this study.</p>
<h2 id="form">The form now has tabs, too</h2>
<p>Both form options use integral 3 mm-thick locating tabs on the <strong>front side</strong> of the 12 mm-thick forming face. They use the same 12 × 8 mm slot layout. They help position the form; the independent padded brace carries the repair load. No tab or fastener is cast into the repair.</p>
<div class="controls"><button data-form="d12" aria-pressed="true">12 mm continuous collar</button><button data-form="d24_relieved" aria-pressed="false">24 mm relieved skirt</button></div>
<div class="grid"><figure><img id="form-front" src="form_d12_front.png" alt="Front of the temporary form, showing both locating tabs"><figcaption>Shower-facing view: purple tabs locate the form on the bare rods.</figcaption></figure><figure><img id="form-rear" src="form_d12_rear.png" alt="Rear of the temporary form, showing the collar"><figcaption id="form-caption">Wall-facing view: 12 mm continuous collar. The rear view reverses screen left and right.</figcaption></figure></div>
<div class="grid"><div><h2>Why not simply make it deeper?</h2><p>The unchanged full collar overlaps captured surfaces when extended to 18 or 24 mm. The main conflicts are the lower valve body and a smaller region on the installed left. Increasing taper did not eliminate them. At 30 mm, conflicts spread considerably.</p><p>The separate 24 mm option keeps the front 12 mm continuous, then extends farther where the scan permits. Two rear clearance windows avoid the captured conflicts. This is <strong>24 mm maximum reach, not a continuous 24 mm molding wall</strong>. Keep the original bounded front repair depth; do not fill through the windows or around service parts.</p></div><div><h2>Temporary use remains the basis</h2><p>I would begin with the 12 mm tabbed form. The 24 mm relieved option is available if extra reach is useful during the dry rehearsal. A deeper continuous collar has not been justified by this scan.</p><p>These tools are designed to be removed after the repair reaches appropriate stripping strength. Leaving a collar permanently behind the trim would need a separate retention, drainage and service-access design. The form does not establish a shower-water seal.</p><p>Full-face seating, stable support and free withdrawal still need a physical rehearsal. A clear collar path does not establish that the large front face sits flat on the travertine.</p></div></div>
<figure><img src="form_d24_relieved_side.png" alt="Side view of the 24 mm relieved collar"><figcaption>24 mm option, actual exported CAD. The short portions at the two rear windows remain 12 mm deep. This geometry is separate from the escutcheon and from the factory foam.</figcaption></figure>
<h2 id="files">Study files and checks</h2><p>One physical part per STEP/STL. Plate alternatives are 1.50 mm clear-stock geometry and 1.52 mm metal-stock geometry. The two form depths are alternatives. No vendor upload, order, physical fit or permanent-use approval has occurred.</p><ul>FILE_LINKS</ul>
<p><a href="TR03_RF02_parts_study.blend">Open the three-scene Blender study</a> · <a href="analysis.json">Executed analysis and export checks</a> · <a href="READ_ME.txt">Handoff notes</a></p>
<p>Rod reference: <a href="https://www.kohler.com/en/support/find-a-service-part/shop-parts/stud-10-24-x-4-56-l-1038645">Kohler 1038645, 10-24 × 4.56 inches</a>. Nut removability is your physical observation. This does not establish handle depth or thread engagement.</p>
</main><script>const buttons=document.querySelectorAll('[data-form]');for(const button of buttons){button.addEventListener('click',()=>{const key=button.dataset.form;for(const b of buttons)b.setAttribute('aria-pressed',String(b===button));document.getElementById('form-front').src='form_'+key+'_front.png';document.getElementById('form-rear').src='form_'+key+'_rear.png';document.getElementById('form-caption').textContent=key==='d12'?'Wall-facing view: 12 mm continuous collar. The rear view reverses screen left and right.':'Wall-facing view: 24 mm maximum skirt, with two rear clearance windows. Only the front 12 mm is continuous.';});}</script></html>'''
    page=page.replace('SCAN_ROWS',''.join(rows)).replace('FILE_LINKS',''.join(files))
    (OUT/'index.html').write_text(page)
    (OUT/'READ_ME.txt').write_text('TR03 / RF02 - 17 October 2026\nDESIGN STUDY, NOT RELEASED\n\nOpen index.html for the direct scan comparison, smaller slot design, two tabbed form options, and CAD links.\n\nPlate: D220; capsule112.35x147.10 R56.175; horizontal12x8 slots;16 mm tabs. Accepted R006 factory centers unchanged. Slot offsets A(-2,0), B(+2,+1) mm in cover frame. Remove end nuts first. Keep tabs flat; no bending is designed. 1.50 and1.52 mm alternatives are separate solids.\n\nForm: D240 front face12 mm;2 mm-wall collar; front-side locator tabs3 mm thick. D12 continuous12 mm. D24_RELIEVED maximum24 mm, but continuous only12 mm; rear windows clear captured lower-body and left-side conflicts. No increase to repair fill depth. Brace independently; rods locate only. All form material, liners and pads removed after suitable cure. Permanent retention not established.\n\nCaptured checks are not physical accuracy bounds or proof of hidden clearance, handle engagement, full form-face seating, support, demolding or waterproofing. No new owner measurements requested. No vendor package changed. Historical TR02 video remains intact.\n')
    # Preserve the old video, but make the new nut fact and refinement easy to find.
    old=ROOT/'deliverables/current/fabrication/FT02/tab-rethink/index.html'
    text=old.read_text();banner='<aside id="tr03-update" style="padding:18px;background:#e3eef1;color:#173642">New: removable nut confirmed. <a href="../tab-refinement/index.html">Smaller 12 × 8 mm slots, tabbed formwork, deeper-collar checks and a plain-language scan comparison.</a> This video documents the earlier 18 × 10 mm study.</aside>'
    if 'id="tr03-update"' in text:text=re.sub(r'<aside id="tr03-update".*?</aside>',banner,text,count=1)
    else:text=re.sub(r'(<body[^>]*>)',lambda m:m.group(1)+banner,text,count=1)
    old.write_text(text)
    print('Built TR03 review, comparison figure, CAD handoff and historical-video update link.')
if __name__=='__main__':run()
