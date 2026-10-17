"""RF04 print selection, PDF and clean friend package. Geometry is built separately."""
from pathlib import Path
import json, shutil, hashlib, zipfile
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'deliverables/current/fabrication/FT02/formwork-small-bed'
PACK = OUT / 'SEND_TO_PRINTER'
CFG = json.loads((ROOT / 'canon/formwork_small_bed_RF04.json').read_text())
CHECK = json.loads((OUT / 'geometry_checks.json').read_text())
ZIPNAME = 'RF04_ORIGINAL_AND_SMALL_BED_PRINT_PACKAGE.zip'
SMALL = 'SMALL_RF04/RF04_SMALL_192_55_D24_RELIEVED_mm'
ORIGINAL = 'ORIGINAL_RF03/PRINT_INSTEAD_RF03_D24_RELIEVED'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def pdf():
    fonts = Path('/System/Library/Fonts/Supplemental')
    pdfmetrics.registerFont(TTFont('Guide', str(fonts / 'Arial.ttf')))
    pdfmetrics.registerFont(TTFont('GuideBold', str(fonts / 'Arial Bold.ttf')))
    pdfmetrics.registerFontFamily('Guide', normal='Guide', bold='GuideBold', italic='Guide', boldItalic='GuideBold')
    styles = getSampleStyleSheet()
    for name in ['Normal', 'BodyText', 'Title', 'Heading1', 'Heading2']:
        styles[name].fontName = 'Guide'
    styles['BodyText'].fontSize = 10
    styles['BodyText'].leading = 14
    styles['BodyText'].spaceAfter = 8
    styles['Title'].fontSize = 26
    styles['Title'].leading = 29
    styles['Title'].alignment = 0
    styles['Title'].textColor = colors.HexColor('#12303f')
    styles['Heading2'].fontName = 'GuideBold'
    styles['Heading2'].fontSize = 13
    styles['Heading2'].spaceBefore = 9
    styles['Heading2'].spaceAfter = 7
    styles.add(ParagraphStyle('Small', parent=styles['BodyText'], fontSize=8.5, leading=11))
    styles.add(ParagraphStyle('Caption', parent=styles['Small'], alignment=TA_CENTER))
    story = []
    def p(text, style='BodyText'):
        story.append(Paragraph(text, styles[style]))
    def picture(path, width):
        with PILImage.open(path) as im:
            w, h = im.size
        story.append(Image(str(path), width=width, height=width*h/w))
    def table(rows, widths):
        cells = [[Paragraph(str(v), styles['Small']) for v in row] for row in rows]
        t = Table(cells, colWidths=widths, hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#deedf0')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('TOPPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#c8d5d9'))]))
        story.append(t)
    p('Two sizes. Same relieved collar.', 'Title')
    p('RF04 small-bed alternate + unchanged RF03 original | October 17, 2026', 'Small')
    p('Take both files to the printer. Choose one size and one format for each physical print. The smaller version only trims the outside face; it keeps both screw tabs and the complete collar.')
    picture(OUT / 'comparison.png', 524)
    p('Left: original 240 mm face. Right: smaller 192.55 mm face. Same scale.<br/>Colors explain features; both are single-material PETG prints.', 'Caption')
    table([
        ['<b>Choose a size</b>', '<b>Original RF03</b>', '<b>Small alternate RF04</b>'],
        ['Finished size, mm', '240 x 240 x 32', '192.55 x 192.55 x 32'],
        ['Usable bed with 5 mm brim', '250 x 250 mm', '203 x 203 mm (rounded up)'],
        ['Minimum face width outside collar', '47.45 mm', '23.725 mm: exactly half'],
        ['Unchanged in both', '8 mm face; 2 mm collar wall; 3 mm tabs', '12 x 8 mm slots; 24 mm rear depth; first 12 mm continuous']
    ], [204,160,160])
    story.append(Spacer(1,8))
    p('Which file?', 'Heading2')
    p('<b>Small:</b> SMALL_RF04 / RF04_SMALL_192_55_D24_RELIEVED_mm.3mf<br/><b>Original:</b> ORIGINAL_RF03 / PRINT_INSTEAD_RF03_D24_RELIEVED.3mf', 'Small')
    p('Use the STL with the same name if the slicer cannot open the geometry-only 3MF. STL units are millimeters. STEP is an editable CAD alternative, not an additional part. Original RF03 files are byte-identical copies.', 'Small')
    p('The original continuous 12 mm-collar design remains in the earlier RF03 package. This package contains the two relieved 24 mm versions requested here.', 'Small')
    story.append(PageBreak())
    p('Print, locate, rehearse.', 'Title')
    p('Temporary repair form - remove it after use', 'Small')
    table([
        ['<b>Slicer setting</b>', '<b>Starting point</b>'],
        ['Material / profile', 'Unfilled PETG; use the friend\'s known filament and printer profile.'],
        ['Scale / orientation', '100%. Flat front face and tabs on bed; collar grows upward. Files already oriented.'],
        ['Nozzle / layer', '0.4 mm nozzle / 0.2 mm layers'],
        ['Walls / solid skins / infill', '5 walls / 1.2 mm top and bottom / 25% gyroid or cubic'],
        ['Brim / supports / raft', '5 mm / supports off after checking layer preview / raft off']
    ], [165,359])
    p('At the printer', 'Heading2')
    p('Confirm the preview shows one solid form at the listed size, lying flat. Use actual usable bed space after clips, exclusion zones and brim. A nominal 220 mm square bed can contain the small version if those exclusions allow it. Do not shrink the model to fit.')
    p('What the smaller face changes', 'Heading2')
    p('The collar keeps the same central service opening clear and guides repair toward that boundary. The smaller face controls less of the surrounding repair surface. Beyond its edge, establish the repair plane against sound tile with a straightedge or suitable additional temporary form. Do not assume the smaller face bridges or supports the full damaged opening.')
    p('How the screws help', 'Heading2')
    p('Remove the rod-end nuts for insertion. The unchanged slots provide coarse alignment with some play. They do not carry repair loads or prove exact centering. Independently support the face with broad padded bracing; do not tighten nuts to load the tabs or pull a distorted face flat.')
    p('Before any repair', 'Heading2')
    p('Rehearse seating and removal on the real hardware. Check flat contact, clearance, stable bracing and withdrawal without trapping the form. The rear reliefs mean only the first 12 mm is continuous; keep repair within that continuous molding zone. Protect the service opening, slots and valve parts. Use a compatible supported repair, not filler spanning an unsupported void.')
    p('After suitable cure, remove all formwork, release film and pads. Neither version is a permanent escutcheon or waterproof liner. Existing no-tile-cutting and factory trim/seal requirements remain in force.', 'Small')
    p(f'Material: the smaller CAD solid uses {CHECK["CAD_volume_reduction_percent"]:.1f}% less volume. Actual filament and time come from the slicer. The earlier $75 allowance covered one selected form plus a retry, not printing every alternative. Software checks verify files and retained geometry; physical fit, strength and water performance remain untested.', 'Small')
    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor('#b4c9ce'))
        canvas.line(44,35,568,35)
        canvas.setFont('Guide',8)
        canvas.setFillColor(colors.HexColor('#4b636c'))
        canvas.drawString(44,23,'RF04 / RF03 | FOR TEMPORARY TOOL PRINT AND DRY FIT | mm')
        canvas.drawRightString(568,23,f'{doc.page} / 2')
    SimpleDocTemplate(str(PACK / 'PRINT_GUIDE.pdf'), pagesize=(612,792),
        leftMargin=44,rightMargin=44,topMargin=36,bottomMargin=47,
        title='RF04 small-bed form and original - friend print guide',author='Shower Kohler project').build(story,onFirstPage=footer,onLaterPages=footer)

