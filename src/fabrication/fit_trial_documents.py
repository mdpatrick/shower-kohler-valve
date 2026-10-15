"""Evergreen field guide, private-free shop package and full-size paper trial."""
from pathlib import Path
import json,math,html,hashlib,zipfile,sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,A3,landscape
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'deliverables/current/fabrication/fit-trial'
sys.path.insert(0,str(ROOT))
from src.fabrication.fit_trial_spec import values,expand
def configure(design=None,report=None,output=None):
    global D,R,V,H,OUT
    OUT=Path(output) if output is not None else ROOT/'deliverables/current/fabrication/fit-trial'
    D=design or json.loads((ROOT/'canon/fit_trial_design.json').read_text())
    R=report or json.loads((OUT/'design_report.json').read_text())
    assert R['design']==D, 'Rebuild analysis before documents; canonical design changed'
    V=values(D,json.loads((ROOT/'data/derived/resolved.json').read_text()),R)
    H=expand(json.loads((ROOT/'canon/fit_trial_handoff.json').read_text()),V)
INK=HexColor('#203942');BLUE=HexColor('#1c6578');PALE=HexColor('#edf3f4')
STYLE=ParagraphStyle('body',fontName='Helvetica',fontSize=10.1,leading=13.8,textColor=INK)
SMALL=ParagraphStyle('small',parent=STYLE,fontSize=8.4,leading=11.3)
HEAD=ParagraphStyle('heading',parent=STYLE,fontName='Helvetica-Bold',fontSize=11.1,leading=14)

def para(c,text,x,y,w,style=STYLE):
    # Deliberate line breaks for the field record; escape all ordinary content.
    text=html.escape(expand(text,V)).replace('\n','<br/>')
    p=Paragraph(text,style);_,height=p.wrap(w,1000)
    assert y-height>43, f'Page overflow: {text[:65]} at {y-height}'
    p.drawOn(c,x,y-height);return y-height
def base(c,title,number,kind='FIELD GUIDE',size=A4):
    w,h=size;c.setFillColor(BLUE);c.rect(0,h-14, w,14,fill=1,stroke=0)
    c.setFont('Helvetica-Bold',9);c.setFillColor(BLUE);c.drawString(36,h-36,'SHOWER ESCUTCHEON REPAIR  /  FT01')
    c.setFont('Helvetica',8);c.drawRightString(w-36,h-36,'15 OCT 2026  |  '+kind)
    y=para(c,title,36,h-55,w-72,ParagraphStyle('title',parent=HEAD,fontSize=23,leading=27))
    c.setStrokeColor(HexColor('#b7c9ce'));c.line(36,35,w-36,35)
    c.setFillColor(INK);c.setFont('Helvetica',7.5)
    c.drawString(36,23,'FOR QUOTE AND DRY FIT  |  Permanent installation requires field verification')
    c.drawRightString(w-36,23,str(number));return y-14
def footerlink(c,label,url,x,y):
    c.setFont('Helvetica',8);c.setFillColor(BLUE);c.drawString(x,y,label)
    c.linkURL(url,(x,y-2,x+c.stringWidth(label,'Helvetica',8),y+9),relative=0)
def picture(c,path,x,y,w,h):
    img=ImageReader(str(path));iw,ih=img.getSize();s=min(w/iw,h/ih)
    dw,dh=iw*s,ih*s;c.drawImage(img,x+(w-dw)/2,y-dh,width=dw,height=dh,mask='auto')
    return y-dh

