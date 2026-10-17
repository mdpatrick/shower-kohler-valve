"""Self-contained RF03 friend handoff; keep all scans/home photos out of ZIP."""
from pathlib import Path
import sys,json,hashlib,zipfile,html,shutil
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from PIL import Image,ImageDraw,ImageFont
OUT=ROOT/'deliverables/current/fabrication/FT02/formwork-print';PACK=OUT/'SEND_TO_PRINTER'
CFG=json.loads((ROOT/'canon/formwork_print_RF03.json').read_text())
R=json.loads((OUT/'geometry_checks.json').read_text());parts=R['parts'];p=parts[0]
font='/System/Library/Fonts/Supplemental/Arial.ttf';bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'

def textphoto(src,dst,title,subtitle):
 im=Image.open(src).convert('RGB');a=Image.new('RGB',(1440,1200),'#f0f6f8');a.paste(im,(0,80));d=ImageDraw.Draw(a)
 d.text((50,20),title,font=ImageFont.truetype(bold,34),fill='#173d4a');d.text((50,1120),subtitle,font=ImageFont.truetype(font,26),fill='#173d4a');a.save(dst)
textphoto(OUT/'D12_print.png',PACK/'PREVIEW.png','PRINT ONE: RF03 / 12 mm continuous collar','240 mm across | 8 mm face | 2 mm collar wall | 12 x 8 mm slots')
textphoto(OUT/'D24_RELIEVED_print.png',PACK/'OPTIONAL_DEEPER/PREVIEW.png','OPTIONAL INSTEAD: 24 mm relieved collar','Rear cutaways clear captured obstacles; continuous molding wall remains 12 mm.')

readme='''RF03 - SEND THIS FOLDER TO YOUR FRIEND

PRINT ONE PART, ONE TIME
Default: PRINT_ONE_RF03_D12.3mf
Fallback: PRINT_ONE_RF03_D12.stl
These two files describe the SAME part. Do not print both.
The 3MF is a generic, geometry-only model with explicit millimeter units.
If your slicer asks, import the geometry and keep your own printer profile.
STL is unitless: interpret its numbers as millimeters.

Required usable bed: 250 x 250 mm with the suggested 5 mm brim.
The actual form is 240 x 240 x 20 mm. It fits many 256 mm beds, subject
 to printer exclusion areas, clips and purge lines. A 220 mm bed is too small.
DO NOT scale it down or automatically shrink it to fit. Ask for a split
version if the printer cannot fit it; a joined seam needs separate design.

MATERIAL / STARTING SETTINGS
Unfilled PETG, one color; ordinary 0.4 mm nozzle; 0.20 mm layers;
5 wall loops; 1.2 mm solid top AND bottom (6 layers each);
25% gyroid or cubic infill; supports OFF; raft OFF; 5 mm brim.
Use your known PETG printer/material profile for temperatures and speed.
Dry filament as that brand requires. Use a suitable build surface/release
layer for PETG. Avoid a blind new speed/temperature profile.
The STL and 3MF already have the broad flat FRONT on the bed, collar UP.
Keep 100% scale. Center on the bed. The 2 mm collar should slice as walls;
inspect preview for intact slots, continuous skins and no unsupported islands.

WHAT THIS IS
A removable molding tool for a local repair around a shower-valve opening.
It is NOT the final decorative escutcheon, a permanent waterproof liner or
replacement valve hardware. The color areas in PREVIEW are explanatory;
print the entire object in one material/color.
The two 12 x 8 mm slots loosely locate on the bare rods after end-nut removal.
The form carries no repair load through those tabs. Use separate broad,
padded bracing. Do not pull it flat by tightening the rod nuts.
After printing, remove only brim/strings and any slot elephant-foot; do not
change the opening shape. Check face flatness and rehearse insertion and
straight withdrawal before using any repair material. Do not force a fit.

OPTIONAL_DEEPER is an alternative, not an additional required print.
Its collar reaches 24 mm but has two deliberate rear cutaways; the continuous
molding depth is still 12 mm. Total print size is 240 x 240 x 32 mm.
Use only if the owner deliberately chooses the deeper version and rehearses
its clearance/removal. D12 is the simpler first print.

CAD_REFERENCE contains editable STEP equivalents in the SAME print pose/mm.
They contain only one custom tool each, no house, wall or factory hardware.
PRINT_GUIDE.pdf explains the process. No G-code or machine settings are
embedded because the printer model is unknown. Friend slices locally.

Made 2026-10-17. RF03 is authorized for temporary-tool printing/dry fit.
Fit, bracing, repair-material suitability, release and final water sealing
are separate installation checks. All formwork/film/pads are removed.
'''
(PACK/'READ_ME_FIRST.txt').write_text(readme)
setting={k:v for k,v in CFG['print'].items()};(PACK/'PRINT_SETTINGS.json').write_text(json.dumps(setting,indent=2)+'\n')

