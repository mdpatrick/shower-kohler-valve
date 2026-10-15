"""Cross-representation checks on generated files, separate from physical fit."""
import json, unittest
from pathlib import Path
import numpy as np
import ezdxf
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]

class SnapshotTests(unittest.TestCase):
    def test_outer_step_uses_measured_upper_bore_without_copying_to_lower(self):
        import cadquery as cq
        records={m['id']:m for m in json.loads((ROOT/'canon/measurements.json').read_text())['measurements'] if m['status']=='user-confirmed'}
        if 'M12-UD' not in records:self.skipTest('No outer-cover readings')
        cover=cq.importers.importStep(str(ROOT/'deliverables/current/cad/TRIM-OUTER_DRAFT_NOT_FOR_FABRICATION.step')).val()
        self.assertAlmostEqual(cover.BoundingBox().xlen,records['M06-OD']['value_mm'],places=5)
        d=json.loads((ROOT/'deliverables/current/analysis/resolved.json').read_text())
        circles=[e for e in cover.Edges() if e.geomType()=='CIRCLE']
        for hole in d['outer_control_openings']:
            self.assertTrue(any(abs(e.radius()*2-hole['diameter_mm'])<1e-5 and np.linalg.norm(np.array(e.arcCenter().toTuple()[:2])-hole['center_local_mm'])<1e-5 for e in circles))
        if 'M12-LD' not in records:
            self.assertEqual(d['outer_control_openings'][0]['diameter_mm'],36)
            self.assertIsNone(d['outer_plate_constraints']['vertical_center_spacing_mm'])
        self.assertEqual(records['M06-OD']['raw_unit'],'in')
        self.assertIsNone(records['M06-OD']['uncertainty_mm'])

    def test_inner_step_carries_accepted_plate_dimensions(self):
        import cadquery as cq
        measurements=json.loads((ROOT/'canon/measurements.json').read_text())['measurements']
        accepted={m['id']:m['value_mm'] for m in measurements if m['status']=='user-confirmed'}
        if 'M11-UD' not in accepted:self.skipTest('No actual plate readings yet')
        plate=cq.importers.importStep(str(ROOT/'deliverables/current/cad/PLATE-INNER_DRAFT_NOT_FOR_FABRICATION.step')).val()
        bounds=plate.BoundingBox()
        self.assertAlmostEqual(bounds.xlen,accepted['M02-W'],places=5)
        self.assertAlmostEqual(bounds.ylen,accepted['M02-H'],places=5)
        circles=[e for e in plate.Edges() if e.geomType()=='CIRCLE']
        self.assertTrue(any(abs(e.radius()*2-accepted['M11-UD'])<1e-5 for e in circles))
        self.assertTrue(any(abs(e.radius()*2-accepted['M11-SWD'])<1e-5 for e in circles))

    def test_uniform_right_handed_transform(self):
        reg=json.loads((ROOT/'deliverables/current/analysis/registration.json').read_text())
        T=np.array(reg['raw_to_installed_mm']);A=T[:3,:3];B=np.array(reg['installed_mm_to_blender_m'])
        s=np.linalg.svd(A,compute_uv=False)
        self.assertLess(np.max(s)-np.min(s),1e-9);self.assertGreater(np.linalg.det(A),0)
        np.testing.assert_allclose(B@np.array([100,60,4,1]),[.1,-.004,.06,1],atol=1e-12)
        np.testing.assert_allclose(np.array(reg['raw_to_blender_m']),B@T,atol=1e-12)

    def test_free_plate_envelope_matches_measurement_without_assuming_compression(self):
        records={m['id']:m for m in json.loads((ROOT/'canon/measurements.json').read_text())['measurements'] if m['status']=='user-confirmed'}
        if 'M04-O' not in records:self.skipTest('No free-depth measurement')
        report=json.loads((ROOT/'deliverables/current/analysis/depth_stack.json').read_text())
        for case in report['cases'].values():
            ranges=case['ranges_z_mm']
            self.assertAlmostEqual(ranges['PLATE-INNER'][1]-ranges['GASKET-01'][0],records['M04-O']['value_mm'],places=5)
            self.assertAlmostEqual(ranges['GASKET-01'][1]-ranges['GASKET-01'][0],records['M05-T']['value_mm'],places=5)
        self.assertIsNone(report['inner_plate_depth']['installed_foam_thickness_mm'])
        self.assertNotIn('M04-D',records)

    def test_dxf_has_no_cuttable_labels(self):
        doc=ezdxf.readfile(ROOT/'deliverables/current/cad/CUSTOM-01_DRAFT_NOT_FOR_FABRICATION.dxf')
        self.assertEqual(doc.units,4)
        self.assertEqual({e.dxftype() for e in doc.modelspace()},{'LINE','ARC','CIRCLE'})
        self.assertEqual(len(doc.modelspace().query('CIRCLE')),1)
        self.assertEqual(len(doc.modelspace().query('ARC')),4)
        self.assertEqual(len(doc.modelspace().query('LINE')),4)

    def test_pdf_two_axis_calibration_in_page_coordinates(self):
        rev=json.loads((ROOT/'canon/measurements.json').read_text())['revision']
        pdf=PdfReader(ROOT/f'deliverables/current/drawings/profile_template_{rev}_DRAFT.pdf')
        self.assertEqual(len(pdf.pages),4)
        expected=[([55,120],[55+100*72/25.4,120]),([525,255],[525,255+100*72/25.4])]
        for page in pdf.pages:
            matrix=np.eye(3);stack=[];last=None;lines=[]
            for operands,op in page.get_contents().operations:
                if op==b'q':stack.append(matrix.copy())
                elif op==b'Q':matrix=stack.pop()
                elif op==b'cm':
                    a,b,c,d,e,f=map(float,operands);matrix=matrix@np.array([[a,c,e],[b,d,f],[0,0,1]])
                elif op in (b'm',b'l'):
                    p=(matrix@np.r_[list(map(float,operands)),1])[:2]
                    if op==b'l' and last is not None:lines.append((last,p))
                    last=p
            for start,end in expected:
                self.assertTrue(any(np.linalg.norm(a-start)<1e-3 and np.linalg.norm(b-end)<1e-3 for a,b in lines))

    def test_no_accidental_fit_or_fabrication_pass(self):
        state=json.loads((ROOT/'canon/project_state.json').read_text())
        self.assertIsNone(state['selected_state'])
        self.assertEqual(state['readiness']['fabrication_approval'],'NOT GIVEN')
        checks=json.loads((ROOT/'deliverables/current/analysis/checks.json').read_text())
        self.assertTrue(all(c['status'] in ('UNRESOLVED','FAIL') for c in checks['coverage']+checks['checks'] if c['id' if 'id' in c else 'feature_id']!='POST-SCAN-STATE'))
        for c in checks['checks']:
            if c['status']=='FAIL':self.assertEqual(c['physical_fit'],'UNRESOLVED')

    def test_depth_reports_real_solid_conflicts_without_moving_studs(self):
        report=json.loads((ROOT/'deliverables/current/analysis/depth_stack.json').read_text())
        resolved=json.loads((ROOT/'data/derived/resolved.json').read_text())
        for case in report['cases'].values():
            self.assertFalse(case['captured_hardware_adjusted'])
            for stud,observed in zip(case['studs'],resolved['studs_mm']):
                self.assertAlmostEqual(stud['tip_z_mm'],observed[2])
                if stud['tip_to_cover_rear_clearance_mm']<0:
                    clash=next(c for c in case['collisions'] if c['part']==stud['id'])
                    self.assertGreater(clash['intersection_mm3'],0)
                    self.assertEqual(clash['model_result'],'FAIL')
            self.assertEqual(case['physical_fit'],'UNRESOLVED')

    def test_factory_comparison_preserves_captured_hardware(self):
        parts=json.loads((ROOT/'deliverables/current/cad/cad_manifest.json').read_text())['parts']
        d=json.loads((ROOT/'deliverables/current/analysis/resolved.json').read_text())
        shift=d['candidate']['thickness_mm']+d['candidate']['seal_display_thickness_mm']
        for p in parts:
            factory=p['factory_location_mm'];placed=p['location_mm']
            if p['id'] in ('CUSTOM-01','NEW-SEAL-PATH'):
                self.assertIsNone(factory);continue
            expected=np.array(placed)
            if p['collection'] in ('02_INNER_AND_GASKET','03_OUTER_TRIM'):expected[2]-=shift
            np.testing.assert_allclose(factory,expected,atol=1e-10)
        for id in ('HANDLE-LOWER','HANDLE-UPPER'):
            p=next(p for p in parts if p['id']==id);side=0 if id=='HANDLE-LOWER' else 1
            self.assertAlmostEqual(abs(p['bounds_local_mm'][side][1]),76.2)

    def test_neighbor_clearance_uses_separate_diverter(self):
        d=json.loads((ROOT/'deliverables/current/analysis/resolved.json').read_text())
        checks=json.loads((ROOT/'deliverables/current/analysis/checks.json').read_text())['checks']
        c=next(c for c in checks if c['id']=='NEIGHBOR-TRIM-CLEARANCE')
        separation=np.linalg.norm(np.array(d['trim_center_mm'])-np.array(d['diverter_tip_mm'][:2]))
        self.assertAlmostEqual(c['candidate_to_diverter_gap_mm'],separation-d['candidate']['diameter_mm']/2-d['nominal']['diverter_trim']['diameter_mm']/2)
        self.assertEqual(c['status'],'UNRESOLVED')

if __name__=='__main__':unittest.main()
