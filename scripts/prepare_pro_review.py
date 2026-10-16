#!/usr/bin/env python3
"""Package GP04 clarification without changing the frozen FT01 geometry.

The archive is an inspection snapshot, not a runnable project or a shop packet.
Original images are placed in PDF pages without retouching or geometric edits.
"""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess
import zipfile
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables/current/gpt-pro-review/GP04'
PREVIOUS = ROOT / 'deliverables/current/gpt-pro-review/GP01'
SUPPLEMENTS = [
    ('docs/physical_checks/inner_plate_planarity_2026-10-15.json', 'User-confirmed coplanar inner-plate face measurements and high caliper confidence'),
    ('docs/decisions/measurement_scope_2026-10-15.json', 'Expert assembles; owner supplies only indispensable machining dimensions, at most a handful'),
    ('docs/decisions/machining_deliverables_2026-10-15.json', 'Minimal justified plate-only machining set; precise per-file instructions and fresh STEP content checks'),
]
TEXT = ROOT / 'docs/gpt_pro_review'
FT = 'deliverables/current/fabrication/fit-trial/'
BASELINE = 'fbe55d6475383feca03e9f337fbf6f450f336c89'
INK = HexColor('#203a43')
TEAL = HexColor('#116779')
PALE = HexColor('#eef4f5')
GREY = HexColor('#51656c')
GOLD = HexColor('#8c5b1b')
P = ParagraphStyle('body', fontName='Helvetica', fontSize=10.5,
                   leading=14, textColor=INK, spaceAfter=8)
SMALL = ParagraphStyle('small', parent=P, fontSize=8, leading=10)
HEAD = ParagraphStyle('head', parent=P, fontName='Helvetica-Bold',
                      fontSize=13, leading=17)

