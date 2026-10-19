"""RP01: illustrated English repair discussion. Does not alter CAD or physical status."""
from pathlib import Path
from io import BytesIO
import json
import math

from PIL import Image
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/pdf/Shower_Wall_Repair_Guide_EN_RP01.pdf'
RECORD = json.loads((ROOT / 'docs/research/rear_wall_repair_RP01.json').read_text())
OUT.parent.mkdir(parents=True, exist_ok=True)
FONTDIR = Path('/Users/mdpatrick/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fonts/truetype')
if (FONTDIR / 'LiberationSans-Regular.ttf').exists():
    pdfmetrics.registerFont(TTFont('Repair', str(FONTDIR / 'LiberationSans-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('RepairBold', str(FONTDIR / 'LiberationSans-Bold.ttf')))
    pdfmetrics.registerFontFamily('Repair', normal='Repair', bold='RepairBold', italic='Repair', boldItalic='RepairBold')
    FONT, BOLD = 'Repair', 'RepairBold'
else:
    FONT, BOLD = 'Helvetica', 'Helvetica-Bold'

W, H = 612, 792
INK, MUTED = HexColor('#20353E'), HexColor('#52676F')
TEAL, PALE = HexColor('#397784'), HexColor('#EDF4F4')
STONE, MORTAR = HexColor('#D8C6A5'), HexColor('#B6BDC0')
GASKET, SEAL = HexColor('#78618C'), HexColor('#308669')
AMBER, LIGHT = HexColor('#A66629'), HexColor('#FBF3E7')
LINE = HexColor('#D4E0E3')
c = canvas.Canvas(str(OUT), pagesize=(W, H), pageCompression=1)
c.setTitle('Shower wall repair from the back - English guide RP01')
c.setAuthor('Shower / Kohler project')
c.setSubject('Supported formed repair, removable tooling, local spray seals and checked Encinitas materials')
TEXT_LOG = []
PAGE = 0


def text(s, x, top, width, size=11.5, leading=16, color=INK, bold=False, maxh=None):
    p = Paragraph(s, ParagraphStyle('p', fontName=BOLD if bold else FONT, fontSize=size,
                                   leading=leading, textColor=color))
    _, height = p.wrap(width, 1000)
    if maxh is not None:
        assert height <= maxh + .1, (PAGE, s[:80], height, maxh)
    assert top-height >= 55, (PAGE, 'below footer', s[:80], top-height)
    p.drawOn(c, x, top-height)
    TEXT_LOG.append({'page': PAGE, 'text': s, 'bounds': [x, top-height, x+width, top]})
    return top-height


def tag(s, x, y, color=TEAL, size=8.5):
    c.setFont(BOLD, size); c.setFillColor(color); c.drawString(x, y, s)


def box(x, y, w, h, color=PALE):
    c.setFillColor(color); c.roundRect(x, y, w, h, 7, stroke=0, fill=1)


def pic(path, x, y, w, h):
    # Limit embedded photos to print-resolution copies; preserve all source bytes.
    with Image.open(ROOT/path) as original:
        iw, ih = original.size
        r = min(w/iw, h/ih)
        preview = original.convert('RGB')
        preview.thumbnail((round(iw*r*220/72), round(ih*r*220/72)), Image.Resampling.LANCZOS)
        encoded = BytesIO()
        preview.save(encoded, format='JPEG', quality=93, optimize=True)
    encoded.seek(0)
    c.drawImage(ImageReader(encoded), x+(w-iw*r)/2, y+(h-ih*r)/2,
                iw*r, ih*r)


def arrow(x1, y1, x2, y2, color=INK, width=1.3):
    c.setStrokeColor(color); c.setFillColor(color); c.setLineWidth(width)
    c.line(x1, y1, x2, y2)
    a = math.atan2(y2-y1, x2-x1)
    p = c.beginPath(); p.moveTo(x2, y2)
    p.lineTo(x2-7*math.cos(a-.45), y2-7*math.sin(a-.45))
    p.lineTo(x2-7*math.cos(a+.45), y2-7*math.sin(a+.45)); p.close()
    c.drawPath(p, stroke=0, fill=1)


def rect(x, y, w, h, color, stroke=None):
    c.setFillColor(color); c.setStrokeColor(stroke or color); c.setLineWidth(.7)
    c.rect(x, y, w, h, fill=1, stroke=bool(stroke))


def page(n, title, subtitle):
    global PAGE
    PAGE = n
    c.setFillColor(white); c.rect(0, 0, W, H, fill=1, stroke=0)
    tag('SHOWER / KOHLER', 42, 752)
    c.setFillColor(MUTED); c.setFont(FONT, 8)
    c.drawRightString(570, 752, 'REPAIR GUIDE RP01  |  ENGLISH  |  19 OCTOBER 2026')
    c.setStrokeColor(LINE); c.line(42, 737, 570, 737); c.line(42, 46, 570, 46)
    c.setFont(FONT, 8); c.drawString(42, 30, 'Rear-access repair  /  Preserve the travertine  /  Site detail to be confirmed')
    c.drawRightString(570, 30, f'{n} / 9')
    text(title, 42, 716, 528, 26, 29, bold=True, maxh=59)
    text(subtitle, 42, 645, 528, 11.5, 16, color=MUTED, maxh=48)


def step(n, title, body, x, top, width, maxh):
    c.setFillColor(TEAL); c.circle(x+10, top-10, 10, fill=1, stroke=0)
    c.setFillColor(white); c.setFont(BOLD, 10); c.drawCentredString(x+10, top-13, str(n))
    text(title, x+28, top, width-28, 13, 17, bold=True, maxh=34)
    text(body, x, top-43, width, 11, 15, maxh=maxh)


def source_note(s, top=82):
    text(s, 42, top, 528, 8.5, 11, color=MUTED, maxh=24)


# 1. Show actual condition and desired result. No generated image is evidence.
page(1, 'Rebuild a firm surface.\nKeep shower spray out.'.replace('\n','<br/>'),
     'A practical repair plan for the owner and repairer. Work from the rear, keep the existing stone, and remove the plastic form after curing.')
pic('deliverables/current/fabrication/FT02/photos/front.png', 42, 301, 250, 285)
pic('deliverables/current/fabrication/FT02/paired_oblique.png', 320, 301, 250, 285)
tag('NOW / ACTUAL OWNER PHOTO', 42, 285)
tag('GOAL / PROPOSED CAD APPEARANCE', 320, 285)
text('Missing material around the opening. The red dimension is an earlier 3D tip reading, not a repair dimension.', 42, 273, 250, 9, 12, color=MUTED, maxh=48)
text('Separate main and diverter plates behind the factory trim. This is a mockup, not completed or tested work.', 320, 273, 250, 9, 12, color=MUTED, maxh=48)
box(42, 114, 528, 109)
text('Recommended approach', 56, 207, 500, 14, 18, bold=True)
text('Use permanent support and a cement-based repair to rebuild the missing bearing surface. Then use the custom plate as the smooth landing for the original Kohler foam seal. Seal the new plate to sound stone around the damage.', 56, 181, 496, 11.5, 16, maxh=64)
text('Working assumption: RF05 fits and centers correctly. That does not by itself prove patch support, handle engagement or waterproofing. No new owner survey is requested.', 42, 101, 528, 9.3, 12, color=MUTED, maxh=36)
c.showPage()

# 2. Permanent layered assembly, explicit conceptual cross-section.
page(2, 'Three jobs, three different parts',
     'The wire may be lath: a way to help mortar hold together and stay in place. It is not the water barrier.')
for x, title, body, col in [
    (42, '1  SUPPORT', 'Permanent backing carries the repair after the plastic form is removed.', MUTED),
    (222, '2  SHAPE', 'Repair mortar fills missing areas and gives the plate a firm, flat seat.', AMBER),
    (402, '3  SEAL', 'The outer plate joint and factory gasket exclude shower spray.', SEAL)]:
    box(x, 510, 168, 86)
    tag(title, x+12, 577, col)
    text(body, x+12, 563, 144, 10.5, 14, maxh=56)
tag('ONE EDGE / CONCEPT, NOT TO SCALE', 42, 486)
# Larger section of one half of the ring, shower above and cavity below.
rect(65, 320, 168, 98, STONE)
rect(233, 365, 184, 53, MORTAR)
rect(233, 341, 184, 24, MUTED)
rect(147, 418, 296, 11, TEAL)
# Exposed edge fillet, rather than a sealant spacer that suspends the plate.
c.setFillColor(SEAL)
fillet = c.beginPath(); fillet.moveTo(134, 418); fillet.lineTo(147, 418)
fillet.lineTo(147, 430); fillet.close(); c.drawPath(fillet, stroke=0, fill=1)
rect(372, 429, 45, 20, GASKET)
rect(351, 449, 105, 7, HexColor('#7A858A'))
tag('SHOWER SIDE', 65, 455, MUTED)
arrow(87, 445, 87, 423, TEAL)
tag('WALL CAVITY', 438, 345, MUTED)
text('Open center<br/>for the valve', 442, 404, 100, 10, 13, color=MUTED, maxh=39)
tag('Existing stone', 77, 385, INK, 9)
tag('New repair', 255, 390, INK, 9)
tag('Permanent backing', 247, 349, white, 8)
text('Original inner plate<br/>and foam gasket', 350, 490, 181, 9.5, 12, maxh=24)
text('New custom plate', 315, 304, 160, 10, 13, color=TEAL)
arrow(409, 309, 437, 422, TEAL)
text('Continuous outer seal<br/>on sound stone', 65, 304, 180, 10, 13, color=SEAL)
arrow(97, 310, 141, 422, SEAL)
text('Backing connects to suitable framing/support outside this sketch. Existing hidden layers and their waterproofing are not identified by this drawing.', 42, 258, 528, 9.5, 13, color=MUTED, maxh=39)
box(42, 114, 528, 106, LIGHT)
text('A smooth mortar face is not automatically a watertight gasket seat.', 56, 204, 500, 12.5, 17, bold=True, maxh=34)
text('For this project, keep the planned custom plate between the repair and factory foam. If you want to omit that plate, establish a separate continuous, suitable sealed landing first. Do not press the foam onto rough or porous infill and assume the joint is waterproof.', 56, 164, 496, 11, 15, maxh=45)
source_note('Basis: project seal concept; Kohler inner-plate/foam/drain instructions [S6]. This is a local spray barrier, not certification of the concealed wall membrane.')
c.showPage()

# 3. Site inspection/structural support: no homeowner measurement demand.
page(3, 'First make the repair stay put',
     'Repairer: identify the exposed wall material, support and water-management layer from the existing rear access before choosing the attachment detail.')
pic('data/evidence/user/rear-context-2026-10-15.jpeg', 42, 354, 310, 235)
text('ACTUAL REAR PHOTO', 42, 341, 310, 8.5, 11, color=TEAL, bold=True)
text('The wood and pipes constrain access. The photo does not establish what every wall layer is, or whether a membrane connection survives.', 42, 325, 310, 9.5, 13, color=MUTED, maxh=39)
box(374, 354, 196, 235)
text('Keep clear', 387, 572, 170, 14, 18, bold=True)
text('Valve body and cartridges<br/><br/>Pipe joints and copper<br/><br/>Mounting rods and nuts<br/><br/>Handle/adapter access<br/><br/>The form removal path', 387, 543, 170, 11, 14, maxh=182)
text('If the existing cementitious edge is sound', 42, 267, 528, 13, 17, bold=True)
text('Provide a secure backer or anchored lath where needed. Lath must have mortar around both faces with suitable cover; keep it off copper. Preserve sound stone edges and faces. Neither a loose sheet of wire nor adhesion to an old edge is a complete support detail.', 42, 243, 528, 11, 15, maxh=60)
text('If the exposed board is soft, crumbly, gypsum or unsupported', 42, 175, 528, 13, 17, bold=True)
text('Build support from suitable framing/cleats, with a cement-board backer where practical. The repairer chooses screw positions, embedment and patch thickness at the wall. Do not anchor into unknown material or run screws toward pipes or through the travertine.', 42, 151, 528, 11, 15, maxh=60)
source_note('Do not use the valve, copper pipes or trim rods as patch supports. If no sound support or compatible waterproofing connection can be made from this access, revise that detail before filling. [S2, S3]', 82)
c.showPage()

# 4. Form and release.
page(4, 'Set the form. Rehearse removal.',
     'The printed plastic is temporary tooling. Its tabs locate it; independent padded bracing holds it steady during filling.')
pic('deliverables/current/analysis/tab-shafts-FS02/candidate_forms.png', 42, 363, 332, 236)
text('RF05 CAD: full 240 mm form at left; small-face alternative at right. The full form is the requested next print. Both show the relieved collar.', 42, 349, 332, 9, 12, color=MUTED, maxh=36)
box(390, 361, 180, 231, LIGHT)
text('24 mm is the<br/>maximum collar depth.', 403, 576, 154, 13, 17, bold=True, maxh=51)
text('Only the front 12 mm band is continuous. Rear reliefs are openings, not sealed mold walls.', 403, 516, 154, 11, 15, maxh=75)
text('Do not let mortar flow through a relief and harden behind the collar. That can trap the form.', 403, 434, 154, 11, 15, maxh=60)
step(1, 'Protect and release', 'Remove the factory trim/foam and removable rod nuts as needed. Protect valve openings. Line only the mold-contact faces with thin, smooth removable PE film. Keep oil, silicone release spray and adhesive residue off bonding and seal surfaces.', 42, 290, 250, 120)
step(2, 'Position and brace', 'Trial the lined tool and straight withdrawal first. Register both finished trim outlines together. Brace on protected sound surfaces; do not force the tool flat with the rods. Keep repair material outside the collar and clear of the tabs.', 320, 290, 250, 120)
box(42, 67, 528, 47)
text('The front 12 mm zone may guide the face repair. Any deeper backing or infill needs its own containment and removal plan. The main form is not a diverter form.', 55, 102, 502, 10, 13, maxh=39)
c.showPage()

# 5. Filling and curing.
page(5, 'Place a supported cement repair',
     'Candidate: Rapid Set Cement All, mixed with water. Use it only after the repairer confirms the actual substrate and support detail are suitable. [S1]')
step(3, 'Prepare before mixing', 'Clean the bonding substrate of loose material and contamination. Pre-wet suitable cementitious surfaces as the product directs, without standing water. Protect the room below. Complete the support, form release and small trial patch before the main fill.', 42, 584, 250, 120)
step(4, 'Fill from the rear', 'Hand-place and consolidate the needed repair zones against the lined face. Work mortar around properly embedded lath if used. Avoid air pockets. Keep the central valve cavity open; do not encase the plumbing or cast over the collar reliefs.', 320, 584, 250, 120)
# Simple top/bottom graphic makes direction unambiguous.
box(42, 282, 528, 103)
tag('SHOWER SIDE', 56, 361, TEAL)
rect(153, 306, 14, 55, TEAL)
rect(167, 310, 80, 47, MORTAR)
rect(247, 310, 12, 15, MUTED)
rect(247, 344, 12, 13, MUTED)
arrow(348, 334, 238, 334, AMBER, 2)
text('PLACE FROM REAR', 362, 355, 190, 11, 15, color=AMBER, bold=True)
text('Plastic face  |  New patch  |  Permanent support', 56, 301, 480, 8.5, 11, color=MUTED)
text('Leave access to pack the supported patch. Sketch shows a filling gap; it is not an attachment schedule.', 278, 324, 276, 9, 12, color=MUTED, maxh=36)
step(5, 'Follow the mix and cure', 'Measure water for the amount mixed; use the current bag directions. Work in manageable batches. Cement All sets quickly (about 15 minutes). Do not add water after it starts setting. Keep exposed repair surfaces moist for at least one hour, longer if required by conditions.', 42, 251, 250, 120)
step(6, 'Release without prying', 'The one-hour product strength claim is not a promise that this thin patch can be stripped safely. Let the repairer confirm release strength. Remove braces/nuts, withdraw toward the shower, and remove all film and shutters. Never lever against the travertine.', 320, 251, 250, 120)
source_note('Cement dust and wet cement require eye/skin protection and dust control. Keep curing water out of the cavity and off materials that must stay dry. Do not add unapproved bonding additives. [S1]', 84)
c.showPage()

# 6. Finish and water path, with a clear top-view seal diagram.
page(6, 'Finish the face and seal the water path',
     'After the form is removed, the patch must be firm, fully supported and free of release film. The plate should sit without rocking or being forced flat.')
text('Finish only the new material', 42, 586, 252, 14, 18, bold=True)
text('Remove ridges on the repair; fill voids with a compatible repair product. Keep the finished support at the intended tile-face plane. Do not grind or cut the existing travertine. Do not use silicone blobs to prop up an unsupported plate.', 42, 558, 250, 11, 15, maxh=105)
text('Dry-fit the complete stack', 320, 586, 250, 14, 18, bold=True)
text('Fit both custom plates and actual factory trim together. Check full foam contact, no plate-to-plate contact, nut clearance, handle engagement and free movement. Leave the central service opening accessible.', 320, 558, 250, 11, 15, maxh=105)
box(42, 269, 528, 160)
# front schematic: two circles for custom/factory, bottom factory drain only
c.setLineWidth(5); c.setStrokeColor(SEAL); c.circle(135, 349, 57, stroke=1, fill=0)
c.setLineWidth(3); c.setStrokeColor(MUTED); c.arc(95, 309, 175, 389, startAng=280, extent=340)
arrow(135, 311, 135, 294, TEAL)
text('Factory drain', 79, 291, 120, 9, 12, color=TEAL)
text('Outer green loop: new plate-to-stone seal', 224, 410, 330, 12, 16, color=SEAL, bold=True, maxh=32)
text('Keep this seal continuous and outside every over-cut. Use a stone-compatible sealant joint on clean, dry surfaces; verify adhesion to the actual metal finish and nonstaining on the stone.', 224, 370, 330, 10.5, 14, maxh=56)
text('Inner gray circle: factory decorative cover. Keep its bottom drain open so it drains onto the FRONT of the custom plate. Do not copy that gap into the new outer seal.', 224, 310, 330, 10, 13, maxh=39)
text('Sealant candidate: Custom Commercial 100% Silicone', 42, 247, 528, 13, 17, bold=True)
text('Use the actual joint dimensions, backing/primer requirements if any, and a small adhesion/staining trial. A paper-thin smear is not a joint design. The current TDS generally requires 24 hours at 70 F before water; allow longer where the material or conditions require it. [S4]', 42, 222, 528, 11, 15, maxh=60)
box(42, 71, 528, 66, LIGHT)
text('Do not flood the gap with sealant or permanently bond the factory trim, foam or serviceable valve parts into the opening. Keep the finished outer seal accessible for future maintenance.', 55, 123, 501, 10.5, 14, maxh=42)
c.showPage()

# 7. Explicit membrane limits, practical decision rather than generic disclaimer.
page(7, 'Waterproofing: close the whole route',
     'The repairer needs to distinguish a local trim seal from the wall\'s concealed waterproofing. This is an inspection during the work, not a new homeowner measurement assignment.')
box(42, 451, 528, 142)
text('If the existing waterproof layer is accessible', 57, 577, 498, 14, 18, bold=True)
text('Identify it and make a compatible, continuous repair to sound material, using that system\'s required overlaps, bonding, corners and cure. Protect that connection while installing the backer and patch. A rear lap must shed water in the correct direction; it cannot simply end at a gap.', 57, 545, 498, 11.5, 16, maxh=80)
text('If that layer cannot be reached without removing stone', 42, 425, 528, 14, 18, bold=True, maxh=36)
text('The custom plate and factory gasket can provide a maintainable local barrier to spray at this opening. They cannot establish that the hidden membrane has been restored, or stop water arriving behind the tile from elsewhere. If the exposed wall is wet, soft or has a broken water path, resolve that finding before closing or wet use.', 42, 378, 528, 11.5, 16, maxh=96)
text('Why I would not simply paint RedGard on the back', 42, 267, 528, 14, 18, bold=True)
text('RedGard is a real waterproofing membrane, but it needs a suitable sound substrate, continuity and a protected finish. Its TDS excludes unstable/wet surfaces and use as a wear surface. A coat on the rear of this patch does not seal its front edge or connect an unknown existing membrane. Do not treat bare RedGard under a removable cover as a manufacturer-approved detail without confirmation. [S5]', 42, 237, 528, 11, 15, maxh=90)
box(42, 68, 528, 66, LIGHT)
text('Choose the water-seal detail before mixing mortar. If that detail is unresolved, dry fitting and support planning can continue, but the repair is not ready for shower use.', 56, 120, 498, 11, 15, bold=True, maxh=45)
c.showPage()

# 8. Dated shopping page: all named HD items verified in selected store UI.
page(8, 'Materials available in Encinitas',
     'Home Depot #0660, 1001 N El Camino Real, Encinitas CA 92024. Website stock checked October 19, 2026, about 3:35-3:51 p.m. PDT. Pickup counts below are not reservations.')
items = RECORD['stock_checked']['items']
roles = [
    'Repair fill - after confirming sound substrate/support.',
    'Optional lath - anchored and embedded, never loose wire.',
    'Backer option - secure to suitable framing/cleats.',
    'Candidate finish seal - actual stone/metal test required.',
    'HOLD PURCHASE - only for an identified compatible detail.'
]
y = 590
for i, (item, role) in enumerate(zip(items, roles)):
    h = 82 if i < 4 else 89
    box(42, y-h, 528, h-7, LIGHT if i == 4 else PALE)
    text(f'<a href="{item["url"]}" color="#236A7A"><b>{item["name"]}</b></a>', 54, y-12, 394, 10.5, 14, maxh=28)
    text(f'${item["price_usd"]:.2f}', 464, y-12, 94, 15, 18, bold=True, maxh=18)
    text(role, 54, y-43, 390, 9.3, 12, maxh=24)
    text(f'{item["quantity_shown"]} in stock<br/>Aisle {item["aisle"]}, bay {item["bay"]}', 456, y-38, 104, 9, 12, color=MUTED, maxh=24)
    text(f'SKU {item["store_sku"]}', 54, y-65, 250, 8, 10, color=MUTED, maxh=10)
    y -= h
text('The first four full packages total $72.10 before tax.', 42, 164, 528, 12.5, 17, bold=True)
text('Buy lath and board only as needed for the chosen support. This is a package-price subtotal, not a job quote; tools, fasteners, release film, blocking, labor and any membrane work are extra.', 42, 139, 528, 10.5, 14, maxh=42)
text('Repairer brings: compatible corrosion-resistant fasteners, any specified board-joint materials, thin PE release film, padded braces, mixing/finishing tools, protection and PPE. Avoid drywall compound, expanding foam, grout or thin-set used as bulk cavity fill.', 42, 91, 528, 9.2, 12, color=MUTED, maxh=36)
c.showPage()

# 9. Compact handoff, cure/test criteria, primary links.
page(9, 'Crew checklist and references',
     'The owner supplies the form and desired final trim position. The repairer handles support and the repair detail. The Kohler specialist handles correct factory assembly. No new CAD survey is assigned.')
checks = [
    'Before filling: support is sound; the water-seal route is decided; all hardware and service areas stay clear.',
    'Lined form seats and withdraws; bracing is independent; collar reliefs cannot trap mortar.',
    'After stripping: all temporary pieces are removed; patch has no loose edge, major void, crack or rocking.',
    'Both finished plate outlines fit together without touching; factory foam lands continuously and handles work.',
    'New outer seal is continuous; factory bottom drain is open; all specified curing is complete.',
    'With rear access open, apply normal controlled shower spray to the assembled trim. Stop and trace any new moisture. Inspect again after the test; record date and result.'
]
y = 587
for s in checks:
    c.setStrokeColor(TEAL); c.setLineWidth(1); c.rect(43, y-12, 10, 10, fill=0, stroke=1)
    y = text(s, 64, y, 506, 10.5, 14, maxh=42) - 12
text('A dry fit or one spray test does not certify the whole concealed shower wall. Keep the seal accessible and inspect it during maintenance.', 42, y, 528, 9.5, 13, color=MUTED, maxh=26)
y -= 45
text('Sources - click the titles for current instructions', 42, y, 528, 12.5, 17, bold=True)
y -= 26
for s in RECORD['sources'][:6]:
    title = s['title'].replace(' and technical data', '')
    text(f'<a href="{s["url"]}" color="#236A7A">[{s["id"]}] {title}</a>', 42, y, 528, 9.3, 12, maxh=24)
    y -= 23
text('Photographs: owner-supplied project evidence. Form and finished-pair pictures: existing project CAD renders. Colored sections are explanatory sketches, not evidence of hidden construction. RF05 and metal CAD are unchanged by this guide.', 42, y-3, 528, 9, 12, color=MUTED, maxh=36)
c.showPage()
c.save()

pages = PdfReader(OUT).pages
assert len(pages) == 9
alltext = '\n'.join(p.extract_text() for p in pages)
for required in ['72.10', '12 mm', '24 hours', 'RF05', '24 in stock', 'RedGard']:
    assert required in alltext, required
assert all(p.extract_text().strip() for p in pages)
qa = ROOT / 'tmp/pdfs/repair-guide-RP01'
qa.mkdir(parents=True, exist_ok=True)
(qa/'text_bounds.json').write_text(json.dumps(TEXT_LOG, indent=2)+'\n')
(qa/'extracted.txt').write_text(alltext)
print(OUT)
print('9 pages; required content and text bounds checked. Render review still required.')
