"""Readable axial envelope diagram generated from the CAD depth report."""
from html import escape

def depth_svg(report, case):
    d=report['cases'][case];out=[]
    def put(s):out.append(s)
    def text(x,y,s,size=19,color='#213c47',weight='normal'):
        put(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(str(s))}</text>')
    def line(x1,y1,x2,y2,color='#d3dfe3',dash=''):
        put(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="1.5" fill="none" stroke-dasharray="{dash}"/>')
    def rect(x,y,w,h,color):put(f'<rect x="{x}" y="{y}" width="{max(.5,w)}" height="{h}" rx="2" fill="{color}"/>')
    put('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 840" role="img" aria-label="Depth intervals at the two stud regions; unchanged tips intersect the assumed cover"><rect width="1100" height="840" fill="#fff"/><g font-family="Arial, sans-serif">')
    text(35,40,d['label']+' — fit conflict',28,'#a62f25','bold')
    text(35,71,'Z = 0 at original intact stone; positive Z points into the shower.',18)
    text(35,98,'Axial envelopes, not a literal material slice. All shown part depths are provisional.',18)
    x=lambda z:300+z*18
    for z in [0,5,10,15,20,25,30,35]:
        line(x(z),145,x(z),665);text(x(z)-9,134,str(z),16)
    text(970,134,'mm',16)
    for i,s in enumerate(d['studs']):
        top=180+i*250
        text(35,top,s['id'],22,'#213c47','bold')
        items=[('Unchanged stud tip',[0,s['tip_z_mm']],'#bc3f31'),
               ('Assumed nut',s['nut_z_mm'],'#78858c'),
               ('Cover at stud axis',s['cover_material_on_axis_z_mm'][0],'#3d657c')]
        for j,(label,span,color) in enumerate(items):
            y=top+25+j*48;text(35,y+19,label,18);rect(x(span[0]),y,x(span[1])-x(span[0]),25,color)
            value=f'inside {span[0]:.1f} / front {span[1]:.1f}' if label=='Cover at stud axis' else f'{span[1]:.1f}'
            text(x(span[1])+12,y+19,value,17,color)
        rear=s['cover_rear_z_mm'];tip=s['tip_z_mm'];y=top+187
        line(x(rear),y,x(tip),y,'#b23028');line(x(rear),y-5,x(rear),y+5,'#b23028');line(x(tip),y-5,x(tip),y+5,'#b23028')
        text(35,y+6,f'Past cover inside: {tip-rear:.1f} mm',17,'#a62f25','bold')
    rim=d['cover_rim_z_mm'];line(x(rim),145,x(rim),665,'#168ca0','5 4')
    text(35,704,f'Cover rim / assumed landing plane: Z {rim:.3f} mm.',19,'#116b7b')
    text(35,735,'No bolt holes in the outer cover. The nuts and stud tips must fit behind its inside surface.',18)
    text(35,765,'Original guide: stud tips at most 7/16 in (11.1 mm) from the finished wall; actual adjustment unverified.',17)
    text(35,797,'A backing plate changes the stack. Its thickness alone does not prove sealing, support or engagement.',17)
    put('</g></svg>');return ''.join(out)

def depth_html(report):
    rows=[]
    labels={'CUSTOM-01':'Trial backing plate','GASKET-01':'Foam (free, not compressed)','PLATE-INNER':'Yellow inner plate, incl. hubs','TRIM-OUTER':'Decorative cover','HANDLE-LOWER':'Lower handle envelope','HANDLE-UPPER':'Upper handle envelope','VALVE-LOWER':'Lower valve envelope','VALVE-UPPER':'Upper valve envelope'}
    basis={'CUSTOM-01':'Trial thickness; no selected material or retention','GASKET-01':'Assumed footprint and free thickness; contact unknown','PLATE-INNER':'Assumed sheet / formed / hub depths','TRIM-OUTER':'Nominal exterior; rear cavity and seating unmeasured','HANDLE-LOWER':'Nominal projection; rear mating and engagement assumed','HANDLE-UPPER':'Nominal projection; rear mating and engagement assumed','VALVE-LOWER':'Scan tip; body profile and hidden extent assumed','VALVE-UPPER':'Scan tip; body profile and hidden extent assumed'}
    fmt=lambda span:'—' if span is None else f'{span[0]:.1f} to {span[1]:.1f}'
    for id,label in labels.items():
        rows.append(f'<tr><td>{label}</td><td>{fmt(report["cases"]["factory"]["ranges_z_mm"].get(id))}</td><td>{fmt(report["cases"]["proposed"]["ranges_z_mm"].get(id))}</td><td>{basis[id]}</td></tr>')
    markup='''<section id="depth"><h2>Depth, seating and water entry</h2>
<div class="notice fail"><strong>The earlier “proposed assembly” is rejected as an assemblable state.</strong> The seated cover intersects the unchanged stud envelopes. These views now show that conflict explicitly. The captured hardware has not been shortened or moved.</div>
<p>The yellow part is the factory inner plate. Its nuts belong behind the decorative cover. Only the control openings belong in the front face; adding bolt holes is not the fix. Kohler's guide places the inner plate at the wall, secures it with nuts, then fits the outer cover and secures it through the handle assemblies. The drain faces down.</p>
<div class="controls"><button data-depth-case="proposed" aria-pressed="true">With trial backing plate</button><button data-depth-case="factory" aria-pressed="false">Original wall only</button><a href="#model" id="show-depth-3d">Open stud section in 3D</a></div>
<figure class="depth-figure"><a id="depth-image-link" href="views/depth_proposed.svg"><img id="depth-image" src="views/depth_proposed.svg" alt="Signed depth relationships at both studs, with an assumed seated cover"></a><figcaption>Negative clearance means overlap. Numbers describe the present draft, not measured physical clearances. The nut envelopes clear the cover in this simplified model; their actual size and seating remain unknown.</figcaption></figure>
<div class="table-wrap"><table id="depth-values"><caption>Conditional model values in mm; original stone is Z = 0</caption><thead><tr><th>Stud</th><th>Tip Z</th><th>Cover inside Z</th><th>Signed gap</th></tr></thead><tbody>DEPTH_ROWS</tbody></table></div>
<p><strong>Why the added plate matters:</strong> the present trial shifts the assumed landing plane outward by 4.175 mm (3.175 mm plate + 1 mm illustrative seal layer). The valve and stud tips stay where the scan placed them. The gasket's shown 3 mm is uncompressed; it is not a known installed spacing. Correct seating also depends on formed metal, hubs, nut seats, adapters and handle engagement.</p>
<details><summary>Every part uses the same Z datum</summary><p>Ranges include the whole modeled part. Overlapping ranges alone do not prove collision: parts may occupy different X/Y regions. The cover conflicts are exact solid intersections of the disclosed assumptions. The plate aperture leaves space at the stud axes; the added plate is not solid there.</p><p>The lower valve placeholder also intersects the cover. Its collar profile and the cover openings are assumed, so this flags incomplete reconstruction, not a newly established physical defect. The yellow plate and nut placeholders have no cover intersection; that does not verify their real seating.</p><div class="table-wrap"><table><thead><tr><th>Part</th><th>Original-wall trial Z, mm</th><th>With backing plate Z, mm</th><th>Evidence / uncertainty</th></tr></thead><tbody>'''+''.join(rows)+'''</tbody></table></div></details>
<div class="grid sealing-grid">
<article class="card"><h3>1. Hide the cuts</h3><p>An outer profile can conceal the saw marks. Coverage alone says nothing about the gasket behind it.</p></article>
<article class="card"><h3>2. Support the inner plate</h3><p>The foam needs a continuous landing and the inner plate must sit flat. The current large trial aperture removes some of the assumed foam landing, so that candidate remains unsuitable as drawn.</p></article>
<article class="card"><h3>3. Control surface water</h3><p>The original foam and downward drain retain their roles. A backing plate adds another wall-to-plate interface whose support, seal and drainage detail must be established. A colored seal band is not evidence of a watertight joint.</p></article>
<article class="card"><h3>4. Check concealed waterproofing</h3><p>The scan cannot show continuity of the hidden water barrier or identify the cause of a prior leak. Inspect through existing access before deciding whether a surface repair is sufficient. Supply/valve leakage and water entering around trim are separate checks.</p></article>
</div>
<p><strong>Before measuring:</strong> prioritize Checks 04–07: rear metal datum and formed depth, actual foam path, cavity beside each stud, and both stud projections from intact tile. Record each cavity depth separately in Check 06 notes. Check 09 covers nut seating, compressed foam and adapter/thread engagement with the installer. Keep the original parts and trim intact.</p>
<p class="subtle">Sources: <a href="https://resources.kohler.com/onlinecatalog/pdf/1041504_2.pdf">Kohler 1041504-2-F, pages 7–8</a>; <a href="https://techcomm.kohler.com/techcomm/pdf/1216755-2.pdf">Kohler 1216755-2-A, steps 8–12</a>. The older guide explicitly gives 7/16 inch maximum from the finished wall. Neither source approves this custom backing-plate detail. <a href="../analysis/depth_stack.json">Depth values and collision results</a>.</p></section>'''

    trial=report['cases']['proposed'];original=report['cases']['factory']
    shift=trial['cover_rim_z_mm']-original['cover_rim_z_mm']
    plate=trial['ranges_z_mm']['CUSTOM-01'];seal=trial['ranges_z_mm']['NEW-SEAL-PATH'];foam=trial['ranges_z_mm']['GASKET-01']
    numeric=''.join(f'<tr><td>{s["id"]}</td><td>{s["tip_z_mm"]:.1f}</td><td>{s["cover_rear_z_mm"]:.1f}</td><td>{s["tip_to_cover_rear_clearance_mm"]:+.1f}</td></tr>' for s in trial['studs'])
    return markup.replace('DEPTH_ROWS',numeric).replace('4.175 mm (3.175 mm plate + 1 mm illustrative seal layer)',f'{shift:.3f} mm ({plate[1]-plate[0]:.3f} mm plate + {seal[1]-seal[0]:g} mm illustrative seal layer)').replace("shown 3 mm",f"shown {foam[1]-foam[0]:g} mm")
