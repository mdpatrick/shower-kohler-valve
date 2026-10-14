"""A plausible projection must not approve an unidentified control or move a valve."""
import copy,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('rough_in',ROOT/'src/analysis/rough_in.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class RoughInTests(unittest.TestCase):
    def setUp(self):
        nominal=json.loads((ROOT/'canon/design_decisions.json').read_text())['nominal_parameters']
        self.d={'nominal':nominal,'controls_mm':[[0,0,33.4],[1.6,79.3,31.9548163734]],
                'diagnostic_control_depths_mm':{}}

    def test_original_upper_tip_flags_conditional_depth(self):
        r=module.analyze_rough_in(self.d)
        self.assertAlmostEqual(r['nominal_bare_upper_tip_from_tile_mm'][1],26.9875)
        self.assertGreater(r['conditional_excess_above_nominal_max_mm'],4)
        self.assertLess(r['conditional_excess_above_nominal_max_mm'],6)
        self.assertFalse(r['same_bare_tip_verified'])
        self.assertEqual(r['status'],'UNRESOLVED')

    def test_plausible_measurement_cannot_approve_or_reposition(self):
        self.d['diagnostic_control_depths_mm']={'upper':20,'lower':-3}
        original=copy.deepcopy(self.d)
        r=module.analyze_rough_in(self.d)
        self.assertEqual(self.d,original)
        self.assertEqual(r['comparison_tip_mm'],20)
        self.assertEqual(r['status'],'UNRESOLVED')
        self.assertEqual(r['physical_fit'],'UNRESOLVED')
        self.assertIsNone(r['valve_move_target_mm'])
        self.assertFalse(r['same_bare_tip_verified'])
        self.assertNotEqual(r['comparison_tip_mm'],r['scan_upper_tip_from_tile_mm'])

if __name__=='__main__':unittest.main()
