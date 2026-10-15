"""Print artifacts from the same resolved parameters; all unapproved drawings marked draft."""
from pathlib import Path
import json,math,sys
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,letter,landscape
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from requests import requests
from build_review import manual_steps
fontroot=Path('/System/Library/Fonts/Supplemental')
pdfmetrics.registerFont(TTFont('Project',str(fontroot/'Arial.ttf')))
pdfmetrics.registerFont(TTFont('ProjectBold',str(fontroot/'Arial Bold.ttf')))
styles=getSampleStyleSheet()
for st in styles.byName.values():st.fontName='Project'
styles.add(ParagraphStyle(name='ProjectTitle',fontName='ProjectBold',fontSize=23,leading=27,textColor=colors.HexColor('#153d49'),spaceAfter=12))
styles.add(ParagraphStyle(name='SmallCell',fontName='Project',fontSize=8,leading=11))
styles['BodyText'].fontSize=10;styles['BodyText'].leading=14;styles['BodyText'].spaceAfter=8
styles['Heading2'].fontName='ProjectBold';styles['Heading2'].textColor=colors.HexColor('#176e80')

def footer(c,doc):
    c.setFont('Project',8);c.setFillColor(colors.HexColor('#50636d'));c.drawString(40,24,'Shower / Kohler | Provisional review | Not for fabrication or permanent installation');c.drawRightString(doc.pagesize[0]-40,24,str(doc.page))

