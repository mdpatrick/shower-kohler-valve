"""Explain the removed gasket and manufacturer stud length without changing CAD."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def generate(out):
    record_path = ROOT / 'docs/physical_checks/foam_and_stud_research_2026-10-15.json'
    record = json.loads(record_path.read_text())
    resolved_path = ROOT / 'data/derived/resolved.json'
    resolved = json.loads(resolved_path.read_text())
    length = record['manufacturer_stud']['length_mm']
    limit = record['manufacturer_installation']['wall_projection_limit_mm']
    rows = []
    for name, xyz in zip(record['conditional_scan_estimate']['stud_order'], resolved['studs_mm']):
        rows.append(dict(stud=name, front_tip_z_mm=xyz[2],
                         inferred_rear_depth_behind_tile_mm=length-xyz[2],
                         inward_travel_to_original_wall_limit_mm=xyz[2]-limit))
    analysis = dict(record_id=record['id'], status=record['status'],
                    assumptions=record['conditional_scan_estimate']['assumptions'],
                    nominal_stud_length_mm=length, original_wall_limit_mm=limit,
                    inferred_rear_depth_at_original_limit_mm=length-limit,
                    rows=rows, not_a_drilling_specification=True,
                    input_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in [record_path, resolved_path]})
    (out / 'stud_rear_estimate.json').write_text(json.dumps(analysis, indent=2)+'\n')
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="430" viewBox="0 0 1100 430" role="img" aria-labelledby="title desc">
<title id="title">The foam belongs to the removable inner plate</title>
<desc id="desc">Schematic rear view of an inner plate with a dark perimeter foam band, and a free foam cross-section approximately six millimeters by six millimeters. The rear footprint is not verified.</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#24515c"/></marker></defs>
<rect width="1100" height="430" rx="14" fill="#f3f7f7"/>
<g font-family="Arial, sans-serif" fill="#18343c">
<text x="28" y="37" font-size="23" font-weight="bold">The foam is attached to the removable inner plate</text>
<text x="28" y="64" font-size="16">Illustration of its function • exact rear outline and sealing path remain unmeasured</text>
<text x="28" y="104" font-size="18" font-weight="bold">Wall-facing side, schematic</text>
<rect x="65" y="128" width="175" height="240" rx="60" fill="#d5dcde" stroke="#89979c" stroke-width="3"/>
<rect x="77" y="140" width="151" height="216" rx="50" fill="none" stroke="#34383e" stroke-width="14"/>
<circle cx="153" cy="203" r="32" fill="#f3f7f7" stroke="#89979c" stroke-width="3"/>
<circle cx="153" cy="294" r="36" fill="#f3f7f7" stroke="#89979c" stroke-width="3"/>
<path d="M226 179L300 150" fill="none" stroke="#24515c" stroke-width="2"/>
<text x="306" y="149" font-size="18" font-weight="bold">Soft perimeter band</text>
<text x="306" y="174" font-size="17">About 6 mm wide</text>
<text x="306" y="199" font-size="17">About 6 mm deep, free</text>
<text x="306" y="237" font-size="16">You measured these values</text>
<text x="306" y="260" font-size="16">on the loose plate.</text>
<text x="306" y="299" font-size="17" font-weight="bold">It leaves with the plate.</text>
<text x="306" y="323" font-size="16">None is shown in your current</text>
<text x="306" y="346" font-size="16">exposed-valve installation.</text>
<path d="M582 100V367" stroke="#c5d1d4"/>
<text x="615" y="104" font-size="18" font-weight="bold">Small section through that band</text>
<rect x="718" y="164" width="83" height="83" fill="#34383e"/>
<rect x="801" y="148" width="10" height="115" fill="#a8b3b8"/>
<path d="M718 278H801" stroke="#24515c" stroke-width="1.6" marker-start="url(#arrow)" marker-end="url(#arrow)"/>
<path d="M845 164V247" stroke="#24515c" stroke-width="1.6" marker-start="url(#arrow)" marker-end="url(#arrow)"/>
<text x="738" y="302" font-size="16">~6 mm</text><text x="860" y="212" font-size="16">~6 mm</text>
<text x="616" y="202" font-size="16">To wall</text><path d="M700 207H674" stroke="#24515c" stroke-width="2" marker-end="url(#arrow)"/>
<path d="M810 151L901 136" stroke="#24515c" stroke-width="1.5"/>
<text x="902" y="135" font-size="16">Metal plate</text>
<text x="615" y="343" font-size="16">Compression in the installed assembly is unknown.</text>
<text x="28" y="405" font-size="16">Layer order: tile / proposed backing → factory foam → inner plate → decorative cover and handles</text>
</g></svg>'''
    (out / 'foam_gasket_schematic.svg').write_text(svg)
    table_rows = ''.join(f'<tr><th scope="row">{r["stud"]}</th><td>{r["front_tip_z_mm"]:.1f}</td>'
                         f'<td>{r["inferred_rear_depth_behind_tile_mm"]:.1f}</td>'
                         f'<td>{r["inward_travel_to_original_wall_limit_mm"]:.1f}</td></tr>' for r in rows)
    return '''<section id="foam-and-studs"><h2>What the foam looks like, and how long the rods are</h2>
<p>The foam is a compressible strip around the wall-facing side of the removable inner plate.
Your approximate 6 × 6 mm measurements describe that strip. The 15.44 mm measurement includes the free foam and formed metal envelope.</p>
<figure><img src="foam_gasket_schematic.svg" alt="Schematic explaining the inner plate perimeter foam and its roughly six by six millimeter free section">
<figcaption>Schematic only. The exact rear gasket footprint has not been photographed or traced. The stock part is
<a href="https://www.kohler.com/en/support/find-a-service-part/shop-parts/assembly-seal-front-plate-1035854">Kohler seal/front-plate assembly K-1035854</a>.
<a href="https://resources.kohler.com/onlinecatalog/pdf/1041507_5.pdf#page=9">Kohler's two-control exploded diagram, page 9</a> identifies it and the studs.</figcaption></figure>
<h3>Factory stud: 4.56 inches long = approximately 115.8 mm</h3>
<p>Kohler identifies <a href="https://www.kohler.com/en/support/find-a-service-part/shop-parts/stud-10-24-x-4-56-l-1038645">K-1038645 as a 10-24 × 4.56 L stud</a>.
This is its full nominal length. The <a href="https://resources.kohler.com/onlinecatalog/pdf/1041504_2.pdf#page=7">installation guide, page 7</a>
limits its installed projection from the original finished wall to <b>7/16 inch = 11.1 mm</b>. The studs thread into the valve; wood is not their specified anchor.</p>
<h3>Conditional estimate from the existing scan</h3><p>All values below are millimeters. SW and NE are the lower-left and upper-right studs as viewed from the shower.</p>
<div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%;text-align:left"><thead><tr>
<th>Stud</th><th>Front tip beyond tile</th><th>Inferred rear tip behind tile</th><th>Inward travel to original 11.1 mm limit</th>
</tr></thead><tbody>'''+table_rows+'''</tbody></table></div>
<p>These figures assume uncut factory-length rods perpendicular to the tile, and the existing provisional scan scale/datum.
At the original-wall limit, a full-length rod would extend about <b>104.7 mm behind the tile</b>.
The wood plane is unmeasured; the calculation cannot determine penetration. <b>These are not pocket-drilling dimensions.</b>
The added plate/bedding and actual gasket, nut, cover and handle fit still require a complete depth check.</p>
<h3>Surface contact is the leading interpretation of the close-up</h3>
<p>The visible rod appears to terminate at the wood surface. A shallow indentation or obscured hole cannot be excluded,
and the second stud's rear contact is not visible. The stock studs are machine-threaded trim hardware, not specified wood anchors.</p>
<p>To settle it without guessing, trace each front stud to its rear end and inspect the contact with a mirror or borescope at a grazing angle.
Look for the end face sitting on wood versus the shaft disappearing into a hole. A paper feeler passing underneath proves a gap;
failure to pass does not distinguish contact from penetration.</p>
<p>A dimensional cross-check is also possible once the actual rod length <b>L</b> is known: measure <b>D</b>, from its front tip to the near wood face <em>along that same rod</em>.
If D is approximately L, it touches; if D is less than L, the implied penetration is L − D; if D is greater, the gap is D − L.
The difference must exceed measurement uncertainty, and a cut or substituted rod invalidates using 115.8 mm for L.</p>
<p class="small"><a href="stud_rear_estimate.json">Calculation and input hashes</a> · manufacturer nominal data and conditional estimates only · no geometry or physical readiness changed.</p></section>'''
