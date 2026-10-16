"""Recovery compares numeric geometry exactly and copied observations to canon."""
import copy
import unittest

from scripts.verify_restore import compare_resolved


class RestoreValidationTests(unittest.TestCase):
    def setUp(self):
        self.old={'controls_mm':[[0,0,30],[0,80,32]],'observations':[{'id':'earlier','text':'accepted'}]}
        self.canon=self.old['observations']+[{'id':'later','text':'attached inner plate'}]
        self.new=copy.deepcopy(self.old);self.new['observations']=self.canon

    def test_accepted_observation_refresh_is_recorded(self):
        result=compare_resolved(self.old,self.new,self.canon)
        self.assertEqual(result['added_ids'],['later'])
        self.assertTrue(result['matches_accepted_canon'])

    def test_even_small_dimensional_change_is_rejected(self):
        self.new['controls_mm'][1][1]+=.001
        with self.assertRaisesRegex(AssertionError,'Resolved geometry changed'):
            compare_resolved(self.old,self.new,self.canon)

    def test_noncanonical_observation_or_omission_is_rejected(self):
        for observations in [self.old['observations'],self.canon+[{'id':'invented'}]]:
            self.new['observations']=observations
            with self.assertRaisesRegex(AssertionError,'observations disagree'):
                compare_resolved(self.old,self.new,self.canon)


if __name__=='__main__':unittest.main()