# Concise print-pose section drawing for the physical handoff.
im=Image.new('RGB',(1440,560),'#f0f6f8');d=ImageDraw.Draw(im)
f=lambda n:ImageFont.truetype(font,n);bf=lambda n:ImageFont.truetype(bold,n)
d.text((45,20),'Orientation: the collar prints upward',font=bf(34),fill='#173d4a')
d.rectangle((100,440,1320,456),fill='#8298a0');d.text((490,480),'Printer bed - flat front face DOWN',font=f(28),fill='#173d4a')
d.rectangle((190,360,580,439),fill='#468fa0');d.rectangle((860,360,1250,439),fill='#468fa0')
d.rectangle((560,240,580,360),fill='#d3a044');d.rectangle((860,240,880,360),fill='#d3a044')
d.rectangle((580,409,660,439),fill='#a170b2');d.rectangle((780,409,860,439),fill='#a170b2')
d.text((210,307),'8 mm face',font=bf(30),fill='#173d4a');d.text((590,180),'12 mm collar',font=bf(30),fill='#173d4a')
d.text((915,205),'Collar wall: 2 mm',font=f(27),fill='#173d4a');d.line((930,240,880,280),fill='#173d4a',width=3)
d.text((600,87),'Slots in 3 mm tabs',font=f(28),fill='#173d4a');d.line((710,128,640,409),fill='#78508a',width=3)
d.text((45,527),'Schematic section, not to scale. Whole object prints in one color. Forming face is above the blue body.',font=f(21),fill='#42616b')
im.save(PACK/'ORIENTATION.png')

# PDF helpers - fixed layouts and explicit page breaks keep the guide short.
c=canvas.Canvas(str(PACK/'PRINT_GUIDE.pdf'),pagesize=(612,792));c.setTitle('RF03 - formwork print handoff');c.setAuthor('Shower escutcheon project')
navy=colors.HexColor('#173d4a');teal=colors.HexColor('#007b88')
style=ParagraphStyle('body',fontName='Helvetica',fontSize=10,leading=14,textColor=navy)
def para(txt,x,y,w=516,size=10):
 st=ParagraphStyle('local',parent=style,fontSize=size,leading=size*1.35);q=Paragraph(txt,st);_,h=q.wrap(w,700);q.drawOn(c,x,y-h);return y-h

def header(num,title,sub):
 c.setFillColor(navy);c.rect(0,702,612,90,fill=1,stroke=0);c.setFillColor(colors.white);c.setFont('Helvetica-Bold',23);c.drawString(42,751,title);c.setFont('Helvetica',11);c.drawString(42,725,sub)
 c.setFillColor(navy);c.setFont('Helvetica',8);c.drawString(42,24,'RF03 | 17 October 2026 | Temporary print / dry fit');c.drawRightString(570,24,f'{num} / 3')

def label(txt,y):
 c.setFillColor(teal);c.setFont('Helvetica-Bold',12);c.drawString(42,y,txt)

def image(p,x,y,w,h):c.drawImage(ImageReader(str(p)),x,y,width=w,height=h,preserveAspectRatio=True,anchor='c',mask='auto')

