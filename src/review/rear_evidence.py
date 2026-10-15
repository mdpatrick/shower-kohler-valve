"""Local review of supplied rear photos; original image bytes are preserved."""
from pathlib import Path
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'deliverables/current/review/rear'
record = json.loads((ROOT / 'docs/physical_checks/rear_installation_2026-10-15.json').read_text())
OUT.mkdir(parents=True, exist_ok=True)
cards = []
for p in record['photos']:
    source = ROOT / p['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == p['sha256']
    dest = OUT / source.name
    if not dest.exists() or hashlib.sha256(dest.read_bytes()).hexdigest() != p['sha256']:
        shutil.copy2(source, dest)
    caption = ('The threaded rod appears to end at the wood surface. This supports the reported rear obstruction; '
               'the photograph does not trace both front trim studs or establish adjustment travel.' if p['view']=='close' else
               'The wider view records the wood member, copper piping and nearby cable. Wood dimensions, function '
               'and clear drilling access are not established.')
    cards.append(f'<figure><a href="{dest.name}"><img src="{dest.name}" alt="Original rear installation photograph: {p["view"]}"></a>'
                 f'<figcaption>{caption}</figcaption></figure>')
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Current rear installation — REAR01</title><style>
*{box-sizing:border-box}body{margin:0;background:#edf2f3;color:#18343c;font:17px/1.55 system-ui,sans-serif}
main{max-width:1200px;margin:auto;padding:28px}h1{font-size:34px;line-height:1.2}h2{font-size:23px;margin-top:0}
a{color:#076b80}section{background:white;padding:24px;margin:22px 0;border-radius:10px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}
figure{margin:0}img{display:block;width:100%;height:auto;border-radius:6px}figcaption{padding:12px 0;font-size:15px}
.status{border-left:5px solid #19838b}.small{font-size:14px;color:#51676f}.button{display:inline-block;padding:10px 16px;background:#dcebed;border-radius:7px}
@media(max-width:700px){.grid{grid-template-columns:1fr}main{padding:18px}h1{font-size:28px}}
</style><main><p><a href="../../fabrication/concentric-border-study/index.html">← Circular plate review</a></p>
<h1>The rear installation, as photographed</h1>
<section class="status"><h2>No foam is installed at this stage</h2>
<p>Your clarification is recorded: the valve is exposed and the foam-backed factory inner plate is removed.
The earlier approximately 6 mm foam thickness/width and 15.44 mm free overall depth describe that removed part.
Foam in an exploded or future assembly view belongs to its eventual reinstallation. It is not cavity filling.</p></section>
<div class="grid">'''+''.join(cards)+'''</div>
<section><h2>Why the old rear view was misleading</h2><p>The front Polycam capture contains visible surfaces, not a complete solid reconstruction of the plumbing and framing behind them.
Seeing its back faces—or the older simplified valve envelopes—does not reveal the real rear assembly.</p>
<p>The updated Blender review opens to these packed photographs. Its <b>REAR01 | current front scan ONLY</b> scene contains the preserved scan without factory trim, gasket or proposed parts.
The original proposal and exploded scenes remain available as references. The photos are unscaled boards, not a measured 3D registration.</p>
<p><a class="button" href="../../blender/installation_REAR01_DRAFT.blend">Updated Blender review</a> · <a href="rear_photos_REAR01.png">Photo board</a></p></section>
<section><h2>What the wood contact means</h2><p>Kohler's trim studs thread into the valve. They do not obtain their trim retention by fastening into wood.
If their rear ends already bear on the wood, that contact could prevent sufficient inward adjustment.
<a href="https://resources.kohler.com/onlinecatalog/pdf/1041504_2.pdf">Kohler installation guide, page 7</a>.</p>
<p>A clearance pocket is an option to evaluate after tracing the same two studs and determining the required retraction, remaining thread engagement and the wood member's role.
The photos do not establish a pocket size or authorize choosing drilling over a suitable hardware correction. The nearby pipe and cable routes also need to be accounted for.</p>
<p>Moving a trim stud inward would not by itself change valve-body or handle-stem depth. The U-handle engagement and final gasket/cover seating checks remain separate.</p></section>
<p class="small">REAR-001 revision 1 · received October 15, 2026 · photographs preserved byte-for-byte · no CAD dimensions or physical readiness changed.
<a href="blender_validation.json">Saved-file checks</a>. No drilling, cutting, vendor upload or order performed.</p></main></html>'''
(OUT / 'index.html').write_text(page)
panel = '''<!-- REAR01 BEGIN --><section class="panel" id="rear-evidence"><h2>Current rear photographs — no installed foam</h2>
<p>The foam-backed factory inner plate is removed. The front scan's back faces do not reconstruct the rear plumbing or wood.
<a href="../../review/rear/index.html">See the rear photos and corrected state explanation</a>, or open the
<a href="../../blender/installation_REAR01_DRAFT.blend">updated Blender review</a>.</p></section><!-- REAR01 END -->'''
index = ROOT / 'deliverables/current/fabrication/concentric-border-study/index.html'
if index.exists():
    text = re.sub(r'<!-- REAR01 BEGIN -->.*?<!-- REAR01 END -->', '', index.read_text(), flags=re.S)
    assert '<main>' in text
    index.write_text(text.replace('<main>', '<main>'+panel, 1))
print('REAR01 HTML and original photo copies prepared.')