def guide():
    path=OUT/'project_handoff_FT01.pdf';c=canvas.Canvas(str(path),pagesize=A4)
    c.setTitle(H['title']);c.setAuthor('Shower escutcheon project')
    page_number=0
    for idx,p in enumerate(H['pages']):
        page_number+=1;y=base(c,p['title'],page_number)
        y=para(c,p['lead'],36,y,A4[0]-72)-10
        if idx==0:
            top=y
            y=picture(c,OUT/p['image'],307,top,252,255)
            left=para(c,'Recommendation',36,top,248,HEAD)-7
            left=para(c,H['recommendation'],36,left,248)
            y=min(y,left)-8
        elif p.get('image'):
            y=picture(c,OUT/p['image'],36,y,A4[0]-72,185)-6
        if p.get('caption'):y=para(c,p['caption'],36,y,A4[0]-72,SMALL)-12
        for b in p['blocks']:
            y=para(c,b['heading'],36,y,A4[0]-72,HEAD)-4
            y=para(c,b['text'],36,y,A4[0]-72)-10
            if b.get('url'):
                footerlink(c,'Open official Kohler installation guide',b['url'],36,y+1);y-=16
        if idx==5:
            y=para(c,'Source files and companion sheets',36,y,A4[0]-72,HEAD)-4
            y=para(c,'Use shop_drawings_FT01.pdf for dimensions and full_size_templates_FT01.pdf at 100% scale. The local index.html contains downloads, source links, quote comparison inputs and the Blender scene.',36,y,A4[0]-72,SMALL)
        c.showPage()
        if idx==4:
            page_number+=1;y=base(c,'Vendor comparison',page_number)
            y=para(c,'Public terms checked 15 October 2026. Actual design-specific quotes and delivery dates are not yet obtained.',36,y,A4[0]-72)-12
            for v in H['vendors']:
                c.setFillColor(PALE);c.roundRect(32,y-27,A4[0]-64,28,4,fill=1,stroke=0)
                y=para(c,v['name']+'  |  '+v['allowance'],40,y-6,A4[0]-80,HEAD)-12
                for text in [v['route'],v['time'],v['note']]:y=para(c,text,40,y,A4[0]-80,SMALL)-5
                y-=8;footerlink(c,'Vendor terms / quote entry',v['url'],40,y);y-=26
            y=para(c,H['budget_limits'],36,y,A4[0]-72,SMALL)-12
            y=para(c,'Compare delivered metal total / delivered plastic total. At 2.0 or less, metal can be the first sacrificial trial if the finish and arrival are acceptable. A higher price does not itself prove better fit.',36,y,A4[0]-72)
            c.showPage()
    c.save();return path

def capsule(c,x,y,w,h):
    r=w/2;cy=(h-w)/2
    p=c.beginPath();p.moveTo(x-r,y-cy);p.lineTo(x-r,y+cy)
    # Exact semicircular ends, no polygon approximation.
    p.arcTo(x-r,y+cy-r,x+r,y+cy+r,180,-180)
    p.lineTo(x+r,y-cy);p.arcTo(x-r,y-cy-r,x+r,y-cy+r,0,-180);p.close()
    c.drawPath(p,stroke=1,fill=0)
def arrow(c,x,y,dx,dy):
    norm=math.hypot(dx,dy);dx,dy=dx/norm,dy/norm
    p=c.beginPath();p.moveTo(x,y);p.lineTo(x+dx*5-dy*2,y+dy*5+dx*2);p.lineTo(x+dx*5+dy*2,y+dy*5-dx*2);p.close();c.drawPath(p,fill=1,stroke=0)
def hdim(c,x1,x2,y,text):
    c.setStrokeColor(BLUE);c.setFillColor(BLUE);c.setLineWidth(.65);c.line(x1,y,x2,y)
    arrow(c,x1,y,1,0);arrow(c,x2,y,-1,0);c.line(x1,y-4,x1,y+4);c.line(x2,y-4,x2,y+4)
    c.setFont('Helvetica',10);c.drawCentredString((x1+x2)/2,y+5,text)
def vdim(c,x,y1,y2,text):
    c.setStrokeColor(BLUE);c.setFillColor(BLUE);c.setLineWidth(.65);c.line(x,y1,x,y2)
    arrow(c,x,y1,0,1);arrow(c,x,y2,0,-1);c.line(x-4,y1,x+4,y1);c.line(x-4,y2,x+4,y2)
    c.saveState();c.translate(x+11,(y1+y2)/2);c.rotate(90);c.setFont('Helvetica',10);c.drawCentredString(0,0,text);c.restoreState()
