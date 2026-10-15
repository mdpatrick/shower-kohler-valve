"""Blank, revision-bound field record. Never imports observations into canon.

The JSON schema describes the same fields as the interactive PDF. Values remain
strings so an observer's raw reading, units and qualifiers survive transcription.
"""
from pathlib import Path
import hashlib
import html
import json

from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from pypdf import PdfReader

from src.fabrication.fit_trial_spec import validate_design

INK = HexColor('#203942')
BLUE = HexColor('#1c6578')
LINE = HexColor('#93adb5')
PALE = HexColor('#f2f7f8')
STATUS = ['NOT RECORDED', 'PASS', 'FAIL', 'UNRESOLVED', 'N/A']
WIDTH, HEIGHT = A4
LEFT, RIGHT = 36, A4[0]-36
SPAN = RIGHT-LEFT
STYLE = ParagraphStyle('field-text', fontName='Helvetica', fontSize=9,
                       leading=12, textColor=INK)


class Record:
    def __init__(self, design, directory):
        validate_design(design)
        self.design, self.directory = design, Path(directory)
        self.revision = design['revision']
        self.path = self.directory/f'expert_visit_record_{self.revision}.pdf'
        self.c = canvas.Canvas(str(self.path), pagesize=A4)
        self.c.setTitle(f'{self.revision} - Expert visit and actual fit record (blank)')
        self.c.setAuthor('Shower escutcheon project')
        self.fields = {}
        self.page = 0

    def text(self, text, y, x=LEFT, width=SPAN, bold=False, size=9):
        p = Paragraph(html.escape(text).replace('\n','<br/>'),
                      ParagraphStyle('p', parent=STYLE, fontSize=size,
                                     leading=size+3, fontName='Helvetica-Bold' if bold else 'Helvetica'))
        _, h = p.wrap(width, HEIGHT)
        assert y-h > 44, f'Field record page {self.page} overflow: {text}'
        p.drawOn(self.c, x, y-h)
        return y-h

    def begin(self, title, subtitle):
        self.page += 1
        c = self.c
        c.setFillColor(BLUE); c.rect(0, HEIGHT-14, WIDTH, 14, fill=1, stroke=0)
        c.setFont('Helvetica-Bold',9); c.drawString(LEFT,HEIGHT-36,'SHOWER ESCUTCHEON REPAIR / '+self.revision)
        c.setFont('Helvetica',8); c.drawRightString(RIGHT,HEIGHT-36,'BLANK FIELD RECORD / 15 OCT 2026')
        y = self.text(title, HEIGHT-55, bold=True, size=22)-9
        y = self.text(subtitle, y)-10
        c.setStrokeColor(LINE); c.line(LEFT,35,RIGHT,35)
        c.setFillColor(INK); c.setFont('Helvetica',7)
        c.drawString(LEFT,23,'Permanent installation is not released by this blank form. Record actual observations.')
        c.drawRightString(RIGHT,23,f'{self.page} / 4')
        return y

    def field(self, name, label, x, top, width, height=21, *, check=None,
              multiline=False, options=None, tooltip=None):
        assert name not in self.fields
        bottom = top-12-height
        assert bottom > 44, f'Field {name} outside page: {bottom}'
        self.text(label, top, x, width, size=8.3)
        options = list(options) if options else None
        default = 'NOT RECORDED' if options and 'NOT RECORDED' in options else ''
        self.fields[name] = dict(label=label, page=self.page, check_id=check,
                                 type='choice' if options else 'text', default=default,
                                 options=options, tooltip=tooltip or label)
        common = dict(name=name, tooltip=tooltip or label, x=x, y=bottom,
                      width=width, height=height, fontName='Helvetica', fontSize=9,
                      borderWidth=.65, borderStyle='solid', borderColor=LINE,
                      fillColor=PALE, textColor=INK, forceBorder=True)
        if options:
            self.c.acroForm.choice(**common, options=options, value=default, fieldFlags='combo')
        else:
            self.c.acroForm.textfield(**common, value='', maxlen=600 if multiline else 120,
                                     fieldFlags='multiline' if multiline else '')
        return bottom-10

    def row(self, y, fields):
        gap = 10
        width = (SPAN-gap*(len(fields)-1))/len(fields)
        bottoms = []
        for i, item in enumerate(fields):
            name, label, *args = item
            bottoms.append(self.field(name,label,LEFT+i*(width+gap),y,width,**(args[0] if args else {})))
        return min(bottoms)

    def note(self, name, label, y, height=38, check=None):
        return self.field(name,label,LEFT,y,SPAN,height,check=check,multiline=True)

    def status_row(self, name, check, label, y):
        self.text(check+'  '+label, y-3, LEFT, 194, size=8.5)
        self.field(name+'_status','Result',LEFT+201,y,112,height=20,check=check,options=STATUS)
        self.field(name+'_evidence','Observation / photo ref.',LEFT+322,y,SPAN-322,height=20,check=check)
        return y-40

    def section(self, label, y):
        self.c.setFillColor(PALE); self.c.rect(LEFT-4,y-19,SPAN+8,20,fill=1,stroke=0)
        return self.text(label,y-3,bold=True,size=10)-13

    def finish_page(self):
        self.c.showPage()

    def save(self):
        assert self.page == 4
        self.c.save()
        design_sha = hashlib.sha256(json.dumps(self.design,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        schema = dict(schema_version=1, project_id='shower-kohler-valve',
                      design_revision=self.revision, record_revision='FR01',
                      design_sha256_canonical_json=design_sha,
                      purpose='Blank field record; no evidence or release is created by generating or completing this form.',
                      result_semantics={'NOT RECORDED':'No result supplied',
                                        'PASS':'Observer found the stated check satisfied; method and evidence required',
                                        'FAIL':'Observed failure; record the conflict and dependent work to stop',
                                        'UNRESOLVED':'Could not verify, including hidden interfaces',
                                        'N/A':'Observer must explain why the check does not apply'},
                      fields=self.fields,
                      interpretation='Preserve raw values and attach dated evidence. Agent review must reconcile these with the current design; no automatic acceptance or canonical import.')
        (self.directory/'field_record_schema.json').write_text(json.dumps(schema,indent=2)+'\n')
        blank = dict(project_id='shower-kohler-valve',design_revision=self.revision,
                     record_revision='FR01',purpose='BLANK TEMPLATE - NO PHYSICAL RESULTS',
                     design_sha256_canonical_json=design_sha,
                     schema_file='field_record_schema.json',
                     values={name:f['default'] for name,f in self.fields.items()},
                     attachments=[], physical_fit='NOT PERFORMED', permanent_installation_release=False)
        (self.directory/'field_record_blank.json').write_text(json.dumps(blank,indent=2)+'\n')
        return self.path


def profiles(r, y):
    """Small geometric reference, not a scale template or observed installation."""
    c = r.c; d = r.design
    m, v = d['main'], d['diverter']
    scale = .62
    cx, cy = 130, y-83
    c.setStrokeColor(INK); c.setLineWidth(.9)
    c.circle(cx,cy,m['outer_diameter_mm']*scale/2,fill=0,stroke=1)
    w,h = m['aperture_width_mm']*scale,m['aperture_height_mm']*scale
    rad, offset = w/2,(h-w)/2
    p = c.beginPath();p.moveTo(cx-rad,cy-offset);p.lineTo(cx-rad,cy+offset)
    p.arcTo(cx-rad,cy+offset-rad,cx+rad,cy+offset+rad,180,-180)
    p.lineTo(cx+rad,cy-offset);p.arcTo(cx-rad,cy-offset-rad,cx+rad,cy-offset+rad,0,-180);p.close()
    c.drawPath(p)
    c.setFont('Helvetica-Bold',9);c.setFillColor(BLUE)
    c.drawCentredString(cx,cy+79,'MAIN / UP')
    c.drawString(cx-84,cy,'A'); c.drawCentredString(cx,cy+5,'B <-->')
    c.drawString(cx+rad+5,cy,'C')
    c.line(cx,cy+h/2,cx,cy+h/2-5);c.line(cx,cy-h/2,cx,cy-h/2+5)
    c.drawCentredString(cx,cy-82,'A = outside / B = opening width / C = height')
    cx = 344
    c.circle(cx,cy,v['outer_diameter_mm']*scale/2,fill=0,stroke=1)
    c.circle(cx,cy,v['aperture_diameter_mm']*scale/2,fill=0,stroke=1)
    c.drawCentredString(cx,cy+57,'DIVERTER')
    c.drawString(cx-52,cy,'D');c.drawCentredString(cx,cy-3,'E <-->')
    c.drawCentredString(cx,cy-64,'D = outside / E = opening')
    r.text('T = thickness\nMeasure at several places.\nCompare flatness on a\nknown-flat reference.',cy+30,438,112,size=8)
    return y-180


def build(design, output):
    r = Record(design,output)
    m,v = design['main'],design['diverter']
    y = r.begin('1. Identify and inspect the parts',
                'Use a copy during the expert visit or incoming inspection. Record actual readings in mm unless stated. Keep entries concise; attach extra notes/photos and check the saved form before printing.')
    y = r.row(y,[('record_id','Record ID / date'),('observer','Observer / company'),('order_reference','Vendor / order reference',{'check':'P15'})])
    y = r.row(y,[('part_ids','Received part IDs / revision',{'check':'P15'}),('material_stock','Material / thickness / finish ordered',{'check':'P15'})])
    y = profiles(r,y)
    stocks=' or '.join(f'{s["id"]} ({s["thickness_mm"]:.3f} mm)' for s in design['stocks'])
    y = r.text(f'Design reference: A {m["outer_diameter_mm"]:g}; B {m["aperture_width_mm"]:.2f}; C {m["aperture_height_mm"]:.2f}; D {v["outer_diameter_mm"]:g} (fallback {v["fallback_outer_diameter_mm"]:g}); E {v["aperture_diameter_mm"]:g}. Stock {stocks}. Diagrams are not full-size templates.',y)-10
    y = r.row(y,[('P16_main_od','A: main outside diameter',{'check':'P16'}),('P16_main_width','B: opening width',{'check':'P16'}),('P16_main_height','C: opening height',{'check':'P16'})])
    y = r.row(y,[('P16_div_od','D: diverter outside diameter',{'check':'P16'}),('P16_div_id','E: diverter opening',{'check':'P16'}),('P16_thickness','T: main / diverter min-max',{'check':'P16'})])
    y = r.note('P17_condition','P17  Flatness method/readings; sharp edges, burrs, distortion or finish defects; photo references',y,34,'P17')
    y = r.row(y,[('P15_result','P15: identity/material result',{'check':'P15','options':STATUS}),('P16_result','P16: dimensions result',{'check':'P16','options':STATUS}),('P17_result','P17: condition result',{'check':'P17','options':STATUS})])
    y = r.note('P01_paper','P01  If paper used: X / Y readings for each 100 mm bar, on each of the TWO A3 sheets; print result or N/A',y,27,'P01')
    r.text('Compare readings to the actual confirmed order and shop targets. Record the method/instrument and deviations; do not substitute design numbers for observations. The paper test checks layout only.',y,size=8)
    r.finish_page()

    y = r.begin('2. Establish factory attachment',
                'The expert checks the original Kohler parts first, then repeats with the added stack on page 3. A factory-only mechanical fit does not prove a seal over the damaged opening.')
    y = r.row(y,[('record_page2','Record ID / date / observer'),('guide_identity','Applicable guide revision / actual part identity')])
    y = r.section('P09 / P10  Distinguish the attachment interfaces',y)
    y = r.text('U = upper volume stem; L = lower temperature stem; D = separate diverter stem. The main handle assemblies thread onto the inner plate hubs; the stem adapters must engage the valve. Seeing a stem through an opening is not proof of engagement.',y)-10
    for key,label in [('U','U - upper volume'),('L','L - lower temperature'),('D','D - diverter')]:
        y = r.row(y,[(f'P10_{key}_parts',label+': adapter / screw / hub',{'check':'P10'}),(f'P10_{key}_factory','Factory-only fit result',{'check':'P10','options':STATUS})])
    y = r.note('P10_factory_evidence','P10  Actual seating/engagement observations, method and photos; failed/hidden interfaces; required adapter correction',y,38,'P10')
    y = r.section('P09  Rod projection and the confirmed wood obstruction',y)
    y = r.text('NE = upper-right rod; SW = lower-left rod, viewed from the shower. Record from the ORIGINAL finished tile face. With a parallel straightedge whose outer face is H above tile, measure gap G back to the tip: projection = H - G. Keep H and G, sign and method; no U/L target is inferred.',y)-10
    y = r.row(y,[('P09_before','Before: NE / SW projection + H / G',{'check':'P09'}),('P09_after','After: NE / SW projection + H / G',{'check':'P09'})])
    y = r.note('P09_adjustment','P09  Rear contact, chosen remedy, retained thread engagement, nut/cover clearance, method and photo refs.',y,42,'P09')
    y = r.row(y,[('P09_result','P09: actual rod/nut fit',{'check':'P09','options':STATUS}),('expert_controls','Expert: isolation / operation / temperature checks')])
    y = r.text('Wood relief is the owner\'s conditional preference if the other depths work. The expert establishes access, clearance and dimensions; preserve tile. The legacy main guide specifies 7/16 inch (11.1125 mm) maximum rod projection from the wall; confirm its applicability before using it.',y,size=8)-7
    r.text('Source: Kohler 1041504-2-F, pages 7-8 (main); 1190382-2-A, page 1 (diverter). Use the applicable original guide for adapter choice, screw lengths and handle assembly. Do not remove pressure-containing parts without the expert\'s isolation plan.',y,size=8)
    r.finish_page()

    y = r.begin('3. Trial the complete added stack',
                'Use the real factory inner plates, foam, covers and handles with the measured custom parts. No force-fitting. PASS requires a stated observation; hidden or untested interfaces remain UNRESOLVED.')
    y = r.row(y,[('record_page3','Record ID / date / observer'),('trial_configuration','Actual parts / revision / stock / diverter size')])
    y = r.text('Shower-side order: sound support -> custom backing -> factory foam / inner plate -> decorative cover -> handle. Added height = actual backing thickness t + effective bedding/support height b. Uncompressed 6 mm foam is not an allowable spacer height.',y)-9
    y = r.row(y,[('stack_main','Main: t / b / total added height'),('stack_div','Diverter: t / b / total added height'),('pair_gap','Smallest actual gap between backings',{'check':'P12'})])
    y = r.row(y,[('P03_main_borders','Main exposed border: top / right / bottom / left',{'check':'P03'}),('P03_div_borders','Diverter border: top / right / bottom / left',{'check':'P03'})])
    checks = [
        ('P02_pose','P02','Both valve/hub openings register'),
        ('P03_retention','P03','Centered and retained without sliding'),
        ('P04_coverage','P04','Every gouge / CUT-03 is covered'),
        ('P05_support','P05','Firm support at seal / clamp zones'),
        ('P06_deflection','P06','No rocking / unacceptable deflection'),
        ('P07_contact','P07','ENTIRE foam/contact path, both valves'),
        ('P08_seating','P08','Both covers seat; no rod/nut conflict'),
        ('P10_complete','P10','U / L / D engage with added plate'),
        ('P11_drain','P11','Factory bottom drain/notch stays clear'),
        ('P12_travel','P12','Full handle travel and neighbor gap'),
        ('P13_P14_service','P13/P14','Tool / removal / cartridge access')]
    for name,check,label in checks:y = r.status_row(name,check,label,y)
    y = r.note('trial_conflicts','Conflicts / incomplete checks / photo index / exact revision changes needed (attach more pages if needed)',y,31)
    r.text('A dry fit is not a water test. Any support, retention, adapter, aperture or thickness change must be recorded and its affected checks repeated.',y,size=8)
    r.finish_page()

    y = r.begin('4. Record the repair and testing',
                'Complete only as work actually happens. The qualified installer selects the support/seal detail and applicable product instructions. Unperformed tests stay NOT RECORDED.')
    y = r.row(y,[('record_page4','Record ID / date / observer'),('repair_drawing','Final part / repair drawing revision(s)')])
    y = r.note('support_detail','P05/P06  Selected support / load path / local rebuilding; detail/sketch/photo refs.; how removal remains possible',y,44,'P05/P06')
    y = r.note('seal_detail','P07/P11  Actual seal-contact detail for BOTH valves, factory gasket condition, product/primer and preserved drain',y,44,'P07/P11')
    y = r.note('P18_product','P18  Product / TDS revision / lot; stone non-staining and substrate compatibility evidence; selected joint detail',y,37,'P18')
    y = r.row(y,[('P18_application','Applied date/time + temperature / humidity',{'check':'P18'}),('P18_exposure','Required cure / earliest water exposure + source',{'check':'P18'})])
    y = r.row(y,[('P18_result','P18: cure conditions met',{'check':'P18','options':STATUS}),('P19_status','P19: supply / valve leak test',{'check':'P19','options':STATUS}),('P20_status','P20: shower spray entry test',{'check':'P20','options':STATUS})])
    y = r.note('P19_observation','P19  Date / observer / isolation or operating state / method / duration / accessible observation points / result / photos',y,40,'P19')
    y = r.note('P20_observation','P20  After verified cure: date / observer / spray method / duration / access points / moisture observations / photos',y,40,'P20')
    y = r.note('expert_disposition','Expert assessment: remaining defects, stop conditions, remediation or further checks; accepted revision and rationale',y,40)
    y = r.row(y,[('expert_name','Expert name / date (assessment attribution)'),('owner_record','Owner received record / date / next action')])
    r.text('Supply leakage and shower-water ingress are separate tests. Stop on new moisture and investigate. A local successful test does not certify the concealed shower system. Return this record with its referenced photos; changes require reconciliation before a permanent-installation manual can be finalized.',y,size=8)
    r.finish_page()
    path = r.save()
    validate_form(path, r.directory/'field_record_schema.json')
    return path


def validate_form(path, schema_path, expected_values=None):
    """Check actual field tree, widgets, defaults/values, and appearance streams."""
    schema = json.loads(Path(schema_path).read_text())
    reader = PdfReader(path)
    fields = reader.get_fields() or {}
    expected = {n:f['default'] for n,f in schema['fields'].items()}
    expected.update(expected_values or {})
    assert len(reader.pages) == 4 and set(fields) == set(expected)
    canonical = {ref.idnum:ref.get_object() for ref in reader.trailer['/Root']['/AcroForm']['/Fields']}
    seen = set()
    for i,page in enumerate(reader.pages,1):
        for ref in page.get('/Annots',[]):
            widget = ref.get_object()
            if widget.get('/Subtype') != '/Widget':continue
            parent_ref = widget.get('/Parent')
            field = parent_ref.get_object() if parent_ref else widget
            name = field.get('/T')
            assert name in expected and name not in seen, f'Unexpected/duplicate widget: {name}'
            assert (parent_ref.idnum if parent_ref else ref.idnum) in canonical, f'Orphan/ambiguous field {name}'
            assert str(fields[name].get('/V','')) == str(expected[name])
            assert str(widget.get('/V',field.get('/V',''))) == str(expected[name])
            assert schema['fields'][name]['page'] == i
            assert len(widget['/AP']['/N'].get_object().get_data()) > 0
            x0,y0,x1,y1 = map(float,widget['/Rect'])
            assert LEFT-1 <= x0 < x1 <= RIGHT+1 and 44 < y0 < y1 < HEIGHT-90
            seen.add(name)
    assert seen == set(expected)
    return dict(pages=4, fields=len(fields), widgets=len(seen),
                field_tree_and_widget_values='PASS', appearance_streams='PASS',
                values='BLANK_DEFAULTS' if not expected_values else 'TEST_VALUES_ROUND_TRIPPED')