def main():
    shutil.copyfile(OUT / 'comparison.png', PACK / 'COMPARE_SIZES.png')
    shutil.copyfile(OUT / 'small_print.png', PACK / 'SMALL_RF04/PREVIEW.png')
    shutil.copyfile(OUT / 'original_print.png', PACK / 'ORIGINAL_RF03/PREVIEW.png')
    (PACK / 'READ_ME_FIRST.txt').write_text('''TAKE BOTH; CHOOSE ONE SIZE AND ONE FORMAT TO PRINT

SMALL ALTERNATE RF04: 192.55 x 192.55 x 32 mm.
  SMALL_RF04/RF04_SMALL_192_55_D24_RELIEVED_mm.3mf
  Or the identically named STL. STEP is editable CAD of the same part.
  Needs at least 203 x 203 mm usable bed with a 5 mm brim.

ORIGINAL RF03: 240 x 240 x 32 mm, unchanged original bytes.
  ORIGINAL_RF03/PRINT_INSTEAD_RF03_D24_RELIEVED.3mf
  Or the identically named STL. RF03_D24_RELIEVED_mm.step is the same part.
  Needs 250 x 250 mm usable bed with a 5 mm brim.

Both: 8 mm face, 2 mm collar wall, 3 mm tabs, 12 x 8 mm slots.
24 mm maximum relieved collar depth; first 12 mm is continuous.
The small form halves the minimum collar-to-edge face width, not diameter.

Open PRINT_GUIDE.pdf and COMPARE_SIZES.png. Print at 100% in millimeters.
Flat front face/tabs down, collar up; files already oriented.
Unfilled PETG; known printer/filament profile. 0.4 mm nozzle, 0.2 mm layer,
5 walls, 1.2 mm skins, 25% infill, 5 mm brim; supports/raft off after preview.
3MF contains geometry and mm units, no printer profile. No G-code supplied.

Slots align loosely; independent padded bracing carries loads.
Remove rod-end nuts before insertion. Rehearse seating, support and release.
Reduced face guides less repair area; use sound tile/straightedge or an
additional temporary form outside its edge. Remove ALL formwork after use.
Physical fit, strength and installed water performance are unverified.

The original RF03 package still also provides the continuous 12 mm version.
This package contains only the original and smaller relieved 24 mm versions.
STL, 3MF and STEP are alternatives, NOT three parts to print.
''')
    (PACK / 'PRINT_SETTINGS.json').write_text(json.dumps({'revision':'RF04','small':CFG['print'],
        'original':{'size_mm':[240,240,32],'usable_bed_with_brim_mm':[250,250]},
        'unchanged_features':CFG['preserved_geometry'],'use':CFG['use']},indent=2)+'\n')
    pdf()
    files = [{'file':str(p.relative_to(PACK)), 'bytes':p.stat().st_size, 'sha256':sha(p)}
             for p in sorted(PACK.rglob('*')) if p.is_file() and p.name != 'MANIFEST.json']
    (PACK / 'MANIFEST.json').write_text(json.dumps({'revision':'RF04','units':'mm',
        'status':CFG['status'],'parts':'Two size alternatives; choose one per physical print.',
        'files':files},indent=2)+'\n')
    with zipfile.ZipFile(OUT / ZIPNAME,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(PACK.rglob('*')):
            if p.is_file():
                zi=zipfile.ZipInfo('RF04_PRINT_OPTIONS/'+str(p.relative_to(PACK)),(2026,10,17,0,0,0))
                zi.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(zi,p.read_bytes())
    (OUT / 'index.html').write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RF04: original and smaller-bed repair form</title>
<style>body{{font:17px/1.55 system-ui;color:#193943;background:#f3f7f7;margin:0}}main{{max-width:1040px;margin:auto;padding:36px 24px 60px}}h1{{font-size:clamp(30px,5vw,48px);line-height:1.1;max-width:780px}}h2{{font-size:24px;margin-top:34px}}a{{color:#086477}}.lead{{font-size:21px;max-width:850px}}.button{{display:inline-block;background:#126477;color:white;padding:12px 18px;border-radius:9px;text-decoration:none;margin:4px 8px 6px 0}}img{{width:100%;border-radius:12px}}figure{{margin:20px 0}}figcaption{{font-size:14px;color:#46616a}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}article{{background:white;border:1px solid #ccdcdf;border-radius:14px;padding:22px}}.tag{{text-transform:uppercase;letter-spacing:.09em;font-size:13px;color:#526d76}}.large{{font-size:29px;font-weight:700}}.notice{{padding:20px;border-left:4px solid #d59b3f;background:#fff7e8}}li{{margin:8px 0}}code{{font-size:14px;overflow-wrap:anywhere}}@media(max-width:680px){{.grid{{grid-template-columns:1fr}}main{{padding:24px 17px}}}}</style>
<main><a href="../index.html">Project handoff</a> · <a href="../formwork-print/index.html">Original RF03 package</a>
<p class="tag">RF04 · Additional small-bed option · Temporary repair form</p><h1>Same collar and screw slots.<br>A smaller face for a smaller bed.</h1>
<p class="lead">The alternate trims only the outer circular face. The original 240 mm form is included unchanged. Take both to your friend's printer and choose the one that fits the usable bed.</p>
<a class="button" download href="{ZIPNAME}">Download both sizes · ZIP</a><a class="button" href="SEND_TO_PRINTER/PRINT_GUIDE.pdf">Print guide · PDF</a>
<figure><img src="comparison.png" alt="Actual CAD: original larger face at left, smaller face at right, identical collars and tabs at the same scale"><figcaption>Actual delivered CAD at the same scale. Blue: face. Gold: collar. Purple: locating tabs. All print as one PETG material.</figcaption></figure>
<div class="grid"><article><p class="tag">Original · RF03</p><div class="large">240 × 240 × 32 mm</div><p>250 × 250 mm usable bed with a 5 mm brim.</p><img src="original_top.png" alt="Original form from directly above"><p><a download href="SEND_TO_PRINTER/{ORIGINAL}.3mf">3MF</a> · <a download href="SEND_TO_PRINTER/{ORIGINAL}.stl">STL</a> · <a download href="SEND_TO_PRINTER/ORIGINAL_RF03/RF03_D24_RELIEVED_mm.step">STEP</a></p><p>Original files copied byte for byte.</p></article>
<article><p class="tag">Smaller alternate · RF04</p><div class="large">192.55 × 192.55 × 32 mm</div><p><strong>203 × 203 mm usable bed</strong> with a 5 mm brim.</p><img src="small_top.png" alt="Smaller form from directly above, collar and tabs unchanged"><p><a download href="SEND_TO_PRINTER/{SMALL}.3mf">3MF</a> · <a download href="SEND_TO_PRINTER/{SMALL}.stl">STL</a> · <a download href="SEND_TO_PRINTER/{SMALL}.step">STEP</a></p><p>{CHECK['CAD_volume_reduction_percent']:.1f}% less CAD volume. Actual filament/time depend on slicing.</p></article></div>
<h2>What “half the face” means here</h2><p>The narrowest face width outside the collar decreases from <strong>47.45 to 23.725 mm</strong>. The outside stays circular. This halves that overhang, rather than the whole diameter or area. The 8 mm face, 2 mm collar wall, 3 mm tabs, 12 × 8 mm slots, rear reliefs and 24 mm maximum collar depth are unchanged. The first 12 mm of the collar is continuous.</p>
<h2>Print one chosen size at 100%</h2><p>Use the 3MF or STL, not both as separate parts. Units are millimeters. The flat front face and tabs are already on the print bed; the collar grows upward. Use unfilled PETG, the friend's established profile, 0.2 mm layers, 5 walls, 1.2 mm skins and 25% infill. Inspect the sliced layers with supports off. Keep a 5 mm brim and no raft. Do not scale the geometry down to fit.</p>
<h2>How the smaller face guides the repair</h2><p>The collar still defines the central boundary: build the supported repair toward it while keeping the service opening clear. The smaller face guides a smaller surrounding area. Beyond its outer edge, establish flushness to sound tile separately with a straightedge or suitable additional temporary form.</p>
<div class="notice"><strong>The screws locate; bracing supports.</strong> The slots allow play. Remove rod-end nuts for insertion and visually align the form. Use broad padded independent support; do not tighten nuts to load the tabs or flatten a warped print. Rehearse full seating and removal before repair. All formwork, release film and pads are removed afterward.</div>
<h2>What has been checked</h2><p>STEP, STL and geometry-only 3MF are checked for size, connected geometry and matching volume. CAD comparisons verify the collar, tabs and slots are unchanged and only outer face material was removed. This does not prove physical seating, strength, repair compatibility or water sealing.</p>
<p><a href="geometry_checks.json">CAD checks</a> · <a href="audit.json">Fresh handoff audit</a> · <a href="RF04_original_and_small_forms.blend">Comparison Blender file</a></p><p>The original RF03 package still includes its continuous 12 mm collar. The final FT02 escutcheon plates remain separate and unchanged.</p></main></html>''')
    print(json.dumps({'zip':str((OUT/ZIPNAME).relative_to(ROOT)), 'package_files':len(files)+1, 'PDF':str((PACK/'PRINT_GUIDE.pdf').relative_to(ROOT))}))

if __name__ == '__main__':
    main()
