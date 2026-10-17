"""Reference overlays and optional RF01 setup; no new measurements inferred."""
import json,math,zipfile,hashlib
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from src.fabrication.fit_trial_documents import capsule
from src.fabrication.release_documents import header,para,scale_bars,prose,SMALL

def reference_profile(c,d,kind):
    c.setLineWidth(.6);c.setStrokeColor(HexColor('#198098'));c.setDash(3,3)
    od=d['main']['outer_diameter_mm'] if kind=='MAIN' else d['diverter']['outer_diameter_mm']
    cover=184.15 if kind=='MAIN' else 98.425
    c.circle(0,0,od/2*mm);c.setStrokeColor(HexColor('#686b70'));c.circle(0,0,cover/2*mm)
    if kind=='MAIN':
        f=d['foam'];cy=-.23
        c.setStrokeColor(HexColor('#b37f25'))
        for inset in [0,f['width_mm']]:
            w=f['outer_width_mm']-2*inset;h=f['outer_height_mm']-2*inset;r=f['outer_corner_radius_mm']-inset
            c.roundRect(-w/2*mm,(cy-h/2)*mm,w*mm,h*mm,r*mm)
        c.setStrokeColor(HexColor('#8b438f'))
        for y,diam,label in [(40.09,48.46,'U'),(-39.95,50,'L')]:
            c.circle(0,y*mm,diam/2*mm);c.setFont('Helvetica',9);c.drawString(4,y*mm+4,label)
    c.setStrokeColor(HexColor('#1a4852'));c.line(-6,0,6,0);c.line(0,-6,0,6)

def reference_templates(out,d):
    c=canvas.Canvas(str(out/'REFERENCE_OVERLAYS_LETTER.pdf'),pagesize=letter);page=0
    for row,(y0,y1) in enumerate([(-10,115),(-115,10)]):
        for col,(x0,x1) in enumerate([(-115,10),(-10,115)]):
            page+=1;header(c,f'MAIN reference / tile {row+1}{"AB"[col]}',page,kind='REFERENCE ONLY / 100%')
            para(c,'Do NOT cut these marks into the metal. Print at 100%; check both bars. Overlap 20 mm and join four crosses. Gray: factory cover. Gold: assumed corner shape of edge-flush foam. Purple: factory openings; lower diameter/centers remain reference assumptions.',36,695,540,SMALL)
            x,y=130,215;c.saveState();clip=c.beginPath();clip.rect(x,y,125*mm,125*mm);c.clipPath(clip,stroke=0);c.translate(x-x0*mm,y-y0*mm);reference_profile(c,d,'MAIN');c.setDash()
            for a in [-5,5]:
                for b in [-5,5]:c.line((a-2)*mm,b*mm,(a+2)*mm,b*mm);c.line(a*mm,(b-2)*mm,a*mm,(b+2)*mm)
            c.restoreState();scale_bars(c,95,90);c.showPage()
    header(c,'DIVERTER reference / 100%',5,kind='REFERENCE ONLY')
    para(c,'Gray cover D98.425 is manufacturer nominal. Blue backing D124 is selected. This shows a concentric border; it does not depict or certify the hidden rear-contact footprint. Cuttable D124/80 profile is in TEMPLATES_LETTER.',36,695,540,SMALL)
    c.saveState();c.translate(306,465);reference_profile(c,d,'DIV');c.restoreState();scale_bars(c,110,100);c.showPage();c.save()