header(1,'Print this one','For the friend operating the printer | One part, one material')
y=para('<b>Open PRINT_ONE_RF03_D12.3mf.</b> If unsupported, use the matching STL in millimeters. Both are the same part; print one copy. The 3MF carries geometry only - keep your own printer profile.',42,681)
image(PACK/'PREVIEW.png',72,348,468,300)
label('Fit on the bed before starting',340)
y=para('<b>240 x 240 x 20 mm</b> model. Allow <b>250 x 250 mm usable area</b> with a 5 mm brim; check clips, purge lines and exclusion zones. A 220 mm bed cannot fit it. Keep <b>100% scale</b>; do not auto-shrink. If it does not fit, request a split design.',42,326)
label('Use these starting settings',y-24)
y=para('<b>Unfilled PETG</b> (one color), 0.4 mm nozzle, 0.20 mm layers, <b>5 walls</b>, <b>1.2 mm top and bottom skins</b>, <b>25% gyroid/cubic infill</b>, 5 mm brim. Supports OFF; raft OFF. Use the printer/filament maker\'s established PETG profile and bed-release advice.',42,y-36)
y=para('Files already sit flat, collar upward. Preview the layers: solid skins, intact 12 x 8 mm slots, collar made from continuous walls. No G-code is supplied because machine settings are unknown.',42,y-12)
para('<b>After printing:</b> remove brim and strings, clear only first-layer squeeze at slots, check the face against a flat surface and hand the whole print back to the owner. Avoid bending the tabs.',42,y-12)
c.showPage()

header(2,'Use & orientation','For the owner / installer | A removable tool, not the final escutcheon')
image(PACK/'ORIENTATION.png',42,466,528,205)
label('Keep the simple collar as the first choice',448)
y=para('<b>D12:</b> 12 mm continuous collar, 20 mm overall including the 8 mm face.<br/><b>Optional D24_RELIEVED:</b> 24 mm maximum depth, 32 mm overall. Two rear cutaways clear captured obstacles. Only the first 12 mm remains a continuous molding wall. Choose it instead of D12 only if deeper guidance is useful; rehearse clearance and removal.',42,432)
label('Before any fill',y-24)
y=para('1. Remove the rod-end nuts and trim as required. Protect the valve and stone. Locate loosely using the two smaller slots; never force the form over the nuts.<br/>2. Rehearse full-face seating and straight withdrawal toward the shower. The collar checks do not prove the broad face will sit flat on real stone.<br/>3. Use broad, padded independent bracing on the front annulus. Rods are alignment aids only. Do not tighten their nuts to carry repair load or pull a warped print flat.',42,y-40)
label('Repair and removal',y-24)
y=para('Use only with sound permanent backing and the installer-selected compatible repair system. Line with removable approximately 0.05 mm PE release film. Hand-place only the needed supported perimeter zones within the front 12 mm depth, outside the collar. Keep the central service space, rods and tabs free of fill. No pressure casting or hard tamping.',42,y-40)
y=para('After the repair reaches suitable stripping strength, remove the brace and withdraw the tool. Remove every plastic piece, film and pad. Inspect the repair, then dry-fit the actual trim/plates and resolve the separate surface sealing and curing detail. Nothing here is approved as a permanent waterproof liner.',42,y-12)
para('<b>The thinner face relies on the same independent support as RF02.</b> Print durability, actual seating and release have not been physically tested. Stop if it rocks, bows or catches; do not alter the travertine to make the tool fit.',42,y-12,size=9)
c.showPage()

header(3,'Budget & file choices','For the owner | Estimate in US dollars, not a vendor or labor quote')
label('A generous payment: $75 for one selected form',674)
y=para('This budgets a whole spool, ordinary setup/cleanup, power, wear and one failed attempt. It is intentionally more than the consumed-plastic cost. It assumes a hobby favor, not commercial shop labor or a new spool dryer/printer purchase.',42,656)
rows=[('Whole 1 kg PETG spool, delivery/tax allowance','$45'),('Electricity, drying and one retry allowance','$5'),('Wear and consumables allowance','$10'),('Setup / cleanup thank-you allowance','$15')]
y-=18
for a,b in rows:
 c.setFont('Helvetica',10);c.setFillColor(navy);c.drawString(48,y,a);c.setFont('Helvetica-Bold',11);c.drawRightString(556,y,b);y-=24