def profile(c,kind,cx,cy):
    od=V['main_od'] if kind=='MAIN' else V['div_od']
    c.setStrokeColor(INK);c.setFillColor(INK);c.setLineWidth(.8);c.circle(cx,cy,od*mm/2,stroke=1,fill=0)
    if kind=='MAIN':capsule(c,cx,cy,V['aperture_w']*mm,V['aperture_h']*mm)
    else:c.circle(cx,cy,V['div_id']*mm/2,stroke=1,fill=0)
    c.setDash(4,3);c.setStrokeColor(HexColor('#7e9197'));c.setLineWidth(.35)
    c.line(cx-od*.52*mm,cy,cx+od*.52*mm,cy);c.line(cx,cy-od*.52*mm,cx,cy+od*.52*mm);c.setDash()
def drawings():
    size=landscape(A3);path=OUT/'shop_drawings_FT01.pdf';c=canvas.Canvas(str(path),pagesize=size)
    for i,kind in enumerate(['MAIN','DIV']):
        base(c,'Main backing plate' if kind=='MAIN' else 'Diverter backing ring',i+1,'SHOP DRAWING - mm',size)
        cx,cy=128*mm,143*mm;profile(c,kind,cx,cy)
        if kind=='MAIN':
            hdim(c,cx-V['main_od']*mm/2,cx+V['main_od']*mm/2,24*mm,f'OUTSIDE DIAMETER {V["main_od"]:.2f}')
            hdim(c,cx-V['aperture_w']*mm/2,cx+V['aperture_w']*mm/2,230*mm,f'OPENING WIDTH {V["aperture_w"]:.2f}')
            vdim(c,208*mm,cy-V['aperture_h']*mm/2,cy+V['aperture_h']*mm/2,f'OPENING HEIGHT {V["aperture_h"]:.2f}')
            c.setFillColor(INK);c.setFont('Helvetica',10)
            c.drawCentredString(cx,cy+44*mm,f'SEMICIRCULAR ENDS R{V["aperture_r"]:g}')
            c.drawCentredString(cx,cy+37*mm,f'Arc centers: X=0, Y=+/-{V["arc_offset"]:g}')
            c.drawCentredString(cx,cy-3*mm,'One centered through opening')
            c.drawCentredString(cx,cy-10*mm,f'Straight sides: {V["straight"]:g} long')
            ident=f'{D["revision"]}_MAIN_{V["main_od"]:g}';outline='Vertical capsule, [[aperture_w:.2f]] x [[aperture_h:.2f]], end R[[aperture_r:g]]. Aperture center equals outer-circle center.'
        else:
            hdim(c,cx-V['div_od']*mm/2,cx+V['div_od']*mm/2,66*mm,f'OUTSIDE DIAMETER {V["div_od"]:.2f}')
            hdim(c,cx-V['div_id']*mm/2,cx+V['div_id']*mm/2,cy,f'THROUGH DIAMETER {V["div_id"]:.2f}')
            ident=f'{D["revision"]}_DIV_{V["div_od"]:g}';outline='Concentric circular ring, outside [[div_od:.2f]], inside [[div_id:.2f]]. Optional separate fallback outside [[fallback_od:.2f]], same inside [[div_id:.2f]]. Order one size only.'
            c.setFont('Helvetica',10);c.setFillColor(INK);c.drawCentredString(cx,cy+73*mm,f'{V["div_id"]:g} mm aperture is a fit-trial choice; factory rear footprint unverified')
        x=255*mm;w=148*mm;y=250*mm
        for heading,text in [
          ('PART / QUANTITY',ident+' | one per selected pair'),
          ('GEOMETRY',outline),
          ('THICKNESS OPTIONS','[[stock]] = [[thickness:.3f]] mm / [[thickness_in:.3f]] inch. First stainless quote; matching STL available for plastic. [[alt_stock]] = [[alt_thickness:.3f]] mm plastic/acrylic alternative. No silent material or thickness substitution.'),
          ('MATERIAL / FINISH','Quote 316 stainless, deburred and directionally grained. Alternative 304 protected brushed stock. Protect visible face; align grain on the pair. Report actual finish and thickness.'),
          ('REQUESTED SHOP TARGETS','Metal cut profile +/-[[metal_tolerance:.2f]] mm; plastic +/-[[plastic_tolerance:.2f]] mm. Global free flatness target [[flatness:.2f]] mm. These are requests for vendor confirmation, not promised capabilities or accepted field tolerance.'),
          ('EDGES','Smooth all edges, inside and outside, both faces. Remove cutting microtabs and sharp burrs. Do not change the contour to solve an installation conflict.'),
          ('STATUS','Authorized design scope: quote and sacrificial dry-fit manufacture. No mounting tabs, threaded holes, bends or countersinks. Permanent installation is not released.'),
          ('DATUM / FILES','Local origin at outer-circle center; rear face Z=0, front Z=thickness. X right, Y toward upper control. STEP controls solid thickness. DXF is 1:1 mm profile, no kerf compensation. STL units are mm by instruction.')]:
            y=para(c,heading,x,y,w,HEAD)-4;y=para(c,text,x,y,w,SMALL)-12
        c.showPage()
    c.save();return path
