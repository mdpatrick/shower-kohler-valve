"""Prevent historical model dimensions from masquerading as current CAD results."""
import copy
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
import unittest

from src.analysis.fit_trial_query import CurrentQuery,QueryError

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/fit_trial/query-check'


class QueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OUT.mkdir(parents=True,exist_ok=True)
        cls.q=CurrentQuery(ROOT)
        cls.before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                    [ROOT/'canon/measurements.json',ROOT/'canon/project_state.json',ROOT/'canon/fit_trial_design.json']}

    def cli(self,*args,success=True):
        p=subprocess.run([str(ROOT/'project'),'query',*args],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(p.returncode,0 if success else 2,p.stderr+p.stdout)
        return json.loads(p.stdout)

    def test_default_cli_returns_current_and_history_is_explicit(self):
        current=self.cli('dimension','candidate.diameter_mm')
        historical=self.cli('historical','dimension','candidate.diameter_mm')
        self.assertEqual(current['result']['value'],220)
        self.assertEqual(current['design_revision'],'FT02')
        self.assertEqual(current['evidence_revision'],'R006')
        self.assertEqual(historical['result']['value'],230)
        self.assertEqual(historical['state'],'historical_reconstruction')
        self.assertFalse(historical['current_design_fit_result'])
        for args in [('dimension',),('dimension','candidate.target_sound_land_mm'),('solid','NO_SUCH_PART'),('invented',)]:
            self.assertEqual(self.cli(*args,success=False)['status'],'QUERY_ERROR')

    def test_current_step_solid_and_stock_selection(self):
        primary=self.q.solid('CUSTOM-01')
        alternate=self.q.solid('DIV','T1500')
        for response,od,t in [(primary,220,1.52),(alternate,124,1.5)]:
            r=response['result'];lo,hi=r['bounds_local_mm']
            self.assertAlmostEqual(hi[0]-lo[0],od,places=6)
            self.assertAlmostEqual(hi[1]-lo[1],od,places=6)
            self.assertAlmostEqual(hi[2]-lo[2],t,places=6)
            self.assertTrue(r['is_valid']);self.assertEqual(r['solid_count'],1)
            self.assertFalse(response['permanent_installation_release'])
        with self.assertRaises(QueryError):self.q.solid(primary['result']['id'],'T1500')
        (OUT/'solid_examples.json').write_text(json.dumps([primary,alternate],indent=2)+'\n')

    def test_coverage_uses_current_circle_in_all_three_states(self):
        response=self.q.coverage('CUT-03')
        cases=response['result']['scenarios']
        self.assertEqual(len(cases),3)
        original=next(c for c in cases if c['state']=='ORIGINAL')
        self.assertAlmostEqual(original['features'][0]['outer_margin_after_trace_mm'],7.40539333102258,places=8)
        self.assertAlmostEqual(original['gap_main_diverter_mm'],3.2378463437339917,places=8)
        for c in cases:
            self.assertEqual(c['main_diameter_mm'],220)
            self.assertEqual(c['features'][0]['result_status'],'UNRESOLVED_FIELD_FIT')
            self.assertEqual(c['features'][0]['feature_id'],'CUT-03')
        self.assertEqual(response['physical_fit'],'NOT PERFORMED')
        self.assertEqual(len(self.q.coverage()['result']['scenarios'][0]['features']),8)
        with self.assertRaises(QueryError):self.q.coverage('OPEN-LOWER-AUX')
        (OUT/'coverage_example.json').write_text(json.dumps(response,indent=2)+'\n')

    def test_stale_design_or_source_cannot_supply_derived_claim(self):
        with tempfile.TemporaryDirectory(dir=OUT) as temp:
            root=Path(temp)
            paths=['canon/fit_trial_design.json','canon/project_state.json','canon/measurements.json',
                   'deliverables/current/fabrication/FT02/design_report.json']
            for rel in paths:
                p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/rel).read_bytes())
            p=root/'canon/fit_trial_design.json';d=json.loads(p.read_text());d['main']['outer_diameter_mm']=222
            p.write_text(json.dumps(d))
            q=CurrentQuery(root)
            self.assertEqual(q.dimension('main.outer_diameter_mm')['result']['value'],222)
            with self.assertRaisesRegex(QueryError,'Stale fit-trial report'):q.clearance()
            p.write_bytes((ROOT/'canon/fit_trial_design.json').read_bytes())
            p=root/paths[-1];report=json.loads(p.read_text())
            report['sources_sha256']={'canon/fit_trial_design.json':'0'*64};p.write_text(json.dumps(report))
            with self.assertRaisesRegex(QueryError,'Stale fit-trial source'):CurrentQuery(root).clearance()

    def test_current_unknown_depth_and_historical_views_are_distinct(self):
        r=self.cli('depth')
        for key in ['effective_bedding_height_mm','actual_compressed_foam_height_mm','installed_rod_projection_mm','actual_adapter_engagement_mm']:
            self.assertIsNone(r['result'][key])
        section=self.cli('section','controls')
        self.assertEqual(section['state'],'historical_reconstruction')
        self.assertFalse(section['current_design_fit_result'])
        measured=self.cli('measure','AXIS-UPPER-TIP','AXIS-LOWER-TIP')
        self.assertEqual(measured['state'],'preserved_evidence_registry')
        self.assertIn('approximate',measured['result']['method'])
        clear=self.q.clearance()
        self.assertIn('Read saved',clear['method'])
        self.assertIn('excludes stone',clear['result']['geometric_check_scope'])
        self.assertIn('expanded_local_study',clear['result'])
        self.assertIn('full_capture_checks',clear['result']['expanded_local_study'])
        states=self.q.compare_states()
        self.assertIsNone(states['result']['physical_selected_arrangement'])

    @classmethod
    def tearDownClass(cls):
        after={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in cls.before}
        if after!=cls.before:raise AssertionError('A query changed accepted/project state')


if __name__=='__main__':unittest.main()
