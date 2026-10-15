"""Physical-distance semantics and exact 3D reconstruction, independent examples."""
import unittest
import numpy as np
from src.analysis.reconcile_installed_centers import projected_distance, free_3d_embeddings, ORDER


class TipDistanceTests(unittest.TestCase):
    def test_depth_projection_and_invalid_distance(self):
        self.assertAlmostEqual(projected_distance(5, 3), 4)
        self.assertAlmostEqual(projected_distance(5, -3), 4)
        self.assertAlmostEqual(projected_distance(5, 0), 5)
        with self.assertRaises(ValueError):
            projected_distance(5, 6)

    def test_recover_unequal_depth_tetrahedron_without_scale_change(self):
        points = np.array([[0., 0., 10.], [2., 80., 12.], [50., 60., 4.], [-52., 19., 2.]])
        D = np.linalg.norm(points[:, None] - points[None, :], axis=2)
        result = free_3d_embeddings(D, points)
        self.assertTrue(result['exact_euclidean_embedding_possible'])
        self.assertEqual(len(result['branches']), 2)
        best = result['branches'][0]
        recovered = np.array([best['hypothetical_installed_tip_centers_mm'][name] for name in ORDER])
        np.testing.assert_allclose(recovered, points, atol=1e-8)
        for branch in result['branches']:
            self.assertAlmostEqual(branch['rotation_determinant'], 1)
            self.assertLess(branch['maximum_pair_residual_mm'], 1e-7)

    def test_inconsistent_distances_are_not_silently_flattened(self):
        D = np.ones((4, 4)) - np.eye(4)
        D[0, 1] = D[1, 0] = 3
        result = free_3d_embeddings(D, np.zeros((4, 3)))
        self.assertFalse(result['exact_euclidean_embedding_possible'])
        self.assertEqual(result['branches'], [])


if __name__ == '__main__':
    unittest.main()