label('Material calculation',y-4)
rng=p['approximate_print']['planning_range_grams_with_brim_purge'];solid=p['solid_mass_upper_bound_g_at_density_1_30']
y=para(f'D12 planning estimate: <b>{rng[0]}-{rng[1]} g including routine brim/purge</b> with the stated settings. At the conservative $35/kg budget that is ${rng[0]*.035:.2f}-${rng[1]*.035:.2f} in plastic. Even a completely solid CAD body is about <b>{solid:.0f} g</b> before brim/purge. The optional deep collar adds only about {(parts[1]["solid_volume_mm3"]-p["solid_volume_mm3"])/1000*1.3:.0f} g if printed solid.',42,y-22)
y=para('These are geometry-based estimates, not an actual slicer report. Budget roughly 6-16 print hours per attempt; printer speed can move this substantially. Power assumption: 0.20 kW average x 16 h x $0.50/kWh = $1.60, plus drying/heat-up. A $5 allowance covers two such prints and about 1.5 kWh extra drying/heat-up. These are conservative budget inputs, not measured electricity use or a local utility tariff.',42,y-12,size=9)
label('Which files to send',y-24)
y=para('<b>Send the entire RF03_FRIEND_PRINT_PACKAGE.zip.</b> Root 3MF/STL = default D12. OPTIONAL_DEEPER = print-instead alternative. CAD_REFERENCE = editable STEP equivalents, each one tool solid, in the same millimeter print pose. PREVIEW and ORIENTATION identify the shape. No scans, home photos, wall assembly, factory parts or printer commands are included.',42,y-40)
label('Sources checked 17 October 2026',y-24)
y=para('Prusa standard PETG category displayed $25.49/kg sale listings; the budget uses $35/kg, not that sale or a checkout quote. Polymaker\'s PETG technical sheet lists 1.30 g/cm3. Prusa\'s PETG and infill guides support using suitable bed preparation and walls/infill rather than blindly making a solid print. Exact URLs and assumptions are in COST_ESTIMATE.json.',42,y-40,size=9)
for title,url in [('Prusa PETG catalog',CFG['sources'][0]['url']),('Polymaker PETG technical sheet',CFG['sources'][1]['url']),('Prusa PETG guide',CFG['sources'][2]['url']),('Prusa infill guide',CFG['sources'][3]['url'])]:
 y-=18;c.setFillColor(teal);c.setFont('Helvetica',9);c.drawString(42,y,title);c.linkURL(url,(42,y-2,360,y+11),relative=0)
c.save()

cost={'revision':'RF03','payment_recommendation_usd':75,'assumptions':CFG['cost_assumptions'],'sources':CFG['sources'],'parts':[{k:x[k] for k in ['id','solid_mass_upper_bound_g_at_density_1_30','approximate_print','CAD_volume_reduction_percent']} for x in parts]}
(PACK/'COST_ESTIMATE.json').write_text(json.dumps(cost,indent=2)+'\n')
(OUT/'cost_estimate.json').write_text(json.dumps(cost,indent=2)+'\n')