# Explicit, ordered evidence. Historical graphics are never called current CAD.
FIGURES = [
    ('Inner plate measured face', 'PLANAR FACE MEASUREMENTS / FRONT TOWARD HANDLES',
     'data/evidence/user/inner-plate-front-caliper-2026-10-14.png',
     'Measured within one plane; the owner considers the caliper readings highly accurate. No tip-depth correction applies. Width 130.35 mm; upper opening 48.46 mm; tape height 165.10 mm.',
     '106.39 mm is nearest-hole-edge gap; 11.71 mm is hole edge to outside rim; SW hole is 5.66 mm; NE diameter is unknown. Use the calipers ahead of scan estimates for these measured dimensions. Foam/depth readings are separate; no numerical accuracy bound was supplied.'),
    ('Decorative cover measured face', 'USER MEASUREMENTS / FRONT TOWARD HANDLES',
     'data/evidence/user/outer-plate-front-caliper-2026-10-14.png',
     'Outside diameter 7.25 inches = 184.15 mm. Upper opening 33.79 mm. The blue 46.25 mm is between nearest inside opening edges. Orange 35.23 mm runs from lower inside opening edge to outside bottom rim.',
     'Lower opening diameter and rear cavity are unmeasured. These front dimensions do not establish nut clearance, handle engagement or the installed center.'),
    ('Upper-right stud tip distances', 'USER CALIPER READINGS / THREE-DIMENSIONAL TIP DISTANCES',
     'data/evidence/user/installed-ne-stud-distances-2026-10-15.png',
     'U-NE = 51.40 mm; L-NE = 80.25 mm. These are 3D distances between end-tip centers at different depths. NE is the upper-right trim rod. Unequal depth makes a tip distance longer than its projection onto the tile plane.',
     'Additional supplied lengths: U-L = 80.00 mm and NE-SW = 109.80 mm. Do not use these directly as CAD hole spacing. Unlike the coplanar inner-plate face measurements on page 2, projected tip spacing needs the depth difference; stud axes at the backing plane remain separate.'),
    ('Lower-left stud tip distances', 'USER CALIPER READINGS / THREE-DIMENSIONAL TIP DISTANCES',
     'data/evidence/user/installed-sw-stud-distances-2026-10-15.png',
     'U-SW = 81.14 mm; L-SW = 54.70 mm. These join end-tip centers at different depths, not points in the tile plane. The 3D lengths exceed their tile-plane projections. SW is the lower-left trim rod.',
     'Do not use these directly as CAD hole spacing. The inner-plate face measurements on page 2 are coplanar and need no tip-depth correction. Here, depth differences are needed for projection; stud inclination and axis intersections at the backing plane are still unestablished.'),
    ('Rear installation context', 'ACTUAL USER PHOTOGRAPH / NO CAD RECONSTRUCTION',
     'data/evidence/user/rear-context-2026-10-15.jpeg',
     'Actual rear view of wood, valve and plumbing. The foam discussed elsewhere belongs to the removable front inner plate; no foam-filled rear cavity is claimed.',
     'The owner confirms rear rod contact with wood and conditionally prefers clearance behind the rods. This photograph does not supply a drilling depth, member classification or a clear route.'),
    ('Rear rod and wood relationship', 'ACTUAL USER PHOTOGRAPH / OWNER-CONFIRMED CONTACT',
     'data/evidence/user/rear-close-2026-10-15.jpeg',
     'The owner confirms the nominal 4.56 inch trim rods meet the wood. The desired remedy is inward trim-stud adjustment where feasible, after checking the other valve and handle depths.',
     'Nominal full rod length 115.824 mm is not exposed projection. The older guide gives 11.1125 mm maximum front projection from the finished wall; applicability and actual datums require confirmation. Do not convert this image into a wood drilling specification.'),
    ('Depth concern from the side', 'USER-SUPPLIED SCAN VIEW / QUALITATIVE DEPTH EVIDENCE',
     'data/evidence/user/depth-side-view-2026-10-14.png',
     'The projecting control tips and trim rods end at different Z depths. The original low-resolution side view is retained without inventing hidden geometry.',
     'Handle connection depth and trim-stud projection are separate constraints. The custom backing adds actual stock thickness plus effective bedding height. There is no established 5 mm engagement or waterproofing allowance.'),
    ('Real inner plate attached', 'SUPPLEMENTAL POLYCAM / SEPARATE WALL-NORMAL INSPECTION',
     FT + 'plane_front.png',
     'The real attached-plate capture shows stem centers apparently high inside visible hub rings. Approximate offsets are 3-4 mm in this inspection, not proven axis errors. Do not force visual concentricity.',
     'Scale was calibrated to the supplied 80 mm 3D U-L length. Outline width reads about 134.46 mm versus 130.35 mm caliper. This scan is not globally registered to the primary capture and cannot serve as a precision mounting jig.'),
    ('Current main aperture', 'FT01 PROPOSED GEOMETRY / ASSUMED FOAM AND LOWER OPENING',
     FT + 'access.png',
     'Main outside diameter 220 mm; centered vertical capsule 116.35 x 151.10 mm with R58.175 ends. Gold represents assumed edge-flush foam. The lower opening circle and some placement dimensions remain assumptions.',
     'The nominal extra land inside the 6 mm foam is only 1 mm. The smallest scoped projected hardware clearance is about 1.61 mm before unresolved scan/placement errors. These are review targets, not accepted field tolerances.'),
    ('Main and diverter size choice', 'FT01 PROPOSED PAIR / SCENARIO PLACEMENT',
     FT + 'sizes.png',
     'Recommended trial: main 220 mm and diverter 124/80 mm. The separate diverter fallback is 120/80 mm. Keep both backing circles concentric with their actual covers.',
     'Earlier placements predict only about 3-5 mm between the larger pair. These are scenarios, not an uncertainty range. The actual diverter seal footprint and paired clearance need the expert fit trial.'),
    ('Proposed appearance on the travertine', 'FT01 APPEARANCE / OFFICIAL EXTERIOR CAD REFERENCES',
     FT + 'paired_front.png',
     'Illustrative exterior appearance of both backing plates together on the primary captured travertine. Factory exterior forms are based on official CAD.',
     'Rendered finish, contact, engagement and sealing are not physical results. This image is useful for appearance; the critical hidden interfaces must be evaluated separately.'),
    ('Exploded layer illustration', 'FT01 PROPOSED ASSEMBLY / DISPLAY OFFSETS ONLY',
     FT + 'exploded.png',
     'Wall, proposed backing, factory inner plate/foam, cover and controls are separated for viewing. The real foam is attached to the inner plate. Display spacing is not installed spacing.',
     'Rods and nuts are omitted from this appearance view; it is not an assembly-path proof. The requested final schematics must include their actual envelopes behind the unperforated decorative cover and section both control connections.'),
    ('Earlier locating-tab experiment', 'HISTORICAL LOC01 / NOT A CURRENT ORDER FILE',
     'deliverables/current/fabrication/concentric-border-study/views/stud_locator_trial.png',
     'This earlier diagonal opening added metal tabs with hypothetical holes/axes. Red marks conditional captured-surface interference in insertion or seated trials. It is not the FT01 capsule design.',
     'The trial does not rule out every notch. A notch removes material; a tab adds it. Pro should independently assess restraint, adjustment, foam land, bearing, depth and complete insertion/removal before recommending a locator variant.'),
]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def para(c, text, x, y, width, style=P):
    p = Paragraph(escape(text).replace('\n', '<br/>'), style)
    _, h = p.wrap(width, 1000)
    if y - h < 38:
        raise ValueError(f'PDF page overflow: {text[:70]}')
    p.drawOn(c, x, y - h)
    return y - h