def templates():
    path=OUT/'full_size_templates_FT01.pdf';c=canvas.Canvas(str(path),pagesize=landscape(A3));size=landscape(A3)
    for i,kind in enumerate(['MAIN','DIV']):
        base(c,kind+' - full-size paper trial',i+1,'A3 LANDSCAPE / 100%',size)
        cx,cy=128*mm,143*mm;profile(c,kind,cx,cy)
        x=255*mm;y=250*mm;w=145*mm
        notes=['Print A3 landscape at 100% / actual size. Disable fit, shrink and printer scaling. Verify both 100 mm bars with a ruler before using this template.',
               'Cut black contours only. The crosshairs are alignment marks, not cuts. Paper checks planar coverage; it cannot establish stiffness, added depth, gasket compression or water performance.',
               'Place the real factory cover concentrically. Check equal visible border at top, bottom, left and right. Trace the actual rear gasket/contact footprint separately before accepting the aperture.',
               'MAIN [[main_od]]: border to measured [[main_cover]] cover is [[main_border:.3f]] mm. DIV [[div_od]]: border to nominal [[div_cover]] cover is [[div_border:.4f]] mm. Actual diverter cover size must be checked on site.',
               'Use both templates together. Predicted pair separation is [[gap_min:.2f]]-[[gap_max:.2f]] mm across earlier scenarios, not error bounds. Prefer 3 mm actual gap; use the [[fallback_od]] mm fallback if needed.']
        for n in notes:y=para(c,n,x,y,w)-15
        c.setLineWidth(.8);c.setStrokeColor(INK);c.line(x,75*mm,x+100*mm,75*mm)
        c.line(x,71*mm,x,79*mm);c.line(x+100*mm,71*mm,x+100*mm,79*mm)
        c.setFont('Helvetica',10);c.drawString(x,81*mm,'100 mm horizontal check')
        c.line(399*mm,50*mm,399*mm,150*mm);c.line(395*mm,50*mm,403*mm,50*mm);c.line(395*mm,150*mm,403*mm,150*mm)
        c.saveState();c.translate(395*mm,100*mm);c.rotate(90);c.drawCentredString(0,0,'100 mm vertical check');c.restoreState()
        if kind=='DIV':
            c.setDash(3,3);c.setStrokeColor(HexColor('#9a7770'));c.circle(cx,cy,V['fallback_od']*mm/2);c.setDash()
            c.setFillColor(INK);c.setFont('Helvetica',10);c.drawCentredString(cx,cy-78*mm,f'Dashed {V["fallback_od"]:g} mm circle = fallback reference only')
        c.showPage()
    c.save();return path

