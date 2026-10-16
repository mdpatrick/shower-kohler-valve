"""A legitimate dependency rebuild must pass; later mutation must not."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.fabrication.audit_aperture import check_preserved_files, REAR, RECEIPT


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.original={name:('original '+name).encode() for name in [
            'canon/measurements.json','canon/transforms.json','canon/fabrication_designs.json',
            'data/evidence/kohler-T14489-4.obj',REAR]}
        for name,data in self.original.items():
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        mock=patch('src.fabrication.audit_aperture.subprocess.check_output',
                   side_effect=lambda args,**kw:self.original[args[-1].split(':',1)[1]])
        mock.start();self.addCleanup(mock.stop)

    def regenerated_rear(self):
        data=b'legitimate newly serialized Blender dependency'
        (self.root/REAR).write_bytes(data)
        return hashlib.sha256(data).hexdigest()

    def test_legacy_snapshot_has_no_silent_new_baseline(self):
        _,record=check_preserved_files(self.root)
        self.assertIn('Legacy',record['scope'])
        self.regenerated_rear()
        with self.assertRaisesRegex(AssertionError,'Generated rear input changed'):
            check_preserved_files(self.root)

    def test_legitimate_rebuild_passes_with_preparation_baseline(self):
        expected=self.regenerated_rear()
        immutable,record=check_preserved_files(self.root,expected)
        self.assertTrue(all(immutable.values()))
        self.assertEqual(record['sha256'],expected)

    def test_mutation_during_aperture_stage_is_rejected(self):
        expected=self.regenerated_rear()
        (self.root/REAR).write_bytes(b'changed by AP01')
        with self.assertRaisesRegex(AssertionError,'Generated rear input changed'):
            check_preserved_files(self.root,expected)

    def test_accepted_evidence_remains_immutable(self):
        expected=self.regenerated_rear()
        (self.root/'canon/measurements.json').write_bytes(b'changed evidence')
        with self.assertRaisesRegex(AssertionError,'Immutable AP01 evidence changed'):
            check_preserved_files(self.root,expected)

    def test_standalone_readback_requires_saved_success_and_matching_bytes(self):
        expected=self.regenerated_rear()
        _,record=check_preserved_files(self.root,expected)
        p=self.root/RECEIPT;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps({'status':'PASS','generated_rear_preservation':record}))
        _,again=check_preserved_files(self.root)
        self.assertEqual(again['sha256'],expected)
        (self.root/REAR).write_bytes(b'changed since successful preparation')
        with self.assertRaisesRegex(AssertionError,'Generated rear input changed'):
            check_preserved_files(self.root)
        self.regenerated_rear()
        p.write_text(json.dumps({'status':'FAIL','generated_rear_preservation':record}))
        with self.assertRaisesRegex(AssertionError,'No successful AP01 preservation receipt'):
            check_preserved_files(self.root)


if __name__=='__main__':unittest.main()
