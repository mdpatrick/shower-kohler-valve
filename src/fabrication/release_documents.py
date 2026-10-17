"""FT02 audience-specific documents and plate-only packages, from active sources."""
from pathlib import Path
import json,math,html,sys,hashlib,shutil,zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter,A3,landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.fabrication.fit_trial_documents import capsule
from src.fabrication.fit_trial_spec import values
from src.fabrication.fit_trial import rr
from src.fabrication.ponoko import acrylic_path
INK=HexColor('#203942');BLUE=HexColor('#196779')
BODY=ParagraphStyle('Body',fontName='Helvetica',fontSize=10,leading=13.5,textColor=INK)
HEAD=ParagraphStyle('Head',parent=BODY,fontName='Helvetica-Bold',spaceAfter=4)
SMALL=ParagraphStyle('Small',parent=BODY,fontSize=8.5,leading=11)

def read(p):return json.loads((ROOT/p).read_text())
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def para(c,text,x,y,w,style=BODY):
 text=html.escape(text).replace('\n','<br/>');p=Paragraph(text,style);_,h=p.wrap(w,2000)
 if y-h<45:raise ValueError(f'Page overflow: {text[:80]} at {y-h}')
 p.drawOn(c,x,y-h);return y-h

def header(c,title,page,size=letter,kind='FIT TRIAL'):
 w,h=size;c.setFillColor(BLUE);c.rect(0,h-12,w,12,fill=1,stroke=0);c.setFont('Helvetica-Bold',9);c.drawString(36,h-34,'KOHLER SHOWER / FT02 / R006');c.setFont('Helvetica',8);c.drawRightString(w-36,h-34,kind)
 y=para(c,title,36,h-51,w-72,ParagraphStyle('title',parent=HEAD,fontSize=21,leading=24))
 c.setStrokeColor(HexColor('#bccfd4'));c.line(36,34,w-36,34);c.setFillColor(INK);c.setFont('Helvetica',7)
 c.drawString(36,22,'FOR QUOTE AND SACRIFICIAL FIT TRIAL | Physical fit and permanent use not established');c.drawRightString(w-36,22,str(page));return y-13

def picture(c,p,x,y,w,h):
 im=ImageReader(str(p));iw,ih=im.getSize();s=min(w/iw,h/ih);dw,dh=iw*s,ih*s
 c.drawImage(im,x+(w-dw)/2,y-dh,dw,dh,mask='auto');return y-dh

def prose(out,name,pages):
 c=canvas.Canvas(str(out/(name+'.pdf')),pagesize=letter);c.setTitle(name.replace('_',' '));htmlsections=[]
 for i,page in enumerate(pages):
  y=header(c,page['title'],i+1)
  y=para(c,page['lead'],36,y,540)-10
  image=page.get('image')
  if image:y=picture(c,out/image,36,y,540,145 if name=='ORDER_AND_NEXT_STEP' else 180)-10
  for heading,text in page['blocks']:
   y=para(c,heading,36,y,540,HEAD)-3;y=para(c,text,36,y,540)-9
  c.showPage()
  blocks=''.join('<h3>'+html.escape(a)+'</h3><p>'+html.escape(b).replace('\n','<br>')+'</p>' for a,b in page['blocks'])
  htmlsections.append('<section><h2>'+html.escape(page['title'])+'</h2><p class="lead">'+html.escape(page['lead'])+'</p>'+('<img src="'+image+'" alt="'+html.escape(page['title'])+'">' if image else '')+blocks+'</section>')
 c.save();(out/(name+'.html')).write_text(shell(name.replace('_',' '),''.join(htmlsections)))
 dump(out/(name+'.source.json'),pages)
 return out/(name+'.pdf')

