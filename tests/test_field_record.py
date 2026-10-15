"""Exercise saved form data, not just the visible blank PDF.

All synthetic observer results stay in ignored build/, never in evidence/canon.
"""
import hashlib
import json
from pathlib import Path
import unittest

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, NameObject
from src.fabrication.field_record import build, validate_form

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/fit_trial/field-record-test'


class FieldRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OUT.mkdir(parents=True,exist_ok=True)
        cls.protected={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                       [ROOT/'canon/project_state.json',ROOT/'canon/fit_trial_design.json']}
        cls.path=build(json.loads((ROOT/'canon/fit_trial_design.json').read_text()),OUT)
        cls.schema=OUT/'field_record_schema.json'

    def test_blank_has_no_observations(self):
        result=validate_form(self.path,self.schema)
        self.assertEqual(result['pages'],4)
        self.assertEqual(result['fields'],75)
        blank=json.loads((OUT/'field_record_blank.json').read_text())
        self.assertEqual(set(blank['values'].values()),{'','NOT RECORDED'})
        self.assertFalse(blank['permanent_installation_release'])
        self.assertEqual(blank['physical_fit'],'NOT PERFORMED')

    def test_fill_all_pages_save_and_reopen(self):
        sample={'observer':'TEST ONLY - NO EVIDENCE',
                'P16_main_width':'123.45 TEST',
                'P17_condition':'TEST ONLY: example defect\nSee synthetic photograph reference.',
                'record_page2':'TEST RECORD - PAGE 2',
                'P10_U_factory':'FAIL',
                'record_page3':'TEST RECORD - PAGE 3',
                'P07_contact_status':'UNRESOLVED',
                'P07_contact_evidence':'TEST ONLY: contact hidden',
                'record_page4':'TEST RECORD - PAGE 4',
                'P19_status':'NOT RECORDED',
                'P20_status':'NOT RECORDED',
                'expert_disposition':'TEST ONLY: no approval.\nReturn the revised detail for review.'}
        writer=PdfWriter();writer.clone_document_from_reader(PdfReader(self.path))
        writer.update_page_form_field_values(None,sample,auto_regenerate=False)
        target=OUT/'synthetic_filled_NOT_EVIDENCE.pdf'
        writer.write(target)
        check=validate_form(target,self.schema,sample)
        self.assertEqual(check['fields'],75)
        self.assertFalse(PdfReader(target).trailer['/Root']['/AcroForm']['/NeedAppearances'].value)
        self.assertEqual(self.protected,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.protected})
        (OUT/'roundtrip.json').write_text(json.dumps(dict(status='PASS',scope='Synthetic form round trip only',
               validation=check,canonical_files_unchanged=True,synthetic_values=sample),indent=2)+'\n')

    def test_visible_widget_without_canonical_field_is_rejected(self):
        writer=PdfWriter();writer.clone_document_from_reader(PdfReader(self.path))
        tree=writer.root_object['/AcroForm']
        tree[NameObject('/Fields')]=ArrayObject(tree['/Fields'][1:])
        target=OUT/'orphan_widget_NOT_EVIDENCE.pdf';writer.write(target)
        # Page widget still exists and can look normal; saved logical data is incomplete.
        reader=PdfReader(target)
        self.assertTrue(any(a.get_object().get('/T')=='record_id' for a in reader.pages[0]['/Annots']))
        with self.assertRaises(AssertionError):validate_form(target,self.schema)


if __name__=='__main__':unittest.main()