def build():
    d=json.loads((ROOT/'data/derived/resolved.json').read_text());rev=d['revision'];groups=requests(d);out=ROOT/'deliverables/current/drawings';out.mkdir(parents=True,exist_ok=True)
    views=ROOT/'deliverables/current/review/views'
    accepted={m['id']:m for m in json.loads((ROOT/'canon/measurements.json').read_text())['measurements'] if m['status']=='user-confirmed'}
    pending={k:v for o in d['observations'] for k,v in o.get('pending_contact_readings',{}).items() if k not in accepted}
    story=[]
    for n,g in enumerate(groups):
        if n:story.append(PageBreak())
        phase='First checks' if g['first'] else 'Actual plate follow-up' if g['id'] in ('11','12') else 'Control-depth follow-up' if g['id']=='10' else 'Installer checks after first readings'
        story+=[Paragraph(f"{g['id']} / {g['title']}",styles['ProjectTitle']),Paragraph(f"Measurement worksheet | {rev} | {phase}",styles['BodyText']),Paragraph(g['purpose'],styles['BodyText'])]
        picture_size=145 if g['id']=='03' else 205
        picture=Image(str(views/(g['view']+'.png')),width=picture_size,height=picture_size)
        if g['id']=='11':
            picture=Image(str(views/'inner_photo.png'),width=177,height=219)
        if g['id']=='12':
            picture=Image(str(views/'outer_photo.png'),width=205,height=210)
        pair=Table([[picture,Paragraph(g['instructions'],styles['SmallCell'] if g['id'] in ('11','12') else styles['BodyText'])]],colWidths=[220,290]);pair.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),10)]));story+=[pair,Spacer(1,12)]
        rows=[[Paragraph(s,styles['SmallCell']) for s in ['ID / contact','Estimate mm','Raw reading','Unit','Repeat readings']]]
        recorded=[]
        for f in g['fields']:
            if f['id'] in pending:
                recorded.append(f"{f['label']}: reported {pending[f['id']]:g} mm; contact clarification pending")
                continue
            if g['id'] in ('04','05','06','11','12') and f['id'] in accepted:
                m=accepted[f['id']]
                recorded.append(f"{f['label']}: {'approximately ' if m.get('approximate') else ''}{m['value_mm']:g} mm")
                continue
            pred='unknown' if f['prediction_mm'] is None else f"{f['prediction_mm']:.1f}"
            if f['id'] in accepted:pred=f"Recorded {accepted[f['id']]['value_mm']:g}"
            rows.append([Paragraph(f"<b>{f['id']}</b><br/>{f['label']}<br/>{f['contacts']}",styles['SmallCell']),Paragraph(f"{pred}<br/>Useful +/-{f['useful_accuracy_mm']}",styles['SmallCell']),'____________','______','_______________'])
        if recorded and g['id'] in ('04','05'):
            story.append(Paragraph('Already recorded: '+'; '.join(recorded)+'. Free state; installed compression remains unknown.',styles['SmallCell']))
        if recorded and g['id']=='06':
            story.append(Paragraph('Already reported: '+'; '.join(recorded)+'.',styles['SmallCell']))
        if len(rows)>1:
            t=Table(rows,colWidths=[222,66,80,44,98],repeatRows=1);t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Project'),('FONTSIZE',(0,0),(-1,-1),8),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6eff0')),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#bacbd0')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),4 if g['id']=='03' else 7),('BOTTOMPADDING',(0,0),(-1,-1),4 if g['id']=='03' else 7)]));story.append(t)
        story+=[Spacer(1,8),Paragraph('Date: __________________  Tool / method: ___________________________________',styles['BodyText']),Paragraph('Photo / trace reference: ___________________________________________________',styles['BodyText']),Paragraph('Notes, repeatability, condition and uncertainty: ______________________________',styles['BodyText']),Paragraph('_________________________________________________________________________',styles['BodyText']),Paragraph('Amber model geometry is assumed. Do not use estimates as your readings. Return raw values and units; do not round to match the model.',styles['SmallCell'])]
    SimpleDocTemplate(str(out/f'measurement_worksheet_{rev}.pdf'),pagesize=A4,rightMargin=40,leftMargin=40,topMargin=36,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
    # Dimensioned drawing: true model values, but no released process/tolerances.
    p=out/f'candidate_drawing_{rev}_DRAFT.pdf';c=canvas.Canvas(str(p),pagesize=landscape(A4));W,H=landscape(A4)
    c.setFont('ProjectBold',20);c.setFillColor(colors.HexColor('#153d49'));c.drawString(35,H-38,'CUSTOM-01 / DRAFT - NOT FOR FABRICATION')
    c.setFont('Project',10);c.drawString(35,H-59,f'{rev} | millimeters | front shown | conceptual drawing scale 1:2 | actual fit unresolved')
    candidate=d['candidate'];dia=candidate['diameter_mm'];s=.5*mm;ox=230;oy=H/2-5;cx,cy=d['trim_center_mm'];apx=candidate['aperture_center_mm'][0]-cx;apy=candidate['aperture_center_mm'][1]-cy
    c.setLineWidth(1);c.setStrokeColor(colors.HexColor('#176e80'));c.circle(ox,oy,dia/2*s)
    c.roundRect(ox+(apx-candidate['aperture_width_mm']/2)*s,oy+(apy-candidate['aperture_height_mm']/2)*s,candidate['aperture_width_mm']*s,candidate['aperture_height_mm']*s,candidate['aperture_radius_mm']*s,stroke=1,fill=0)
    c.setDash(3,3);c.setStrokeColor(colors.HexColor('#70838b'));c.line(ox-dia/2*s-15,oy,ox+dia/2*s+15,oy);c.line(ox,oy-dia/2*s-15,ox,oy+dia/2*s+15);c.setDash()
    c.setFillColor(colors.black);c.setFont('Project',10);c.drawCentredString(ox,oy+dia/2*s+20,f'Outer diameter {dia:.1f}');c.drawCentredString(ox,oy-dia/2*s-30,'C = center of outer profile; +X right / +Y up')
    c.drawString(ox+12,oy+12,'C');c.drawCentredString(ox+apx*s,oy+apy*s,f'AP-01 {candidate["aperture_width_mm"]:.1f} x {candidate["aperture_height_mm"]:.1f}')
    lines=[f'Profile: circle, diameter {dia:.1f}',f'Thickness: {candidate["thickness_mm"]:.3f} (UNVALIDATED)',f'AP-01: one through clearance aperture',f'Width x height: {candidate["aperture_width_mm"]:.1f} x {candidate["aperture_height_mm"]:.1f}',f'Four corner radii: {candidate["aperture_radius_mm"]:.1f}',f'AP-01 center from C: X {apx:+.3f}; Y {apy:+.3f}','Separate fastener holes: NONE','Stud paths currently lie inside AP-01','Material / finish: NOT SELECTED','Thickness tolerance: NOT RELEASED','Hole / profile tolerances: NOT RELEASED','Flatness: NOT RELEASED','Edge treatment / burr limit: NOT RELEASED','Retention / load path: UNRESOLVED','Gasket-to-aperture conflict: UNRESOLVED','Nominal drawn values are not proven accuracy.']
    x=440;y=H-100
    for line in lines:c.drawString(x,y,line);y-=22
    c.setFont('Project',9);c.drawString(35,55,'Use the separate clean DXF for a future approved cut path. This drawing does not approve fabrication.');c.drawString(35,40,'Retain original Kohler parts. No additional tile cutting, grinding or drilling. Verify template, thickness mockup and physical access.');c.showPage();c.save()
    # Tiled 1:1 template: four letter pages, 30 mm center overlap, vector paths.
    c=canvas.Canvas(str(out/f'profile_template_{rev}_DRAFT.pdf'),pagesize=letter);W,H=letter
    for row,(y0,y1) in enumerate([( -15,125),(-125,15)]):
      for col,(x0,x1) in enumerate([(-125,15),(-15,125)]):
        c.setFillColor(colors.HexColor('#153d49'));c.setFont('ProjectBold',16);c.drawString(35,H-35,f'PROFILE TRIAL / {rev} / tile {row+1}-{col+1}')
        c.setFont('Project',10);c.drawString(35,H-55,'DRAFT - NOT FOR FABRICATION. Print at 100% / actual size.');c.drawString(35,H-72,'Measure BOTH 100 mm bars before taping. Disable fit-to-page.');c.drawString(35,H-89,'Match the C cross and overlap grid; do not cut the stone. UP is +Y.')
        sx=40;sy=230;side=140*mm
        c.saveState();clip=c.beginPath();clip.rect(sx,sy,side,side);c.clipPath(clip,stroke=0,fill=0)
        c.translate(sx-x0*mm,sy-y0*mm);c.scale(mm,mm)
        c.setStrokeColor(colors.HexColor('#d7e2e5'));c.setLineWidth(.15)
        for t in range(-120,121,10):c.line(t,-125,t,125);c.line(-125,t,125,t)
        c.setStrokeColor(colors.black);c.setLineWidth(.4);c.circle(0,0,dia/2)
        c.roundRect(apx-candidate['aperture_width_mm']/2,apy-candidate['aperture_height_mm']/2,candidate['aperture_width_mm'],candidate['aperture_height_mm'],candidate['aperture_radius_mm'])
        c.setDash(2,2);c.line(-125,0,125,0);c.line(0,-125,0,125);c.setDash()
        for gx,gy in [(-10,-10),(-10,10),(10,-10),(10,10)]:c.line(gx-2,gy,gx+2,gy);c.line(gx,gy-2,gx,gy+2)
        c.setFont('Project',3.8);c.drawString(2,2,'C');c.drawString(apx-12,apy,'AP-01 / DRAFT');c.restoreState()
        c.setStrokeColor(colors.black);c.setLineWidth(.5);c.rect(sx,sy,side,side)
        c.setFont('Project',9);c.drawString(sx,sy-17,f'Local C coordinates: X {x0} to {x1} mm; Y {y0} to {y1} mm')
        # Separate two-axis calibration, each exactly 100 mm in PDF coordinates.
        bx=55;by=120;c.line(bx,by,bx+100*mm,by)
        for x in [bx,bx+100*mm]:c.line(x,by-5,x,by+5)
        c.drawString(bx,by+12,'100 mm X calibration (measure between end ticks)')
        vx=525;vy=255;c.line(vx,vy,vx,vy+100*mm)
        for y in [vy,vy+100*mm]:c.line(vx-5,y,vx+5,y)
        c.saveState();c.translate(vx+16,vy+5);c.rotate(90);c.drawString(0,0,'100 mm Y calibration');c.restoreState()
        c.drawString(35,78,'Paper/card checks planar registration and coverage only. It cannot validate the depth stack.');c.drawString(35,62,f'Trial plate thickness shown in CAD: {candidate["thickness_mm"]} mm. Use measured spacers / a thickness mockup later.');c.drawString(35,46,'Prototype materials are not approved for permanent wet-area use. Keep original hardware and drainage.');c.showPage()
    c.save()
    story=[]
    for i,s0 in enumerate(manual_steps(),1):
        if i>1:story.append(PageBreak())
        story+=[Paragraph(f'{i:02d} / {s0["title"]}',styles['ProjectTitle']),Paragraph(f'{rev} - DRAFT SEQUENCE - NOT INSTALLATION APPROVAL',styles['BodyText'])]
        right=Paragraph('<b>Responsible:</b> '+s0['person']+'<br/><br/><b>Prerequisite:</b> '+s0['prerequisite']+'<br/><br/><b>Tools / materials:</b> '+s0['tools'],styles['BodyText'])
        t=Table([[Image(str(views/(s0['view']+'.png')),width=260,height=260),right]],colWidths=[278,232]);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0)]));story+=[t,Spacer(1,22),Paragraph('Action',styles['Heading2']),Paragraph(s0['action'],styles['BodyText']),Paragraph('Completion check',styles['Heading2']),Paragraph(s0['check'],styles['BodyText']),Paragraph('Stop condition',styles['Heading2']),Paragraph(s0['stop'],styles['BodyText'])]
    depth=json.loads((ROOT/'deliverables/current/analysis/depth_stack.json').read_text())
    story += [PageBreak(),Paragraph('Depth and sealing / review correction',styles['ProjectTitle']),
        Paragraph('The earlier seated-cover image is not a feasible assembly. The unchanged stud envelopes intersect the assumed cover. No captured hardware has been shortened or moved.',styles['BodyText']),
        Image(str(views/'section_studs.png'),width=230,height=230),
        Paragraph('All Z values use the original intact-stone plane as zero, with positive Z toward the shower. Numbers below are conditional model values, not physical measurements.',styles['BodyText'])]
    rows=[[Paragraph(x,styles['SmallCell']) for x in ['Trial / stud','Tip Z, mm','Cover inside Z, mm','Signed gap, mm']]]
    for case in depth['cases'].values():
        for stud in case['studs']:
            rows.append([Paragraph(case['label']+' / '+stud['id'],styles['SmallCell']),f"{stud['tip_z_mm']:.1f}",f"{stud['cover_rear_z_mm']:.1f}",f"{stud['tip_to_cover_rear_clearance_mm']:.1f}"])
    table=Table(rows,colWidths=[210,95,110,95]);table.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Project'),('FONTSIZE',(0,0),(-1,-1),9),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6eff0')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story += [table,Spacer(1,10),
        Paragraph('Negative gap means interference. The assumed nut envelopes clear the cover, but real nut seats, formed metal, rear cavity and compressed foam remain unmeasured. A thicker backing plate also changes hub/adapter engagement and the cover landing.',styles['BodyText']),
        Paragraph('Kohler 1041504-2-F, page 7: the inner plate lies flat at the wall; the studs project at most 7/16 inch from the finished wall; the foam covers the opening; nuts stay behind the outer cover; its drain faces down. Page 8 requires appropriate adapters for engagement and seating. Current guide 1216755-2-A, steps 8-12, shows the same assembly order. Check the actual revision.',styles['BodyText']),
        Paragraph('Four separate questions remain: conceal all cuts; provide continuous supported foam landing; resolve surface-water seals and drainage; inspect concealed waterproofing through existing access. The current trial aperture conflicts with the assumed gasket path. Coverage alone is not a waterproof repair.',styles['BodyText'])]
    free=depth.get('inner_plate_depth',{})
    if free.get('overall_free_depth_mm') is not None:
        story.append(Paragraph(f"Measured loose-part envelope: {free['overall_free_depth_mm']:g} mm from uncompressed foam back to frontmost metal, with approximately {free['free_foam_thickness_mm']:g} mm free foam thickness and {free['representative_band_width_mm']:g} mm representative band width. This free-state plate intersects the assumed cover; actual compression and local cavity geometry must be checked before judging installed fit.",styles['BodyText']))
    r=depth['rough_in'];lo,hi=r['nominal_bare_upper_tip_from_tile_mm']
    story += [PageBreak(),Paragraph('Control depth / diagnostic follow-up',styles['ProjectTitle']),
        Paragraph('The user confirms excessive stud projection and reports rear bolt contact with wood. Trim studs thread into the valve; they do not need wood anchorage. Identify the same rear fasteners, framing/blocking and usable travel before selecting a remedy.',styles['BodyText']),
        Image(str(views/'control_depth_measure.png'),width=245,height=245),
        Paragraph(f"K-2973-KS specification p3: the labeled upper bare-tip and finished-wall dimensions imply a nominal upper-tip interval {lo:.1f} to {hi:.1f} mm from tile. Current comparison: {r['comparison_tip_mm']:.1f} mm ({r['comparison_basis']}). This is {r['conditional_result']}. It is not a valve-relocation target.",styles['BodyText']),
        Paragraph('Check 10 identifies the as-found tips/adapters and records block height H and both underside-to-tip gaps. H - G gives signed projection. The installer separately checks the plaster guard or documented axis datum. The 7/16-inch trim-stud limit does not apply to control stems.',styles['BodyText']),
        Paragraph('Correct adapter and screw lengths must permit handle engagement and full cover/bonnet seating. An added backing plate changes that relationship again. Internal valve seals contain supply water; improper trim seating concerns external shower-water entry. Test these separately after the complete assembly is resolved.',styles['BodyText']),
        Paragraph('Sources: K-2973-KS specification p3; Kohler 1205551-2-D pp10-13 and25; 1041504-2-F pp3,7-8. No stud cutting, wood drilling, control-stem modification or valve relocation is selected.',styles['SmallCell'])]
    manual=ROOT/f'deliverables/current/manual/repair_manual_{rev}_DRAFT.pdf';SimpleDocTemplate(str(manual),pagesize=A4,leftMargin=40,rightMargin=40,topMargin=36,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
    print('Generated worksheet, drawing, calibrated tiled profile and six-step draft manual PDFs')

if __name__=='__main__':build()