def shell(title,body):return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>body{font:17px/1.55 system-ui;color:#233f49;background:#eef3f4;margin:0}main{max-width:980px;margin:auto;padding:28px}section{background:white;padding:30px;margin:22px 0;border-radius:10px}h1{font-size:38px;line-height:1.12}h2{color:#196779}h3{font-size:18px;margin-bottom:5px}p{margin-top:5px}img{max-width:100%;max-height:540px;display:block;margin:20px auto}a{color:#09677c}table{border-collapse:collapse;width:100%}td,th{padding:10px;border-bottom:1px solid #c4d4d9;text-align:left;vertical-align:top}.lead{font-size:19px}.badge{color:#7f5a24}code{font-size:13px;overflow-wrap:anywhere}@media(max-width:650px){main{padding:12px}section{padding:18px}h1{font-size:29px}}</style><main><p><a href="index.html">FT02 project home</a></p><h1>'+html.escape(title)+'</h1><p class="badge">Fit-trial release | Physical and permanent checks remain open</p>'+body+'</main></html>'

def profile(c,d,kind,scale=1):
 od=d['main']['outer_diameter_mm'] if kind=='MAIN' else d['diverter']['outer_diameter_mm']
 c.circle(0,0,od/2*mm*scale)
 if kind=='MAIN':capsule(c,0,0,d['main']['aperture_width_mm']*mm*scale,d['main']['aperture_height_mm']*mm*scale)
 else:c.circle(0,0,d['diverter']['aperture_diameter_mm']/2*mm*scale)

def shop(out,d,parts,route):
 dest=out/route;dest.mkdir(exist_ok=True);c=canvas.Canvas(str(dest/'SHOP_DRAWINGS.pdf'),pagesize=letter)
 for i,p in enumerate(parts):
  y=header(c,p['kind']+' - one flat custom plate',i+1,kind='SHOP DRAWING / mm')
  y=para(c,p['id'],36,y,540,SMALL)-10
  cx,cy=306,438;c.saveState();c.translate(cx,cy);c.setLineWidth(.9);c.setStrokeColor(BLUE);profile(c,d,p['kind'],.65)
  c.setStrokeColor(HexColor('#8da8b0'));c.setDash(4,3);c.line(-210,0,210,0);c.line(0,-215,0,215);c.restoreState()
  c.setFont('Helvetica',10);c.setFillColor(INK);c.drawCentredString(cx,cy+216,f'OD {p["diameter_mm"]:.2f} | quantity 1 | front view +Y up')
  c.drawString(390,cy+180,'+Y / grain');c.line(420,cy+155,420,cy+173)
  if p['kind']=='MAIN':dims=f'Centered vertical capsule {d["main"]["aperture_width_mm"]:.2f} x {d["main"]["aperture_height_mm"]:.2f}; ends R{d["main"]["aperture_radius_mm"]:.3f}; arc centers (0, +/-{d["main"]["straight_side_length_mm"]/2:.3f}). No mounting holes/tabs.'
  else:dims=f'Concentric through opening D{d["diverter"]["aperture_diameter_mm"]:.2f}. No mounting holes/tabs.'
  y=225
  for text in [dims,f'Thickness {p["thickness_mm"]:.3f} mm. Outer center X=Y=0; back Z=0; front Z={p["thickness_mm"]:.3f}. STEP is one solid. '+('Metal DXF is the finished profile, without customer kerf compensation. ' if route=='METAL_FIT_TRIAL' else 'Acrylic CUT DXF is compensated; STEP is the finished profile. ')+ 'All files use mm. View above is 65%, dimensions govern.',
   ('Ponoko #4 brushed304:1.52 mm nominal, catalog range1.44-1.64. Brushed one face; actual quote offers linear deburring on MAIN only. DIV has As-cut only. Safe edges, cosmetic face and matching grain still require confirmation/secondary finishing. Requested profile +/-0.13 mm.' if route=='METAL_FIT_TRIAL' else 'Ponoko clear acrylic: 1.50 mm nominal, catalog range 1.27-1.73. Dry-fit only. PONOKO_K020_CUT DXF uses 0.20 mm nominal kerf compensation; this drawing and STEP show FINISHED targets. No second compensation. Requested profile +/-0.25 mm.'),
   'Flatness target 0.5 mm; report actual stock thickness. Smooth/deburr both faces and all edges; remove cutting microtabs without altering profile. Protect cosmetic face; align grain +Y on both plates. No bends, threads or countersinks. These are requested shop targets, not supplier certifications.']:
   y=para(c,text,36,y,540,SMALL)-9
  c.showPage()
 c.save();return dest/'SHOP_DRAWINGS.pdf'

def scale_bars(c,x,y):
 c.setStrokeColor(INK);c.setFillColor(INK);c.setLineWidth(.6);c.line(x,y,x+100*mm,y);c.line(x,y,x,y+100*mm)
 for q in [0,100]:c.line(x+q*mm,y-3,x+q*mm,y+3);c.line(x-3,y+q*mm,x+3,y+q*mm)
 c.setFont('Helvetica',8);c.drawString(x+10,y-13,'100 mm X - measure this');c.saveState();c.translate(x-9,y+15);c.rotate(90);c.drawString(0,0,'100 mm Y - measure this');c.restoreState()

def templates(out,d):
 c=canvas.Canvas(str(out/'TEMPLATES_LETTER.pdf'),pagesize=letter);page=0
 for row,(y0,y1) in enumerate([( -10,115),(-115,10)]):
  for col,(x0,x1) in enumerate([(-115,10),(-10,115)]):
   page+=1;header(c,f'MAIN / tile {row+1}{"AB"[col]} / 100%',page,kind='US LETTER TILE')
   para(c,'Print at actual size (100%), not Fit. Check both 100 mm bars on EVERY page. Join matching crosses; adjacent tiles overlap by 20 mm. Cut ONLY the solid outer/aperture profile.',36,695,540,SMALL)
   x,y=130,215;c.saveState();clip=c.beginPath();clip.rect(x,y,125*mm,125*mm);c.clipPath(clip,stroke=0);c.translate(x-x0*mm,y-y0*mm);c.setStrokeColor(BLUE);c.setLineWidth(.7);profile(c,d,'MAIN')
   for a in [-5,5]:
    for b in [-5,5]:c.line((a-2)*mm,b*mm,(a+2)*mm,b*mm);c.line(a*mm,(b-2)*mm,a*mm,(b+2)*mm)
   c.restoreState();c.setStrokeColor(HexColor('#b4c4ca'));c.rect(x,y,125*mm,125*mm)
   scale_bars(c,95,90);c.showPage()
 page+=1;header(c,'DIVERTER / one sheet / 100%',page,kind='US LETTER TEMPLATE');c.saveState();c.translate(306,465);c.setStrokeColor(BLUE);profile(c,d,'DIV');c.restoreState();scale_bars(c,110,100);c.showPage()
 page+=1;header(c,'Reference overlay + removable gauges',page,kind='REFERENCE / NOT CUT PATH')
 para(c,'The main cover/gasket overlay uses the same 4-tile registration as the main profile; use REFERENCE_OVERLAYS_LETTER.pdf for the actual 100% overlay, or use the gauges below. Use from the FRONT, never as a spacer under foam. Nominal widths do not certify actual concentricity.',36,695,540,SMALL)
 para(c,'Main cover D184.15; nominal inner outline 130.35 x 165.10 with assumed R40 corners; foam band 6 mm at edge. These are REFERENCE marks only, not extra cuts in the metal. Main cutting outline D220, one capsule 116.35 x 151.10. Diverter cover nominal D98.425; custom ring D124/80.',36,630,540,SMALL)
 y=560
 for label,w in [('MAIN visible border',d['positioning_aid']['main_border_mm']),('DIV visible border',d['positioning_aid']['diverter_border_mm'])]:
  c.setFont('Helvetica-Bold',11);c.drawString(90,y,label+f': {w:.4f} mm');y-=50
  c.setStrokeColor(BLUE);c.rect(90,y,w*mm,35);c.setFont('Helvetica',9);c.drawString(90+w*mm+15,y+10,'Cut this card width; compare at four directions.');y-=50
 scale_bars(c,105,90);c.showPage();c.save()
 c=canvas.Canvas(str(out/'TEMPLATES_A3.pdf'),pagesize=landscape(A3))
 for i,kind in enumerate(['MAIN','DIV']):
  header(c,kind+' / full-size cutting profile',i+1,landscape(A3),'A3 / 100%');c.saveState();c.translate(180*mm,145*mm);c.setStrokeColor(BLUE);profile(c,d,kind);c.restoreState();scale_bars(c,300*mm,45*mm);c.showPage()
 c.save()

def assets(out,d):
 dest=out/'photos';dest.mkdir(exist_ok=True)
 shutil.copy2(ROOT/'data/evidence/user/installed-control-spacing-2026-10-15.png',dest/'front.png');shutil.copy2(ROOT/'data/evidence/user/rear-close-2026-10-15.jpeg',dest/'rear.jpeg')
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.patches import Circle,FancyArrowPatch
 fig,ax=plt.subplots(figsize=(8,4.8));ax.add_patch(Circle((0,0),110,fc='#d3e4e7',ec='#216578'));ax.add_patch(Circle((0,0),92.075,fc='#b8bdbd',ec='#4c5a5e'))
 for ang in [0,90,180,270]:
  a=math.radians(ang);p=(92.075*math.cos(a),92.075*math.sin(a));q=(110*math.cos(a),110*math.sin(a));ax.add_patch(FancyArrowPatch(p,q,arrowstyle='<->',mutation_scale=10,color='#b87023'))
 ax.text(130,30,'Use the same removable\ncard gauge at four sides.\n\nMain border: 17.925 mm\nDiverter: 12.7875 mm\n\nRemove all guides before\nsealing / final assembly.',fontsize=11,va='center');ax.text(0,0,'Real factory cover',ha='center',fontsize=11);ax.set(xlim=(-135,320),ylim=(-130,130));ax.set_aspect('equal');ax.axis('off');fig.tight_layout();fig.savefig(out/'centering.png',dpi=160);plt.close(fig)

def package(out,d,r,route,stock):
 dest=out/route;dest.mkdir(exist_ok=True);parts=[p for p in r['parts'] if p['stock']==stock and p['kind'] in d['selected_parts']]
 # These are generated route directories, not owner evidence. Remove only old
 # generator outputs to prevent obsolete stock files surviving a rebuild.
 for old in dest.iterdir():
  if old.is_file() and (old.name.startswith(d['revision']+'_') or old.name in ['SHOP_DRAWINGS.pdf','UPLOAD_LIST.txt','SHOP_NOTES.txt','SHA256.json','CUT_PATHS.json']):old.unlink()
 cuts=[]
 for p in parts:
  for fmt,rel in p['files'].items():
   if route=='CLEAR_FIT_TRIAL' and fmt=='dxf':continue
   shutil.copy2(out/rel,dest/Path(rel).name)
  if route=='CLEAR_FIT_TRIAL':cuts.append(acrylic_path(d,p,dest/(p['id']+'_PONOKO_K020_CUT.dxf')))
  shutil.copy2(out/'cad'/(p['id']+'_preview.png'),dest/(p['id']+'_preview.png'))
 shop(out,d,parts,route)
 suffix='_PONOKO_K020_CUT.dxf' if route=='CLEAR_FIT_TRIAL' else '.dxf'
 uploads='\n'.join(f'QTY 1 | {p["id"]}{suffix} | {p["kind"]} | thickness {p["thickness_mm"]:.3f} mm' for p in parts)+'\n'
 (dest/'UPLOAD_LIST.txt').write_text(uploads)
 notes=f'{d["revision"]} {route}\nOne MAIN plus one DIV, not every format. Upload the two DXFs in UPLOAD_LIST. STEP and STL are the intended finished parts, not additional order items.\n'
 notes+=(d['preferred_material']+'\nMetal DXF is the uncompensated finished profile; Ponoko automatically offsets its cutter.\n' if route=='METAL_FIT_TRIAL' else 'Clear acrylic 1.50 mm nominal. CUT DXFs are vendor-specific: outside +0.10 mm, inside -0.10 mm, for 0.20 mm nominal kerf. Do not apply a second compensation. STEP and drawing preserve finished dimensions. No 3 mm substitution or permanent-use claim.\n')
 notes+='No scaling, permanent tabs, threads, countersinks or bends. Follow SHOP_DRAWINGS. Confirm actual thickness, flatness, safe edges, cosmetic finish, price and arrival before purchase. Catalog stock is not a finish/flatness certification. No exact Kohler BN match. A fit trial is not a water-performance pass.\n'
 if cuts:dump(dest/'CUT_PATHS.json',cuts)
 (dest/'SHOP_NOTES.txt').write_text(notes)
 files=sorted(p for p in dest.iterdir() if p.is_file() and p.name!='SHA256.json');dump(dest/'SHA256.json',{p.name:sha(p) for p in files})
 zpath=out/(d['revision']+'_'+route+'.zip')
 with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(dest.iterdir()):z.write(p,route+'/'+p.name)
 return {'route':route,'zip':zpath.name,'sha256':sha(zpath),'upload_list':uploads,'files':len(files)+1}

def engineering(out,d,r,h):
 s=read(str((out/'engineering/locator_evaluation.json').relative_to(ROOT)));layout=s['layout'];tf=s['transforms'];budget=s['allowance_budget']
 pages=[{'title':'Accepted survey and registration','image':'sections.png','lead':'R006 selected planar calipers govern the two mounting holes. The source scan and historic observations remain intact.', 'blocks':[
  ['Final readings','DA 5.66; DB 5.66; FAX 119.17; FBX 16.38; FAY 61.40; FBY 108.85 mm. Contacts are TOP/LEFT blocks to FAR inside hole walls on the loose front face. FAX118.79 and FBY109.06 are superseded, not averaged.'],
  ['Derived layout','A (116.34,58.57), B (13.55,106.02) from LEFT/TOP, y down. In nominal outline-centered y-up frame: A (+51.165,+23.980), B (-51.625,-23.470). Center spacing 113.213456 mm; predicted edge gap 107.553456. Old edge gap 106.39 implies 112.05 centers and remains a 1.163456 mm disagreement, not an uncertainty bound.'],
  ['Working transform',f'Outline to cover translation {tf["inner_outline_to_cover_xy_up"]["translation_mm"]} mm, no reflection. Cover to installed translation {tf["cover_to_installed_xy_up"]["translation_mm"]}; rigid row rotation is recorded in engineering/locator_evaluation.json. This uses cover-edge calipers plus equal lower-bore and horizontal-centering assumptions and diagnostic cap picks; it is not a measured final pose.'] ]},
 {'title':'Locator choice and access','image':'engineering/locator_evaluation.png','lead':d['locator_decision'],'blocks':[
  ['Candidate geometry','Rounded tabs 15 mm wide, R1.5 roots. Round A / line-aligned slot B: widths 6.4, 7, 8 mm; lengths 9.4, 10, 11 mm. Both factory bores lie wholly inside the plain capsule, so tabs would add real inward material. A/bore orientation was checked; the slot follows the spacing vector.'],
  ['Budget','Nominal #10 crest 4.826 mm and factory bore5.66 give 0.417 mm factory radial play. A 7 mm custom hole adds1.087, totaling1.504 mm translational opportunity before cut error, depth-plane and pose variation. Nominal extra land is only1 mm INSIDE the approximately6 mm full gasket band. Slots cannot absorb arbitrary transverse error.'],
  ['Specific conflicts','The new full-source check includes low/boundary surfaces omitted by FT01. At illustrative1 mm bedding, the balanced tab has about0.51 mm2 seated captured-surface overlap; the present rod ends obstruct its insertion sweep. Removing/retracting studs may remove end conflicts but does not prove the unknown formed-hole-plane relation. Plain access avoids those added constraints.'] ]},
 {'title':'Coverage, support and remaining trial checks','image':'support_seal.png','lead':'Geometric source checks do not establish physical contact or water performance. Read the complete machine-readable study for every tested scope.','blocks':[
  ['Coverage and gap',f'Working-pose minimum projected outer margin across stored damage traces: {min(x["visual_outer_margin_mm"] for x in s["coverage"]):.2f} mm; pair gap {s["pair_gap_nominal_mm"]:.2f} mm. Historical poses remain separate. These are trace margins, not verified sound support. No new valve position is prescribed.'],
  ['Full-source scope','All primary source triangles were available; main local check uses un-eroded opening and Z=0 through80. Plain plate overlaps some low source topography at Z0; at1 mm illustrative bedding no in-opening projected interference is found. Real support must decide seating height. No hidden-back-face or water-tightness claim follows.'],
  ['Diverter','Rear factory plate is installed after the custom ring and need not pass through its aperture. Official exterior CAD does not define its rear contact. D124/80 remains a useful sacrificial trial with explicit complete rear-contact, screw engagement, support and tool-access checks; no actual pass is claimed.'],
  ['What remains physical','Factory engagement and cover centering, full foam/rear-contact landing, stable support and retention, neighbor gap, correct adapters/rod adjustment, service access, valid seal detail, cure, function/drain checks and separate plumbing/spray tests.'] ]},
 {'title':'Research and purchasing evidence','lead':'Public catalog and private Ponoko quote interface checked16 October2026. Selected part uploads authorized; no purchase or trade message.','blocks':[[x['label'],x['note']+'\n'+x['url']] for x in h['research'][:8]]}]
 # Research is chunked to keep source notes readable rather than squeeze them.
 pages=pages[:3]
 for i in range(0,len(h['research']),5):
  pages.append({'title':'Sources and purchasing evidence '+str(i//5+1),'lead':'Dated primary-source research; catalog claims and actual quotes are separate.','blocks':[[x['label'],x['note']+'\n'+x['url']] for x in h['research'][i:i+5]]})
 pages.append({'title':'Actual prices and order recommendation','lead':h['costs']['delivered_pair_prices'],'blocks':[['Recommended route',h['costs']['decision']],['Printed fallback',h['costs']['print_fallback']],['Live quote scope','Private formal PDFs are preserved locally; the vendor uses one mutable working cart. Separate metal/clear snapshots preserve what was priced. A cart link may later display a different alternative. No payment, staff message, or physical check occurred.']]})
 if (out/'engineering/form_assessment.json').exists():
  form=json.load(open(out/'engineering/form_assessment.json'));pages.append({'title':'Rear-fill form assessment','image':'engineering/form_assessment.png','lead':form['decision'],'blocks':[[k,v] for k,v in form['handoff_blocks']]})
 return prose(out,'ENGINEERING_RECORD',pages)

def run():
 d=read('canon/fit_trial_design.json');h=read('canon/fit_trial_handoff.json');out=ROOT/d['output_directory'];r=read(d['output_directory']+'/design_report.json');assets(out,d)
 from src.fabrication.release_support_documents import reference_templates,form_documents
 reference_templates(out,d)
 form_documents(out,d,read(d['output_directory']+'/engineering/form_assessment.json'))
 paths=[prose(out,n,h[k]) for n,k in [('ORDER_AND_NEXT_STEP','owner'),('PLUMBER_START_HERE','plumber'),('INSTALLATION_GUIDE','guide')]];paths.append(engineering(out,d,r,h));templates(out,d)
 packages=[package(out,d,r,'METAL_FIT_TRIAL',d['stocks'][0]['id']),package(out,d,r,'CLEAR_FIT_TRIAL',d['stocks'][-1]['id'])];dump(out/'packages.json',packages)
 (out/'PRE_VISIT_MESSAGE_DRAFT.txt').write_text('Draft only - not sent\n\nI have a Kohler K-2973-KS-NA with T14489-4-BN trim and a K-737-K-NA diverter with T14491-4-BN trim. I am bringing FT02 custom backing plates and the original trim parts. Please verify the correct adapter/screw/hub versions, adjust the trim studs (their rear ends contact wood), and dry-fit the complete supported assembly before any sealant. Please preserve the travertine and factory drain/service access. I need a practical support/seal/assembly check, not a new CAD survey. Bring/check appropriate adapters, screws and gasket parts. See PLUMBER_START_HERE and the repair-form assessment before any local support repair. If fit fails, a marked contact location and photo are enough to guide a revision.\n')
 body='<section><p class="lead">One selected plain main profile and one diverter, with separate material routes. No additional owner measurement is requested.</p><img src="paired_oblique.png" alt="Proposed appearance on source travertine"><p>'+html.escape(d['locator_decision'])+'</p><p><a href="FT02_METAL_FIT_TRIAL.zip">Metal pair ZIP</a> | <a href="METAL_FIT_TRIAL/UPLOAD_LIST.txt">Exact upload list</a> | <a href="FT02_CLEAR_FIT_TRIAL.zip">Clear alternative ZIP</a></p></section>'
 body+='<section><h2>Documents for the visit</h2>'+''.join('<p><a href="'+n+'.html">'+n.replace('_',' ')+'</a> | <a href="'+n+'.pdf">PDF</a></p>' for n in ['ORDER_AND_NEXT_STEP','PLUMBER_START_HERE','INSTALLATION_GUIDE','ENGINEERING_RECORD','REPAIR_FORM_SETUP'])+'<p><a href="TEMPLATES_LETTER.pdf">100% Letter tiles</a> | <a href="TEMPLATES_A3.pdf">A3 profiles</a> | <a href="REFERENCE_OVERLAYS_LETTER.pdf">Reference overlays</a> | <a href="escutcheon_fit_trial_FT02.blend">Blender scene</a></p></section>'
 body+='<section><h2>Factory order and actual geometry</h2><img src="exploded.png" alt="Exploded factory order"><img src="sections.png" alt="Actual captured sections"><p>Exploded offsets show order, not installed dimensions. Factory reference shapes are approximate; custom parts come from the STEP solids.</p></section>'
 body+='<section><h2>Actual attached inner plate</h2><img src="plane_front.png" alt="Original attached-state scan diagnostic"><p>Observed scan, kept separate from the proposed appearance. Manual wall-normal diagnostic and80 mm calibration are not independent scale validation. No forced registration or hidden engagement proof.</p></section>'
 body+='<section><h2>Pricing and timing</h2><p>'+html.escape(h['costs']['delivered_pair_prices'])+'</p><p>'+html.escape(h['costs']['decision'])+'</p><p>Ponoko is preferred. Use the current draft quote for lead, shipping and cost; finish and tax must be checked before purchase.</p></section>'
 if (out/'engineering/form_assessment.json').exists():
  f=json.load(open(out/'engineering/form_assessment.json'));body+='<section><h2>Removable rear-fill form</h2><p>'+html.escape(f['decision'])+'</p><img src="engineering/form_assessment.png" alt="Specific form feasibility study"><p><a href="RF01_REPAIR_FORM_TRIAL.zip">Separate optional tool files</a> | <a href="REPAIR_FORM_SETUP.html">Setup/removal instructions</a></p></section>'
 (out/'index.html').write_text(shell('A practical plate pair for the Kohler visit',body))
 pdfs=sorted(out.glob('*.pdf'))+sorted((out/'METAL_FIT_TRIAL').glob('*.pdf'))+sorted((out/'CLEAR_FIT_TRIAL').glob('*.pdf'))
 dump(out/'document_check.json',{'pdf_page_counts':{str(p.relative_to(out)):len(PdfReader(p).pages) for p in pdfs},'paragraph_layout':'bounds checked while generating','visual_review':'PENDING','sources':['canon/fit_trial_design.json','canon/fit_trial_handoff.json','src/fabrication/release_documents.py']})
 print('Audience documents and two isolated plate-order archives built.')
if __name__=='__main__':run()
