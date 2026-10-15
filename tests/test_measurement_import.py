"""Exercise observation history and rejection paths in disposable project copies."""
import copy, importlib.util, json, shutil, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('observation_import',ROOT/'src/analysis/import_measurements.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        for name in ['canon/measurements.json','canon/project_state.json','data/derived/resolved.json']:
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p)
        self.path=self.root/'response.json'
        self.canon_path=self.root/'canon/measurements.json'
        # Disposable empty canon keeps importer tests independent of real observations.
        self.canon_path.write_text(json.dumps(dict(project_id='shower-kohler-valve',revision='R001',measurements=[],history=[])))
        self.original=self.canon_path.read_bytes()
        self.revision=json.loads(self.original)['revision']

    def tearDown(self):self.tmp.cleanup()

    def observation(self,id,value,unit='mm',**kwargs):
        return dict(measurement_id=id,raw_readings=value if isinstance(value,list) else [value],unit=unit,
                    method='test caliper',date='2026-10-14',**kwargs)

    def submit(self,items,**kwargs):
        packet=dict(project_id='shower-kohler-valve',review_revision=self.revision,observations=items)
        packet.update(kwargs);self.path.write_text(json.dumps(packet))
        return module.import_response(self.path,self.root)

    def accepted(self):return {m['id']:m for m in json.loads(self.canon_path.read_text())['measurements'] if m['status']=='user-confirmed'}
    def advance(self):self.revision=json.loads(self.canon_path.read_text())['revision']

    def test_empty_is_not_confirmation(self):
        self.assertEqual(self.submit([])['status'],'no changes');self.assertEqual(self.original,self.canon_path.read_bytes())

    def test_inch_conversion_and_derived_spacing(self):
        self.submit([self.observation('M01-O',4,'in'),self.observation('M01-I',2.25,'in')])
        self.assertAlmostEqual(self.accepted()['M01']['value_mm'],79.375)
        self.assertEqual(self.accepted()['M01-O']['raw_unit'],'in')
        self.assertEqual(self.accepted()['M01-O']['raw_readings'],[4])
        self.assertTrue((self.root/'canon/measurement_responses/R002.json').exists())
        state=json.loads((self.root/'canon/project_state.json').read_text())
        self.assertEqual(state['readiness']['fabrication_approval'],'NOT GIVEN')

    def test_stud_depth_relation(self):
        self.submit([self.observation('M07-H',50),self.observation('M07-GSW',23.5),self.observation('M07-GNE',19.2)])
        self.assertAlmostEqual(self.accepted()['M07-SW']['value_mm'],26.5)
        self.assertAlmostEqual(self.accepted()['M07-NE']['value_mm'],30.8)

    def test_round_hole_centers_require_both_diameters(self):
        self.submit([self.observation('M11-G',106.39),self.observation('M11-SWD',5.66),self.observation('M11-R',11.71)])
        self.assertNotIn('M11-CC',self.accepted());self.assertNotIn('M11-NERC',self.accepted())
        self.advance();self.submit([self.observation('M11-NED',6.0)])
        self.assertAlmostEqual(self.accepted()['M11-CC']['value_mm'],112.22)
        self.assertAlmostEqual(self.accepted()['M11-NERC']['value_mm'],14.71)

    def test_control_depth_is_signed_and_diagnostic(self):
        self.submit([self.observation('M10-H',2,'in'),self.observation('M10-GU',2.25,'in',notes='Adapter identity unknown'),self.observation('M10-GL',1.5,'in')])
        upper=self.accepted()['M10-UPPER'];lower=self.accepted()['M10-LOWER']
        self.assertAlmostEqual(upper['value_mm'],-6.35)
        self.assertAlmostEqual(lower['value_mm'],12.7)
        self.assertEqual(upper['role'],'diagnostic cross-check; tip identity required')
        self.assertEqual(self.accepted()['M10-GU']['notes'],'Adapter identity unknown')
        self.assertNotIn('M07-SW',self.accepted())

    def test_control_setup_cannot_borrow_stud_reference_height(self):
        self.submit([self.observation('M07-H',50),self.observation('M10-GU',18)])
        self.assertNotIn('M10-UPPER',self.accepted())

    def test_conflicting_repeat_does_not_calibrate(self):
        r=self.submit([self.observation('M01-O',[90,94])])
        self.assertIn('M01-O',r['conflicts']);self.assertNotIn('M01-O',self.accepted())

    def test_changed_value_keeps_prior_without_correction(self):
        self.submit([self.observation('M02-W',116)]);self.advance()
        r=self.submit([self.observation('M02-W',117)])
        self.assertIn('M02-W',r['conflicts']);self.assertEqual(self.accepted()['M02-W']['value_mm'],116)

    def test_explicit_correction_preserves_history(self):
        self.submit([self.observation('M02-W',116)]);self.advance()
        self.submit([self.observation('M02-W',117,correction_reason='Moved jaws to actual metal edges')])
        rows=json.loads(self.canon_path.read_text())['measurements']
        self.assertEqual([m['status'] for m in rows],['superseded','user-confirmed'])
        self.assertEqual(self.accepted()['M02-W']['value_mm'],117)

    def test_bad_repeat_cannot_supersede_good_measurement(self):
        self.submit([self.observation('M02-W',116)]);self.advance()
        self.submit([self.observation('M02-W',[117,120],correction_reason='Trying again')])
        self.assertEqual(self.accepted()['M02-W']['value_mm'],116)

    def test_independent_dimension_retains_role(self):
        self.submit([self.observation('M08-X',104)])
        self.assertEqual(self.accepted()['M08-X']['role'],'independent cross-check')
        self.assertNotIn('M01',self.accepted())

    def test_invalid_packets_do_not_write(self):
        cases=[dict(project_id='wrong'),dict(review_revision='R999'),dict(observations=[self.observation('unknown',1)]),
               dict(observations=[self.observation('M02-W',1,'feet')]),
               dict(observations=[self.observation('M02-W',-1)]),
               dict(observations=[self.observation('M02-W',True)]),
               dict(observations=[self.observation('M02-W',116,uncertainty_mm=float('nan'))]),
               dict(observations=[self.observation('M02-W',116),self.observation('M02-W',116)]),
               dict(observations=[self.observation('M01-O',60),self.observation('M01-I',70)]),
               dict(observations=[self.observation('M03-SW-XN',20),self.observation('M03-SW-XF',15)]),
               dict(observations=[self.observation('M07-H',20),self.observation('M07-GSW',30)])]
        for bad in cases:
            with self.subTest(bad=bad):
                items=bad.get('observations',[])
                with self.assertRaises(ValueError):self.submit(items,**{k:v for k,v in bad.items() if k!='observations'})
                self.assertEqual(self.original,self.canon_path.read_bytes())
                self.assertFalse((self.root/'canon/measurement_responses').exists())

    def test_dry_run_has_no_side_effects(self):
        self.path.write_text(json.dumps(dict(project_id='shower-kohler-valve',review_revision=self.revision,observations=[self.observation('M02-W',116)])))
        self.assertEqual(module.import_response(self.path,self.root,dry_run=True)['status'],'validated dry run')
        self.assertEqual(self.original,self.canon_path.read_bytes())

if __name__=='__main__':unittest.main()
