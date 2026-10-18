"""PS01: current print selection; copy verified geometry without remodeling it."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

ROOT = Path(__file__).resolve().parents[2]
FT = ROOT / 'deliverables/current/fabrication/FT02'
OUT = FT / 'selected-forms'
PACK = OUT / 'SEND_TO_PRINTER'
CFG = json.loads((ROOT / 'canon/formwork_selection.json').read_text())
PARTS = [
    dict(key='original', folder='01_PRIMARY_ORIGINAL_DEEP_240', stem='PRIMARY_ORIGINAL_240_D24_RELIEVED_mm',
         title='Primary: original face', size=[240,240,32], bed=[250,250], depth=24,
         source=FT/'formwork-small-bed/SEND_TO_PRINTER/ORIGINAL_RF03',
         sources={'stl':'PRINT_INSTEAD_RF03_D24_RELIEVED.stl','3mf':'PRINT_INSTEAD_RF03_D24_RELIEVED.3mf','step':'RF03_D24_RELIEVED_mm.step'},
         preview=FT/'formwork-small-bed/original_print.png'),
    dict(key='small', folder='02_PRIMARY_SMALL_DEEP_192_55', stem='PRIMARY_SMALL_192_55_D24_RELIEVED_mm',
         title='Primary: reduced outer face', size=[192.55,192.55,32], bed=[203,203], depth=24,
         source=FT/'formwork-small-bed/SEND_TO_PRINTER/SMALL_RF04',
         sources={ext:'RF04_SMALL_192_55_D24_RELIEVED_mm.'+ext for ext in ['stl','3mf','step']},
         preview=FT/'formwork-small-bed/small_print.png'),
    dict(key='optional', folder='03_OPTIONAL_SHORT_12MM', stem='OPTIONAL_SHORT_240_D12_mm',
         title='Optional only: short collar', size=[240,240,20], bed=[250,250], depth=12,
         source=FT/'formwork-print/SEND_TO_PRINTER',
         sources={'stl':'PRINT_ONE_RF03_D12.stl','3mf':'PRINT_ONE_RF03_D12.3mf','step':'CAD_REFERENCE/RF03_D12_mm.step'},
         preview=FT/'formwork-print/D12_print.png')
]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def guide():
    fonts = Path('/System/Library/Fonts/Supplemental')
    for name, filename in [('Guide','Arial.ttf'),('GuideBold','Arial Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(fonts/filename)))
    pdfmetrics.registerFontFamily('Guide', normal='Guide',bold='GuideBold',italic='Guide',boldItalic='GuideBold')
    ss=getSampleStyleSheet()
    for n in ['BodyText','Title','Heading2']:
        ss[n].fontName='Guide'
    ss['BodyText'].fontSize=9.5; ss['BodyText'].leading=13; ss['BodyText'].spaceAfter=7
    ss['Title'].fontSize=25; ss['Title'].leading=29; ss['Title'].alignment=0
    ss['Title'].textColor=colors.HexColor('#143f48')
    ss['Heading2'].fontName='GuideBold'; ss['Heading2'].fontSize=13; ss['Heading2'].spaceBefore=9
    ss.add(ParagraphStyle('Small',parent=ss['BodyText'],fontSize=8.5,leading=11))
    story=[]
    def p(t,s='BodyText'): story.append(Paragraph(t,ss[s]))
    def pic(path,w):
        with PILImage.open(path) as im: h=w*im.height/im.width
        story.append(Image(str(path),width=w,height=h))
    def table(rows,widths):
        t=Table([[Paragraph(str(v),ss['Small']) for v in row] for row in rows],colWidths=widths)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e0eeeb')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#c6d5d1'))]))
        story.append(t)
    p('The two selected deep forms', 'Title')
    p('PS01 / Owner selection / 17 October 2026 / Units: millimeters','Small')
    p('<b>Bring both primary designs.</b> The owner wants the deeper relieved collar with the original face AND the same deeper collar with the reduced outer face for a smaller printer bed. The separate short 12 mm model is optional only.')
    pic(FT/'formwork-small-bed/comparison.png',524)
    p('<b>Left:</b> primary original, 240 mm face. <b>Right:</b> primary smaller face, 192.55 mm. Actual CAD, same scale; colors explain features, not different print materials.','Small')
    table([['<b>Primary designs</b>','<b>Original RF03</b>','<b>Small RF04</b>'],['Overall size','240 x 240 x 32 mm','192.55 x 192.55 x 32 mm'],['Maximum collar depth','24 mm, relieved','24 mm, relieved'],['Usable bed with 5 mm brim','250 x 250 mm minimum','203 x 203 mm minimum'],['Minimum face width outside collar','47.45 mm','23.725 mm (half)']], [204,160,160])
    p('What the 12 mm number means','Heading2')
    p('Both selected deep forms keep an uninterrupted front 12 mm molding band. The collar extends to 24 mm where the rear clearance reliefs permit it. This <b>does not make them the short D12 model</b>. Overall print height is 32 mm: 8 mm face plus 24 mm maximum collar.')
    p('Use these filenames','Heading2')
    p('<b>01_PRIMARY_ORIGINAL_DEEP_240</b><br/>PRIMARY_ORIGINAL_240_D24_RELIEVED_mm.3mf<br/><b>02_PRIMARY_SMALL_DEEP_192_55</b><br/>PRIMARY_SMALL_192_55_D24_RELIEVED_mm.3mf','Small')
    p('Use the same-name STL if preferred. STEP is editable CAD. These are alternative formats of each part, not three parts to print. Names are clarified copies; geometry bytes match the checked RF03/RF04 originals.','Small')
    story.append(PageBreak())
    p('Print and use the selected forms','Title')
    table([['<b>Setting</b>','<b>Starting point</b>'],['Material / scale','Unfilled PETG, known printer/filament profile, 100% scale.'],['Orientation','Flat front face and tabs on the bed; collar grows upward. Files are pre-oriented.'],['Nozzle / layer','0.4 mm / 0.2 mm'],['Walls / skins / infill','5 walls / 1.2 mm top and bottom / 25% gyroid or cubic'],['Brim / support / raft','5 mm / supports off after inspecting layers / raft off']], [165,359])
    p('At the printer','Heading2')
    p('Confirm the selected dimensions in the slicer. Use actual clear bed area after clips and exclusion zones. Do not shrink either model to fit. Both deeper files are supplied; agree physical print quantities with the owner. Do not substitute the short version automatically. Geometry-only 3MF contains no machine settings; no G-code is supplied.')
    p('Locate, brace and rehearse','Heading2')
    p('Remove rod-end nuts for insertion. The 12 x 8 mm slots give coarse alignment and play. Support the face with independent padded bracing; do not load the 3 mm tabs or pull a warped face flat with the nuts. Rehearse seating and withdrawal on the actual hardware before any repair.')
    p('The smaller face guides less surrounding repair area. Use sound tile and a straightedge or additional temporary form beyond its edge. Keep rear repair in the continuous front 12 mm molding zone; protect the central service opening and do not encase valve parts. Remove all formwork, release film and pads after suitable cure. These are temporary tools, not final escutcheons or waterproof liners.')
    p('Optional extra: the short 12 mm form','Heading2')
    with PILImage.open(PARTS[2]['preview']) as im: ph=130*im.height/im.width
    image=Image(str(PARTS[2]['preview']),width=130,height=ph)
    text=Paragraph('<b>03_OPTIONAL_SHORT_12MM</b><br/>OPTIONAL_SHORT_240_D12_mm.3mf<br/>Same-name STL and STEP included.<br/><br/>240 x 240 x 20 mm overall.<br/>12 mm continuous collar; no rear reliefs.<br/>250 x 250 mm usable bed with brim.<br/><b>Included only as a backup.</b>',ss['Small'])
    t=Table([[image,text]],colWidths=[150,374]);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
    story.append(t)
    p('Physical fit, full-face support, print strength and repair suitability remain to be checked. Earlier RF03 files calling D12 the default or D24 optional are preserved history; this PS01 selection governs this handoff.','Small')
    def footer(c,d):
        c.setFont('Guide',8);c.setFillColor(colors.HexColor('#4b636c'))
        c.drawString(44,24,'PS01 | Temporary repair forms | Current owner selection | mm')
        c.drawRightString(568,24,f'{d.page} / 2')
    SimpleDocTemplate(str(PACK/'PRINT_THIS_GUIDE.pdf'),pagesize=(612,792),leftMargin=44,rightMargin=44,topMargin=35,bottomMargin=44).build(story,onFirstPage=footer,onLaterPages=footer)

def zip_files(dest, paths, base):
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(paths):
            if p.is_file(): z.write(p,p.relative_to(base).as_posix())

def main():
    PACK.mkdir(parents=True,exist_ok=True)
    mapping=[]
    for part in PARTS:
        folder=PACK/part['folder'];folder.mkdir(exist_ok=True)
        for ext,name in part['sources'].items():
            src=part['source']/name; dst=folder/(part['stem']+'.'+ext)
            shutil.copyfile(src,dst);assert sha(src)==sha(dst)
            mapping.append(dict(output=dst.relative_to(PACK).as_posix(),source=src.relative_to(ROOT).as_posix(),sha256=sha(dst),bytes=dst.stat().st_size))
        shutil.copyfile(part['preview'],folder/'PREVIEW.png')
        (folder/'READ_ME_FIRST.txt').write_text(f"{part['title'].upper()}\n\nMaximum collar depth: {part['depth']} mm. Overall dimensions: {' x '.join(map(str,part['size']))} mm.\nUsable bed with 5 mm brim: {' x '.join(map(str,part['bed']))} mm.\n\n"+('Owner selected this deeper relieved form as a primary design.\nThe first 12 mm remains continuous below the rear reliefs.\n' if part['depth']==24 else 'Optional backup only. The two relieved 24 mm forms are the primary choices.\n')+f"\nPrint {part['stem']}.3mf OR .stl, not both formats.\nSTEP is the same part for CAD editing. Units mm; 100% scale.\nUnfilled PETG; known printer profile; see PRINT_THIS_GUIDE.pdf.\nTemporary repair tool: rehearse fit/release and use independent padded bracing.\n")
    (PACK/'00_START_HERE.txt').write_text('CURRENT OWNER SELECTION: BOTH DEEPER RELIEVED FORMS\n\n01_PRIMARY_ORIGINAL_DEEP_240: 240 x 240 x 32 mm.\n02_PRIMARY_SMALL_DEEP_192_55: 192.55 x 192.55 x 32 mm.\nBOTH have a 24 mm maximum relieved collar and the same tabs/slots.\nThe first 12 mm is continuous below the rear reliefs, not a shorter model.\n\n03_OPTIONAL_SHORT_12MM: optional 240 x 240 x 20 mm D12 backup only.\nDo not make this the default or substitute it for the deeper forms.\n\nBring both primary design files; agree physical quantities at the printer.\nOne STL or 3MF per physical part; STEP is editable CAD. Millimeters, 100%.\nOpen PRINT_THIS_GUIDE.pdf and COMPARE_PRIMARY_FORMS.png.\nOld PRINT_INSTEAD / OPTIONAL_DEEPER filenames are superseded in this handoff.\nGeometry bytes are unchanged and traced in GEOMETRY_SOURCES.json.\n')
    shutil.copyfile(FT/'formwork-small-bed/comparison.png',PACK/'COMPARE_PRIMARY_FORMS.png')
    (PACK/'SELECTION.json').write_text(json.dumps(CFG,indent=2)+'\n')
    (PACK/'GEOMETRY_SOURCES.json').write_text(json.dumps(mapping,indent=2)+'\n')
    guide()
    manifests=[]
    for p in sorted(PACK.rglob('*')):
        if p.is_file() and p.name!='MANIFEST.json': manifests.append(dict(path=p.relative_to(PACK).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    (PACK/'MANIFEST.json').write_text(json.dumps(manifests,indent=2)+'\n')
    zip_files(OUT/'SELECTED_DEEP_FORMS_AND_OPTIONAL_SHORT.zip',PACK.rglob('*'),PACK)
    for part in PARTS:
        paths=list((PACK/part['folder']).rglob('*'))+[PACK/'PRINT_THIS_GUIDE.pdf',PACK/'SELECTION.json',PACK/'GEOMETRY_SOURCES.json']
        zip_files(OUT/(part['folder']+'.zip'),paths,PACK)
    audit={'revision':'PS01','status':'PASS','scope':'Packaging and source-byte identity; no geometry or physical-fit change','geometry_files_compared':len(mapping),'all_geometry_bytes_match':True,'primary':['original','small'],'optional':['short'],'download_testing':'Not performed, at owner request.'}
    (OUT/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit,indent=2))

if __name__=='__main__': main()
