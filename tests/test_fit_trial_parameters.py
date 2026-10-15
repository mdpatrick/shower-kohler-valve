"""Regression: changed design must change every manufactured profile and handoff.

The variant is deliberately unpublished and lives only under build/. Its values
are test stimuli, not accepted physical measurements or a design recommendation.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import unittest
import zipfile

import cadquery as cq
from pypdf import PdfReader

from src.fabrication.fit_trial_spec import validate_design, values, expand

ROOT=Path(__file__).resolve().parents[1]
CURRENT=ROOT/'deliverables/current/fabrication/fit-trial'
TEST=ROOT/'build/fit_trial/parameter-propagation'

class ParameterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design=json.loads((ROOT/'canon/fit_trial_design.json').read_text())
        cls.variant=copy.deepcopy(cls.design)
        cls.variant['main'].update(outer_diameter_mm=218,aperture_width_mm=116.85,
            aperture_height_mm=151.60,aperture_radius_mm=58.425,straight_side_length_mm=34.75)
        cls.variant['diverter'].update(outer_diameter_mm=122,fallback_outer_diameter_mm=118,aperture_diameter_mm=78)
        cls.variant['foam'].update(nominal_aperture_inset_mm=6.75,nominal_extra_land_mm=.75)
        for s,t in zip(cls.variant['stocks'],[2.,3.2]):
            s.update(id=f'T{round(t*1000):04d}',thickness_mm=t)

    def test_inconsistent_geometry_fails_before_export(self):
        from src.fabrication.fit_trial import run
        for key,value in [('aperture_radius_mm',50),('straight_side_length_mm',20),('aperture_center_mm',[1,0])]:
            d=copy.deepcopy(self.design);d['main'][key]=value
            output=TEST/('invalid-'+key)
            with self.assertRaises(ValueError):run(d,output)
            self.assertFalse(output.exists())

    def test_unknown_dimension_token_cannot_silently_survive(self):
        with self.assertRaises(KeyError):expand('Opening [[made_up]]',{})

    def test_documents_reject_stale_analysis(self):
        from src.fabrication import fit_trial_documents as docs
        with self.assertRaises(AssertionError):
            docs.configure(self.variant,json.loads((CURRENT/'design_report.json').read_text()),TEST/'stale')

    def test_changed_parameters_reach_real_files(self):
        from src.fabrication import fit_trial,fit_trial_documents as docs
        from src.fabrication.audit_fit_trial import check_paper_profiles
        before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [ROOT/'canon/fit_trial_design.json',CURRENT/'design_report.json']}
        out=TEST/'variant';out.mkdir(parents=True,exist_ok=True)
        for name in ['paired_front.png','plane_front.png','paired_oblique.png','exploded.png']:
            shutil.copy2(CURRENT/name,out/name)
        fit_trial.run(self.variant,out)
        r=json.loads((out/'design_report.json').read_text())
        docs.run(self.variant,r,out)
        for p in r['parts']:
            solid=cq.importers.importStep(str(out/p['files']['step'])).val()
            self.assertAlmostEqual(solid.BoundingBox().xlen,218 if p['kind']=='MAIN' else 122 if p['kind']=='DIV' else 118,places=6)
            self.assertAlmostEqual(solid.BoundingBox().zlen,2 if p['stock']=='T2000' else 3.2,places=6)
            inner=min(cq.Workplane(obj=solid).faces('>Z').val().Wires(),key=lambda w:w.BoundingBox().xlen).BoundingBox()
            self.assertAlmostEqual(inner.xlen,116.85 if p['kind']=='MAIN' else 78,places=6)
            self.assertAlmostEqual(inner.ylen,151.60 if p['kind']=='MAIN' else 78,places=6)
        check_paper_profiles(out,self.variant)
        with self.assertRaises(AssertionError):check_paper_profiles(CURRENT,self.variant)
        shop=''.join(p.extract_text() for p in PdfReader(out/'shop_drawings_FT01.pdf').pages)
        for value in ['OUTSIDE DIAMETER 218.00','OUTSIDE DIAMETER 122.00','OPENING WIDTH 116.85',
                      'OPENING HEIGHT 151.60','R58.425','THROUGH DIAMETER 78.00','T2000 = 2.000','T3200 = 3.200']:
            self.assertIn(value,shop)
        page=(out/'index.html').read_text()
        for value in ['Ø218 / diverter Ø122','T2000 is 2.000 mm','+1.200 mm','0.75 mm','FT01_recommended_T2000_quote.zip']:
            self.assertIn(value,page)
        self.assertNotIn('[[',page)
        for base,case in zip(json.loads((CURRENT/'design_report.json').read_text())['placement_scenarios'],r['placement_scenarios']):
            self.assertAlmostEqual(case['gap_main_diverter_mm'],base['gap_main_diverter_mm']+2)
            self.assertAlmostEqual(case['main_margin_after_trace_mm'],base['main_margin_after_trace_mm']-1)
        for stock in ['T2000','T3200']:
            zpath=out/f'FT01_{"recommended" if stock=="T2000" else "plastic"}_{stock}_quote.zip'
            with zipfile.ZipFile(zpath) as z:
                self.assertIsNone(z.testzip())
                notes=z.read('READ_ME.txt').decode()
                self.assertIn('MAIN218 plus one DIV122',notes)
                self.assertNotIn('[[',notes)
                for name,digest in json.loads(z.read('SHA256.json')).items():
                    self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),digest)
        self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in before})
        (TEST/'result.json').write_text(json.dumps({'status':'PASS','scope':'Unpublished changed-dimension CAD / paper geometry / labels / HTML / quote package regression','variant':self.variant,'canonical_inputs_unchanged':True},indent=2)+'\n')

if __name__=='__main__':unittest.main()