def html_page():
    def link(p,label):return f'<a href="{html.escape(p)}">{html.escape(label)}</a>'
    parts={p['kind']:p for p in R['parts'] if p['stock']==V['stock']}
    uploads=''.join('<div class="file"><b>'+kind+'</b> '+ ' / '.join(link(p['files'][ext],ext.upper()) for ext in ['step','dxf','stl'])+'</div>' for kind,p in parts.items() if kind!='DIV-FALLBACK')
    sections=[]
    for i,p in enumerate(H['pages']):
        img=(f'<figure><img src="{p["image"]}" alt="{html.escape(p["caption"])}"><figcaption>{html.escape(p["caption"])}</figcaption></figure>') if p.get('image') else ''
        blocks=''.join(f'<h3>{html.escape(b["heading"])}</h3><p>{html.escape(b["text"]).replace(chr(10),"<br>")}</p>'+ (f'<p>{link(b["url"],"Official source")}</p>' if b.get('url') else '') for b in p['blocks'])
        sections.append(f'<section id="part-{i+1}"><h2>{html.escape(p["title"])}</h2><p class="lead">{html.escape(p["lead"])}</p>{img}{blocks}</section>')
    rows=''.join('<tr>'+''.join(f'<td>{html.escape(v[k])}</td>' for k in ['name','route','allowance','time'])+f'<td>{link(v["url"],"Published terms")}'+(f'<br>{link(v["finish_url"],"Finish / timing")}' if v.get('finish_url') else '')+'</td></tr>' for v in H['vendors'])
    fallback=parts['DIV-FALLBACK'];alt=''.join('<li>'+p['kind']+' '+link(p['files']['stl'],f'{V["alt_thickness"]:g} mm STL')+' / '+link(p['files']['step'],'STEP')+'</li>' for p in R['parts'] if p['stock']==V['alt_stock'])
    htmltext='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Escutcheon fit trial and project handoff | FT01</title><style>
    :root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#edf3f4;color:#203942;font:17px/1.58 system-ui,sans-serif}main{max-width:1140px;margin:auto;padding:28px}h1{font-size:40px;line-height:1.15;max-width:850px}h2{font-size:27px;line-height:1.25}h3{font-size:18px;margin:24px 0 4px}p{margin:8px 0 15px}section{scroll-margin-top:80px}section,.hero{background:#fff;border-radius:12px;padding:28px;margin:24px 0}a{color:#09657e}nav{position:sticky;top:0;background:#fff;padding:12px 20px;border-bottom:1px solid #c6d5d9;z-index:3;display:flex;gap:24px;flex-wrap:wrap}.lead{font-size:19px}.badge{font-size:13px;letter-spacing:.08em;color:#665221}.file{padding:12px;background:#edf4f5;margin:10px 0;border-radius:7px}.actions{display:flex;gap:12px;flex-wrap:wrap}.button{display:inline-block;padding:12px 16px;background:#145f72;color:white;border-radius:6px;text-decoration:none}figure{margin:20px 0}figure img{display:block;max-height:560px;max-width:100%;height:auto;margin:auto}figcaption{font-size:14px;color:#4c626b;margin:12px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.grid img{width:100%;border-radius:9px}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:12px;text-align:left;border-bottom:1px solid #c7d6dc;vertical-align:top}th{background:#edf4f5}input{font:inherit;width:170px;padding:8px;border:1px solid #8ba6af;border-radius:4px}label{display:block;margin:12px 0}output{display:block;padding:14px;background:#e6f2f5;border-radius:6px}small{color:#4c626b}details{margin:18px 0}code{font-size:14px}@media(max-width:700px){main{padding:12px}section,.hero{padding:18px}.grid{grid-template-columns:1fr}h1{font-size:31px}nav{gap:12px;font-size:14px}}
    </style><nav><a href="#files">Upload files</a><a href="#part-4">Expert visit</a><a href="#quotes">Quotes</a><a href="#drawings">Documents</a></nav><main><p class="badge">FT01 · 15 OCTOBER 2026 · QUOTE AND DRY FIT</p><h1>A useful part for the Kohler visit</h1><div class="hero"><p class="lead">'''+html.escape(H['recommendation'])+'''</p><p><b>Recommended:</b> main Ø[[main_od]] / diverter Ø[[div_od]], a broad vertical capsule opening, [[thickness:.3f]] mm first metal stock, and no integral bolt tabs.</p><p>Permanent installation remains subject to the real handle, gasket, support and water checks. You can price and make a sacrificial fit trial now.</p></div><section id="files"><h2>Upload these two parts</h2><p>Metal: use STEP or DXF, millimeters, quantity one each, [[thickness_in:.3f]] inch stainless. Printing: use STL in millimeters. [[stock]] is [[thickness:.3f]] mm thick. The DXF contains only the two cutting contours.</p>'''+uploads+'''<div class="actions"><a class="button" href="FT01_recommended_[[stock]]_quote.zip">Download recommended pair + shop sheets</a><a class="button" href="FT01_plastic_[[alt_stock]]_quote.zip">[[alt_thickness]] mm plastic alternative</a></div><details><summary>Fallback and alternate files</summary><p>If the pair is too close on the wall, replace only the diverter with the [[fallback_od]] mm fallback: '''+' / '.join(link(fallback['files'][e],e.upper()) for e in ['step','dxf','stl'])+'''</p><ul>'''+alt+'''</ul><p>Do not order every alternative. The [[alt_thickness]] mm trial changes depth by +[[depth_difference:.3f]] mm relative to the metal.</p></details></section>'''+''.join(sections)+'''<section><h2>Why these sizes and this opening?</h2><div class="grid"><img src="sizes.png" alt="Comparison of [[div_od]] and [[fallback_od]] mm diverter rings beneath the [[main_od]] mm main"><img src="access.png" alt="Capsule opening and nominal foam footprint"></div><p>The capsule keeps more metal under uncertain rounded corners than the earlier R33 opening, while clearing all [[capture_pieces:,]] scoped captured triangle pieces in each of [[scenario_count]] earlier placement scenarios. The closest calculated hardware gap is about [[hardware_min:.2f]] mm before unbounded scan and placement errors. The nominal extra foam land is only [[foam_land:.2f]] mm. These small margins are reasons to trial the actual parts, not to invent a large machining tolerance.</p><p>The newly attached scan is direct evidence of the real plate/hub relationship, but its metal width disagrees with the caliper by about 4 mm. It does not supply a reliable bolt-jig pattern. Fixed tabs are omitted to preserve adjustable centering and avoid new insertion/engagement conflicts.</p></section><section id="quotes"><h2>Compare current quotes</h2><p>'''+html.escape(H['budget_limits'])+'''</p><div class="scroll"><table><tr><th>Vendor</th><th>Route</th><th>Planning allowance</th><th>Published timing</th><th>Source</th></tr>'''+rows+'''</table></div><div class="grid"><label>Plastic delivered total ($)<br><input id="plastic" type="number" min="0" step="0.01" placeholder="Enter actual quote"></label><label>Metal delivered total ($)<br><input id="metal" type="number" min="0" step="0.01" placeholder="Enter actual quote"></label></div><output id="comparison">Enter both delivered totals, including finish, shipping, rush and tax.</output><p><small>Local calculator only. It does not upload, place an order or prove fit. Arrival date and finish still matter.</small></p></section><section id="drawings"><h2>Handoff documents and model</h2><p>'''+ ' · '.join(link(p,l) for p,l in [('project_handoff_FT01.pdf','Field guide PDF'),('shop_drawings_FT01.pdf','Shop drawings PDF'),('full_size_templates_FT01.pdf','1:1 A3 templates PDF'),('escutcheon_fit_trial_FT01.blend','Blender model')])+'''</p><div class="grid"><img src="paired_oblique.png" alt="Proposed pair on scanned travertine"><img src="exploded.png" alt="Exploded layer order; illustrative offsets"></div><p>Blender has three separate scenes: proposed exterior appearance, exploded order, and the actual new attached-plate scan. Official exterior forms do not establish hidden engagement. Exploded spacing is illustrative.</p><p>'''+ ' · '.join(link(p,l) for p,l in [('design_report.json','Dimensions and scoped checks'),('attached_scan_assessment.json','Attached-scan assessment'),('audit.json','Independent export/geometry audit')])+'''</p><p>Manufacturer references: '''+' · '.join(link(s['url'],s['label']) for s in H['source_links'])+'''</p></section></main><script>
    const p=document.querySelector('#plastic'),m=document.querySelector('#metal'),o=document.querySelector('#comparison');function update(){const a=Number(p.value),b=Number(m.value);if(!p.value||!m.value||a<=0||b<0){o.textContent='Enter both delivered totals; plastic must be greater than zero.';return}const r=b/a;o.textContent=`Metal is ${r.toFixed(2)}× plastic. `+(r<=2?'Within your suggested threshold: consider metal as the first fit trial if finish and arrival suit the visit.':'Above your suggested threshold: plastic is the cheaper learning step unless metal timing or finish justifies the difference.')}p.addEventListener('input',update);m.addEventListener('input',update);
    </script></html>'''
    (OUT/'index.html').write_text(expand(htmltext,V))

def packages():
    for stock,filename in [(V['stock'],f'{D["revision"]}_recommended_{V["stock"]}_quote.zip'),(V['alt_stock'],f'{D["revision"]}_plastic_{V["alt_stock"]}_quote.zip')]:
        parts=[p for p in R['parts'] if p['stock']==stock and p['kind'] in ['MAIN','DIV']]
        notes=('FT01 - QUOTE AND SACRIFICIAL FIT TRIAL ONLY\n'
          'Quantity: one MAIN[[main_od]] plus one DIV[[div_od]]. All coordinates mm. No assembly scaling.\n'
          'Thickness: '+str(parts[0]['thickness_mm'])+' mm. STEP solid is authoritative; DXF is a thickness-free mm cutting profile. STL coordinates are mm.\n'
          'Metal [[stock]]: quote 316 stainless, deburred and grain finished; compare 304 brushed if useful.\n'
          'Plastic [[alt_stock]]: [[alt_thickness]] mm clear acrylic or solid PETG/PLA; dry fit only. [[stock]] STL may also be printed for a thickness-matched trial.\n'
          'Confirm profile tolerance, flatness, actual thickness, finish, edges and delivery. No silent substitution.\n'
          'Remove cutting tabs (not mounting tabs), burrs and sharp edges. Uniform protected cosmetic face.\n'
          'No integral mounting tabs, threads, bends or countersinks. No kerf compensation in file.\n'
          'No permanent-installation release: actual factory fit, support, seal and water performance require on-site review.\n')
        selected=[OUT/p['files'][ext] for p in parts for ext in ['step','dxf','stl']]+[OUT/'shop_drawings_FT01.pdf']
        hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in selected}
        with zipfile.ZipFile(OUT/filename,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for p in selected:z.write(p,p.name)
            z.writestr('READ_ME.txt',expand(notes,V));z.writestr('SHA256.json',json.dumps(hashes,indent=2)+'\n')
        with zipfile.ZipFile(OUT/filename) as z:assert z.testzip() is None and len(z.namelist())==9
def run(design=None,report=None,output=None):
    configure(design,report,output)
    # Keep these true-size profiles away from the title and note column.
    # A different layout is required outside this explicitly supported range.
    assert max(V['main_od'],V['div_od'],V['fallback_od'])<=230, 'Profile exceeds current A3 layout'
    paths=[guide(),drawings(),templates()]
    counts={p.name:len(PdfReader(p).pages) for p in paths};assert list(counts.values())==[7,2,2]
    html_page();packages()
    (OUT/'document_check.json').write_text(json.dumps({'pdf_page_counts':counts,'paragraphs_within_page_bounds':True,'shop_and_template_units':'mm','templates_page_size':'A3 landscape','dimension_context':V,'visual_review':'pending'},indent=2)+'\n')
    print('FT01 documents, two private-free quote packages and local HTML built:',counts)
if __name__=='__main__':run()