def base(c, title, category, num):
    w, h = A4
    c.setFillColor(white)
    c.rect(0, 0, w, h, stroke=0, fill=1)
    c.setFillColor(TEAL)
    c.rect(0, h - 9, w, 9, stroke=0, fill=1)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(32, h - 33, category)
    c.setFillColor(INK)
    c.setFont('Helvetica-Bold', 20)
    assert c.stringWidth(title, 'Helvetica-Bold', 20) <= w - 64
    c.drawString(32, h - 64, title)
    c.setStrokeColor(HexColor('#ccdadd'))
    c.line(32, 35, w - 32, 35)
    c.setFillColor(GREY)
    c.setFont('Helvetica', 8)
    c.drawString(32, 21, 'GP04 | 15 October 2026 | Measurement clarification; FT01 CAD unchanged')
    c.drawRightString(w - 32, 21, str(num))


def evidence_pdf():
    path = OUT / '03_VISUAL_EVIDENCE.pdf'
    c = canvas.Canvas(str(path), pagesize=A4, pageCompression=1, invariant=1)
    c.setTitle('Kohler shower backing plates - visual evidence for independent review')
    c.setAuthor('Shower escutcheon project')
    w, h = A4
    base(c, 'Choose the plate files to machine', 'REVIEW BRIEF / CURRENT DESIGN IS A FIT TRIAL', 1)
    y = h - 92
    sections = [
        ('A small, precise manufacturing set',
         'Pro must choose which main/diverter plate variants should actually be made and return exact file-by-file instructions. Each manufacturing STEP must contain one custom plate solid. Keep wall, valve and assembly references outside the fabricator package. Specify filenames, dimensions, purpose, stock, quantities, isolated previews and verification. The six current standalone candidates are listed in 06_PLATE_ONLY_FILE_GUIDE.txt.'),
        ('Who measures and assembles',
         'The expert is expected to assemble/install, not supply new CAD measurements. Measuring was difficult for the owner. Ask the owner for at most a handful of indispensable machining dimensions, only after using existing evidence and simpler design options. Each request needs the affected CAD decision, illustrated contacts and plane, easiest method and necessary precision. General field forms are optional; ordinary installation checks remain separate.'),
        ('Current proposal to challenge',
         'Main: diameter 220 mm, centered upright capsule 116.35 x 151.10 mm, end radius 58.175 mm. Diverter: 124 mm outside / 80 mm inside; 120 mm fallback. Stock: 1.524 mm metal or matching plastic; separate 3 mm plastic trial. No locators in the present files.'),
        ('Four decisions',
         'Choose the best aperture while preserving full foam support and real control access. Decide whether bolt notches or other locators are useful and feasible. Establish the minimum factory-fit and water-path checks for the expert. Specify the documents and file-level tests the agent should produce.'),
        ('Read the pictures according to their labels',
         'Inner-plate face dimensions were measured within one plane; the owner considers those caliper readings highly accurate. Installed tip distances span unequal depths and are 3D lengths. Proposed CAD and exploded pictures contain assumptions. GP04 clarifies this distinction; FT01 CAD is unchanged.'),
        ('What has not been established',
         'Physical handle attachment, compressed foam contact, sound support and retention, the final sealing detail, actual paired gap, and installed water performance remain open. The existing digital audit does not certify these. The nominal 1 mm extra foam land is particularly narrow.'),
        ('Use the separate text prompt',
         '01_PASTE_INTO_GPT_PRO.txt asks for a decision and a self-contained BEGIN AGENT INSTRUCTIONS block. 02_PROJECT_BRIEF.txt holds the full measured facts and current limitations. The visual pages supplement those files; they do not replace them.'),
    ]
    for title, body in sections:
        y = para(c, title, 32, y, w - 64, HEAD) - 5
        y = para(c, body, 32, y, w - 64) - 17
    c.showPage()
    mapping = []
    for page, (title, category, source, caption, limits) in enumerate(FIGURES, 2):
        base(c, title, category, page)
        # Preserve source bytes/pixels; only scale uniformly for page placement.
        im = ImageReader(str(ROOT / source))
        iw, ih = im.getSize()
        box_x, box_y, box_w, box_h = 32, 184, w - 64, 557
        factor = min(box_w / iw, box_h / ih)
        dw, dh = iw * factor, ih * factor
        c.setFillColor(PALE)
        c.roundRect(box_x, box_y, box_w, box_h, 5, stroke=0, fill=1)
        c.drawImage(im, box_x + (box_w - dw) / 2,
                    box_y + (box_h - dh) / 2, width=dw, height=dh, mask='auto')
        y = para(c, caption, 32, 170, w - 64) - 8
        y = para(c, limits, 32, y, w - 64) - 8
        short = source.replace(FT, 'FT01/')
        para(c, 'Source: ' + short, 32, y, w - 64, SMALL)
        mapping.append(dict(page=page, title=title, category=category,
                            repository_source=source, sha256=sha(ROOT / source),
                            size_bytes=(ROOT / source).stat().st_size,
                            rendering='Original image uniformly placed, no retouching; source pixels retained in repository'))
        c.showPage()
    c.save()
    reader = PdfReader(path)
    assert len(reader.pages) == len(FIGURES) + 1
    for i, page in enumerate(reader.pages, 1):
        assert 'GP04' in page.extract_text(), f'Missing footer on page {i}'
    return mapping