def form_documents(out,d,form):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    spec=json.loads((Path(__file__).resolve().parents[2]/'canon/repair_form_design.json').read_text())
    t=d['stocks'][0]['thickness_mm']
    fig,ax=plt.subplots(figsize=(10,4.3))
    ax.add_patch(Rectangle((-18,59.225),18,48,fc='#dfb789',label='Supported cured repair / sound substrate'))
    ax.add_patch(Rectangle((.5,58.175),t,49,fc='#6b909b',label='Custom metal (bedding illustrative)'))
    ax.add_patch(Rectangle((.5+t,59.175),4,6,fc='#555',label='Factory foam / compression schematic'))
    ax.plot([0,0],[59.225,110],color='#333',lw=1);ax.annotate('All form, film and pads removed',xy=(0,80),xytext=(12,95),arrowprops={'arrowstyle':'->'},fontsize=11)
    ax.annotate('About 1.05 mm metal bridge at side\nActual support and gasket contact still checked',xy=(.5,58.7),xytext=(11,73),arrowprops={'arrowstyle':'->'},fontsize=10)
    ax.text(-17,51,'Valve / service opening stays empty',fontsize=10);ax.set(xlim=(-22,75),ylim=(45,115),xlabel='Z toward shower (mm)',ylabel='X from cover center (mm)');ax.set_title('After demolding: section at side, geometry schematic');ax.legend(loc='upper left',fontsize=8);ax.grid(alpha=.15);fig.tight_layout();fig.savefig(out/'engineering/form_after_removal.png',dpi=170);plt.close(fig)
    pages=[{'title':'RF01: decide before printing or filling','lead':'Repair contractor + Kohler installer. This optional tool is separate from the two plate orders. Use only if the plate trial exposes a real support gap.', 'image':'engineering/form_assessment.png','blocks':[
      ['Purpose and measured limits','One temporary PETG body: D240 face, 12 mm thick; 12 mm deep drafted collar, 118.35 x145.10 outside at front, 2 mm wall, 1 degree draft smaller toward the rear. Minimum interior is113.93 x140.68. Lined cast opening is118.45 x145.20 at the face. This is not the custom plate aperture.'],
      ['Choose this route only when useful','First trial the factory parts and the FT02 plates. If they have sound stable support, omit the form and preserve that support. Otherwise inspect the exposed rear substrate and permanent backing. Use RF01 for a small supported cementitious repair only after a free insert/withdraw rehearsal and service-tool check.'],
      ['What the analysis proves','The modeled collar and its inner face lip clear scoped captured surfaces in one working pose. It does not establish the full panel contact plane, every concealed surface, print strength, bond or cartridge extraction. Real pads must touch sound stone without rocking. No fill if the dry trial binds, shifts, or blocks service.'] ]},
      {'title':'RF01: set the front datum; fill from rear','lead':'Contractor | Tools: printed RF01, straightedge, 0.05 mm PE film/pads, two padded battens, stable brace, removable hardware cover, suitable permanent backing and repair material.','image':'REPAIR_FORM_TRIAL/RF01_isolated_preview.png','blocks':[
      ['Prepare and rehearse','Print the flat front face on the bed, collar upward. Smooth/line the molding surfaces; check face flatness target0.3 mm. Bench-test a small repair/film/PETG coupon for release and heat. Wrap the back molding face and outside collar in continuous removable0.05 mm PE; keep seams outside bearing zones and all release oils off stone.'],
      ['Hold from the front','Three matched removable0.05 mm contact pads near (+/-60,90) and(0,-102) in the cover-centered frame set the lined casting face at the existing sound-tile plane. They are not structural anchors. Clamp broad padded battens across the front at y=+/-90 to a stable brace with a sound reaction. No force on stems, rods or pipes; no tile drilling. Prove stability under light intended placement pressure.'],
      ['Fill only the required zones','Protect moving hardware with a removable cover. From rear, close exposed outer sides with removable shuttering. Hand-place repair into missing front12 mm bearing zones OUTSIDE the collar and within theD220 support area, bonded to prepared suitable substrate and securely supported permanent backing. Leave the central cavity, pipes, stops and service space empty. Do not ram material or bury a temporary part.'] ]},
      {'title':'RF01: cure, remove and inspect','lead':'A tool produces shape; suitable substrate, backing, workmanship and the complete seal system produce a usable repair. No permanent plastic remains.','image':'engineering/form_after_removal.png','blocks':[
      ['Material branch','Rapid Set Cement All is a candidate only on suitable sound cementitious substrate, with clean prepared surfaces and supported vertical work. Its datasheet permits featheredge to4 inches and generally45-90 F placement; follow the current bag/datasheet mix, SSD and curing instructions. Existing travertine or unknown board is not assumed a suitable bond substrate. If unsuitable, use supported matching stone/cement-board repair and a compatible bonding/waterproofing system. No new tile abrasion is authorized.'],
      ['Cure and strip are separate decisions','Cement All requires water curing for at least1 hour under its specified conditions; that is not permission to strip, load, seal or wet the shower after1 hour. Contractor confirms adequate strength, moisture and product-specific cure. Release brace and pull straight toward shower by the panel, using the rear-narrowing draft. Do not pry on tile or plumbing; stop if it binds. Remove every film, pad, cover and shutter.'],
      ['Check the finished repair','Inspect voids, adhesion, sound support, flatness and unchanged service opening. Repeat the complete factory/plate dry fit. Any repair visible inside the aperture must remain clear of control and tool envelopes. Resolve concealed waterproofing before sealing; then follow INSTALLATION_GUIDE for compatible seal/primer, cure, drain, function and separate supply/spray checks.'] ]}]
    prose(out,'REPAIR_FORM_SETUP',pages)
    dest=out/'REPAIR_FORM_TRIAL'
    drawing=[{'title':'RF01 temporary printed forming tool','lead':'Quantity1, PETG. One valid connected solid. Manufacturing geometry is in mm; this construction tool is not an escutcheon or a permanent insert.','image':'REPAIR_FORM_TRIAL/RF01_isolated_preview.png','blocks':[
      ['Geometry and orientation','Cover-centered X right/Y up; +Z toward shower. Face outerD240, panel12 thick. Molding plastic faceZ+0.05; frontZ+12.05; collar rearZ-11.95. Collar front outer118.35x145.10 with semicircular ends; nominal wall2, depth12, draft1 degree smaller at rear. Minimum internal113.931x140.681. No threads or embedded fasteners.'],
      ['Print and inspect','Flat front face on print bed; collar upward. Use solid bearing zones and dense face, without a hollow unsupported shell. Smooth and line molding face/outer collar; target molding-plane flatness0.3 mm. No certified force/temperature rating is implied. Read BOM, CHECKS and the setup sheet before field use.'],
      ['Conditional readiness','Geometric STEP/STL read-back passed; actual support, full panel seating, print/liner coupon, hardware/service clearance and clean withdrawal remain dry checks before any filling. Do not order with the plate pair by default.'] ]}]
    prose(out,'REPAIR_FORM_DRAWING',drawing)
    import shutil
    for fn in ['REPAIR_FORM_SETUP.pdf','REPAIR_FORM_DRAWING.pdf']:shutil.copy2(out/fn,dest/fn)
    (dest/'READ_ME.txt').write_text('RF01 optional temporary tool. Upload ONE of STEP or STL, quantity1, to a suitable PETG printing service. No price obtained. Read setup and check actual dry placement/removal before fill. All printed parts and film are removed. Does not change FT02 plate files.\n')
    files=[p for p in dest.iterdir() if p.is_file() and p.name!='SHA256.json'];(dest/'SHA256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
    with zipfile.ZipFile(out/'RF01_REPAIR_FORM_TRIAL.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(dest.iterdir()):z.write(p,'REPAIR_FORM_TRIAL/'+p.name)
