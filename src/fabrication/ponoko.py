"""Vendor cutting paths are distinct from authoritative finished-part CAD."""
from pathlib import Path
import copy,json,hashlib,math
import cadquery as cq
import ezdxf
from src.fabrication.fit_trial import make_main

def acrylic_path(d,part,destination):
    kerf=d['vendor_variant']['clear_kerf_mm'];x=copy.deepcopy(d)
    if part['kind']=='MAIN':
        m=x['main'];m['outer_diameter_mm']+=kerf;m['aperture_width_mm']-=kerf;m['aperture_height_mm']-=kerf;m['aperture_radius_mm']-=kerf/2
        s=make_main(x,1)
    else:
        s=cq.Workplane('XY').circle((d['diverter']['outer_diameter_mm']+kerf)/2).circle((d['diverter']['aperture_diameter_mm']-kerf)/2).extrude(1)
    wires=s.faces('>Z').wires().translate((0,0,-1))
    cq.exporters.export(wires,str(destination),exportType='DXF')
    doc=ezdxf.readfile(destination);doc.units=ezdxf.units.MM
    for entity in doc.modelspace():entity.dxf.layer='CUT'
    doc.saveas(destination)
    rb=cq.importers.importDXF(str(destination)).wires().toPending().extrude(1).val()
    assert rb.isValid() and len(rb.Solids())==1 and len(wires.vals())==2
    assert abs(rb.BoundingBox().xlen-(part['diameter_mm']+kerf))<1e-5
    assert abs(rb.Volume()-s.val().Volume())<.01
    return {'file':destination.name,'kerf_mm':kerf,'path_outer_diameter_mm':part['diameter_mm']+kerf,'finished_outer_diameter_mm':part['diameter_mm'],'outside_offset_mm':kerf/2,'aperture_offset_mm':-kerf/2,'readback':'PASS: mm, two closed contours, one extrudable solid, exact bounds/area','sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'note':'Nominal 0.20 mm CO2 burn compensation already applied to this DXF only. Do not apply a second compensation. Finished-part STEP and drawing govern target dimensions; actual kerf varies.'}
