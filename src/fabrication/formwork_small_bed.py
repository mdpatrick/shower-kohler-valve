"""RF04: trim only the perimeter of the approved RF03 relieved-form CAD."""
from pathlib import Path
import sys, json, shutil, hashlib
import cadquery as cq
import trimesh
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.fabrication.formwork_print import write_3mf, read_3mf_mesh

OUT = ROOT / 'deliverables/current/fabrication/FT02/formwork-small-bed'
PACK = OUT / 'SEND_TO_PRINTER'
CFG = json.loads((ROOT / 'canon/formwork_small_bed_RF04.json').read_text())
OLD = ROOT / 'deliverables/current/fabrication/FT02/formwork-print/SEND_TO_PRINTER'
STEM = 'RF04_SMALL_192_55_D24_RELIEVED_mm'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build():
    small = PACK / 'SMALL_RF04'
    original = PACK / 'ORIGINAL_RF03'
    small.mkdir(parents=True, exist_ok=True)
    original.mkdir(parents=True, exist_ok=True)
    copies = []
    sources = [OLD / 'OPTIONAL_DEEPER/PRINT_INSTEAD_RF03_D24_RELIEVED.stl',
               OLD / 'OPTIONAL_DEEPER/PRINT_INSTEAD_RF03_D24_RELIEVED.3mf',
               OLD / 'CAD_REFERENCE/RF03_D24_RELIEVED_mm.step']
    for src in sources:
        dst = original / src.name
        shutil.copyfile(src, dst)
        assert sha(src) == sha(dst)
        copies.append({'source': str(src.relative_to(ROOT)), 'file': str(dst.relative_to(PACK)), 'sha256': sha(src)})
    old = cq.importers.importStep(str(ROOT / CFG['source_STEP'])).val()
    diameter = CFG['panel_diameter_mm']
    crop = cq.Workplane('XY', origin=(120, 120, -1)).circle(diameter / 2).extrude(34).val()
    aligned = old.intersect(crop)
    new = aligned.translate(tuple(CFG['print_translation_from_RF03_mm']))
    assert new.isValid() and len(new.Solids()) == 1
    removed = old.cut(aligned)
    assert removed.BoundingBox().zmax <= 8.0001
    assert aligned.cut(old).Volume() < .001
    # Preserve all central geometry, not merely selected feature coordinates.
    center = cq.Workplane('XY', origin=(120, 120, -1)).circle(85).extrude(34).val()
    a, b = old.intersect(center), aligned.intersect(center)
    central_delta = a.cut(b).Volume() + b.cut(a).Volume()
    assert central_delta < .001
    collar_half = cq.Workplane('XY', origin=(120, 120, 8)).box(300, 300, 25, centered=(True, True, False)).val()
    a, b = old.intersect(collar_half), aligned.intersect(collar_half)
    collar_delta = a.cut(b).Volume() + b.cut(a).Volume()
    assert collar_delta < .001
    stl, mf, step = [small / (STEM + ext) for ext in ['.stl', '.3mf', '.step']]
    cq.exporters.export(new, str(step))
    cq.exporters.export(new, str(stl), tolerance=.01, angularTolerance=.03)
    mesh = trimesh.load(stl, force='mesh')
    assert mesh.is_volume and len(mesh.split()) == 1
    assert np.allclose(mesh.bounds, [[0, 0, 0], [diameter, diameter, 32]], atol=.02)
    write_3mf(mesh, mf, 'RF04 smaller-face relieved temporary repair form; millimeters')
    rb = cq.importers.importStep(str(step)).val()
    rm = read_3mf_mesh(mf)
    assert rb.isValid() and abs(rb.Volume() - new.Volume()) < .01
    assert rm.is_volume and abs(rm.volume - mesh.volume) < .02
    report = {
        'revision': 'RF04', 'scope': 'CAD/export checks only; no physical fit or slicer run',
        'source_STEP_sha256': sha(ROOT / CFG['source_STEP']),
        'config_sha256': sha(ROOT / 'canon/formwork_small_bed_RF04.json'),
        'size_mm': [diameter, diameter, 32], 'original_size_mm': [240, 240, 32],
        'solid_volume_mm3': new.Volume(), 'original_solid_volume_mm3': old.Volume(),
        'CAD_volume_reduction_percent': 100 * (1 - new.Volume() / old.Volume()),
        'solid_mass_upper_bound_g_at_1_30': new.Volume() / 1000 * 1.30,
        'removed_geometry_max_print_z_mm': removed.BoundingBox().zmax,
        'central_geometry_symmetric_difference_mm3': central_delta,
        'rear_collar_symmetric_difference_mm3': collar_delta,
        'new_material_outside_original_mm3': aligned.cut(old).Volume(),
        'originals_preserved': copies,
        'files': [{'file': str(p.relative_to(PACK)), 'sha256': sha(p), 'bytes': p.stat().st_size} for p in [stl, mf, step]],
        'physical_fit': 'NOT PERFORMED', 'permanent_use': 'NOT APPROVED',
        'capture': CFG['capture_scope']
    }
    (OUT / 'geometry_checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    build()