# Self-contained web page and a clean file-only ZIP.
body=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RF03 - Friend print package</title><style>body{{font:18px/1.55 system-ui,sans-serif;background:#f0f6f8;color:#173d4a;max-width:1080px;margin:auto;padding:24px}}h1{{font-size:38px}}a{{color:#006f83}}.box{{background:white;padding:24px;border-radius:14px;margin:20px 0}}img{{width:100%;height:auto}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #c5d4d8;text-align:left;padding:10px}}@media(max-width:700px){{.grid{{grid-template-columns:1fr}}h1{{font-size:30px}}}}</style><body><a href="../tab-refinement/index.html">TR03 / RF02 study</a><h1>Ready to send to your friend</h1><p>One temporary repair form with the smaller 12 x 8 mm locating slots. Print the continuous 12 mm collar first. The deeper relieved form is an optional alternative.</p><div class="box"><h2><a href="RF03_FRIEND_PRINT_PACKAGE.zip">Download the complete print package</a></h2><p>Generic 3MF, STL, editable STEP, illustrated PDF and exact settings. No wall assembly or scans.</p><p><a href="SEND_TO_PRINTER/PRINT_ONE_RF03_D12.3mf">Default 3MF</a> · <a href="SEND_TO_PRINTER/PRINT_ONE_RF03_D12.stl">Default STL</a> · <a href="SEND_TO_PRINTER/PRINT_GUIDE.pdf">Print guide</a></p><b>Print one, not both formats. Keep 100% size.</b></div><div class="grid"><div class="box"><img src="SEND_TO_PRINTER/PREVIEW.png" alt="Actual CAD of RF03 D12 with flat front face down and collar up"><p><b>Default: 240 x 240 x 20 mm.</b> Continuous 12 mm collar.</p></div><div class="box"><img src="SEND_TO_PRINTER/OPTIONAL_DEEPER/PREVIEW.png" alt="Actual CAD of optional deeper collar with rear cutaways"><p><b>Optional: 240 x 240 x 32 mm.</b> Reaches 24 mm in places; only 12 mm continuous.</p></div></div><div class="box"><h2>Less material; same collar and smaller slots</h2><p>The forming face is 8 mm rather than 12 mm. The collar stays 2 mm thick and the tabs 3 mm. This removes {p['CAD_volume_reduction_percent']:.1f}% of the solid CAD volume. Use 5 walls, 1.2 mm skins and 25% infill in PETG. The front annulus still needs independent padded bracing; the locating rods carry no repair load.</p><img src="SEND_TO_PRINTER/ORIENTATION.png" alt="Diagram of correct print orientation"></div><div class="box"><h2>Bed size and settings</h2><p>Allow <b>250 x 250 mm usable print area</b>, including 5 mm brim. A 220 mm bed is too small. Check clips and exclusion zones; do not shrink to fit. The 3MF has geometry only: use your friend's own printer and PETG profile. 0.4 mm nozzle, 0.20 mm layers, supports off, raft off. Read the PDF before printing.</p></div><div class="box"><h2>Venmo budget: $75</h2><p>Generous allowance for a whole delivered spool ($45), power/drying ($5), wear/consumables ($10), and setup/cleanup thank-you ($15), including material for one retry. Typical consumed plastic is much less: estimated {rng[0]}-{rng[1]} g, or ${rng[0]*.035:.2f}-${rng[1]*.035:.2f} at our conservative $35/kg input. Actual printer timing and charges are unknown.</p><p><a href="cost_estimate.json">Calculations and primary sources</a></p></div><div class="box"><h2>After printing</h2><p>Remove the rod-end nuts for placement. Rehearse full-face seating and straight withdrawal. Protect the valve; retain the separate supported repair/release procedure. Remove all tool, liner and pad material afterward. This is not the final decorative plate or a permanent waterproof liner.</p><p><a href="geometry_checks.json">Geometry checks</a> · <a href="capture_checks.json">Captured clearance scope</a> · <a href="audit.json">Fresh print audit</a> · <a href="RF03_print_forms.blend">CAD-only Blender views</a></p></div></body></html>'''
(OUT/'index.html').write_text(body)
manifest={'revision':'RF03','quantity':'Print one chosen variant, not every format','files':[]}
for f in sorted(PACK.rglob('*')):
 if f.is_file() and f.name!='MANIFEST.json':manifest['files'].append({'file':str(f.relative_to(PACK)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(PACK/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(OUT/'RF03_FRIEND_PRINT_PACKAGE.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(PACK.rglob('*')):
  if f.is_file():z.write(f,arcname='RF03_FRIEND_PRINT/'+str(f.relative_to(PACK)))
print('RF03 print guide, web review and clean friend ZIP generated.')