def sources():
    # Retain the GP01 inspection snapshot exactly; do not silently pull later
    # software maintenance or current canon into this evidence-only revision.
    with zipfile.ZipFile(PREVIOUS / '04_TECHNICAL_REFERENCE.zip') as z:
        manifest = json.loads(z.read('SNAPSHOT_MANIFEST.json'))
    assert manifest['source_commit'] == BASELINE
    return sorted(item['repository_source'] for item in manifest['files'])


def zip_bytes(archive, name, data):
    info = zipfile.ZipInfo(name, (2026, 10, 15, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def technical_zip(paths):
    items = []
    path = OUT / '04_TECHNICAL_REFERENCE.zip'
    with zipfile.ZipFile(PREVIOUS / '04_TECHNICAL_REFERENCE.zip') as old, \
            zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for rel in paths:
            data = old.read('repo_snapshot/' + rel)
            # Verify the retained snapshot against its original source commit.
            committed = subprocess.check_output(['git', 'show', BASELINE + ':' + rel], cwd=ROOT)
            if hashlib.sha256(data).digest() != hashlib.sha256(committed).digest():
                raise ValueError('Baseline has changed; revise snapshot context before packaging: ' + rel)
            dest = 'repo_snapshot/' + rel
            zip_bytes(z, dest, data)
            items.append(dict(path=dest, repository_source=rel, size_bytes=len(data),
                              sha256=hashlib.sha256(data).hexdigest()))
        supplements = []
        for rel, scope in SUPPLEMENTS:
            data = (ROOT / rel).read_bytes()
            dest = 'review_addenda/' + Path(rel).name
            zip_bytes(z, dest, data)
            supplement = dict(path=dest, repository_source=rel,
                              size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                              scope=scope + '; numeric R005 and FT01 CAD unchanged')
            items.append(supplement)
            supplements.append(supplement)
        snapshot = dict(source_commit=BASELINE, current_CAD='FT01',
                        scope='Inspection snapshot only; not a runnable checkout or vendor packet',
                        files=items,
                        baseline_files_unchanged_from='GP01',
                        post_baseline_addenda=supplements,
                        omitted='Raw scans, extracted/derived meshes, Blender file, runtime and nonselected history. See outer MANIFEST.json.')
        zip_bytes(z, 'SNAPSHOT_MANIFEST.json', (json.dumps(snapshot, indent=2) + '\n').encode())
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        for item in items:
            assert hashlib.sha256(z.read(item['path'])).hexdigest() == item['sha256']
    return items


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    texts = sorted(TEXT.glob('*.txt'))
    assert len(texts) == 5
    for p in texts:
        shutil.copyfile(p, OUT / p.name)
    figures = evidence_pdf()
    items = technical_zip(sources())
    scans = json.loads((ROOT / 'canon/inputs.json').read_text())['inputs']
    omitted = [{k: item[k] for k in ['id', 'repository_path', 'sha256', 'size_bytes']}
               for item in scans]
    blend = ROOT / FT / 'escutcheon_fit_trial_FT01.blend'
    omitted.append(dict(id='BLENDER-FT01', repository_path=str(blend.relative_to(ROOT)),
                        sha256=sha(blend), size_bytes=blend.stat().st_size))
    payload = [OUT / p.name for p in texts] + [OUT / '03_VISUAL_EVIDENCE.pdf', OUT / '04_TECHNICAL_REFERENCE.zip']
    manifest = dict(package='GP04', supersedes_review_package='GP03', project='shower-kohler-valve', date='2026-10-15',
                    baseline_commit=BASELINE, current_CAD='FT01', measurement_revision='R005',
                    status='INDEPENDENT_REVIEW_PROMPT_PACKAGE; CAD remains FOR_QUOTE_AND_DRY_FIT_ONLY',
                    actual_external_transmission=False, baseline_geometry_changed=False,
                    source_note='The 82 GP01 technical snapshot files remain byte-identical to the baseline commit. GP04 carries forward both measurement clarifications and adds the plate-only machining requirement, fresh STEP inspection and exact candidate file guide. Prompt, brief and PDF state the current requirements. Later software maintenance is not pulled into the snapshot.',
                    payload_files=[dict(path=p.name, sha256=sha(p), size_bytes=p.stat().st_size) for p in payload],
                    evidence_figures=figures, technical_snapshot_files=len(items),
                    omitted_local_assets=omitted,
                    omissions_note='Omitted assets remain in the local repository. No raw mesh recomputation is possible from this compact package alone.',
                    manifest_self_hash_note='Manifest excluded from its own hash to avoid circularity; outer ZIP verified separately.')
    write_json(OUT / 'MANIFEST.json', manifest)
    archive = OUT / 'GPT_PRO_PROMPT_PACKAGE_GP04.zip'
    members = payload + [OUT / 'MANIFEST.json']
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(members):
            zip_bytes(z, p.name, p.read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == {p.name for p in members}
        for p in members:
            assert hashlib.sha256(z.read(p.name)).hexdigest() == sha(p)
    audit = dict(package='GP04', zip_crc='PASS', all_member_hashes='PASS',
                 baseline_commit_byte_comparison='PASS', baseline_files_checked=len(items)-len(SUPPLEMENTS),
                 clarification_addenda=len(SUPPLEMENTS),
                 outer_archive_members=len(members), evidence_pages=len(figures) + 1,
                 archive_sha256=sha(archive), archive_size_bytes=archive.stat().st_size,
                 CAD_modified=False, physical_fit='NOT PERFORMED',
                 PDF_visual_review='REQUIRED AFTER BUILD')
    (ROOT / 'build/gpt-pro-review').mkdir(parents=True, exist_ok=True)
    write_json(ROOT / 'build/gpt-pro-review/package_check.json', audit)
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
