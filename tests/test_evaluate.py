import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from timbrelio.evaluate import Config, cluster_metrics, load_features, neighbor_indices, neighbor_overlap


class EvaluationTests(unittest.TestCase):
    def test_load_preserves_ids_and_rejects_invalid_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'features.csv'
            path.write_text('track_id,genre,f1,f2\n000001,Rock,1,2\n000002,Jazz,3,4\n')
            metadata, values, names = load_features(path)
            self.assertEqual(metadata.track_id.tolist(), ['000001', '000002'])
            self.assertEqual(names, ['f1', 'f2'])
            self.assertEqual(values.shape, (2, 2))
            path.write_text('track_id,f1,f2\n1,1,2\n1,3,4\n')
            with self.assertRaisesRegex(ValueError, 'unique'):
                load_features(path)
            path.write_text('track_id,f1,f2\n1,1,NaN\n2,3,4\n')
            with self.assertRaisesRegex(ValueError, 'finite'):
                load_features(path)

    def test_neighbors_exclude_self_with_duplicates(self):
        data = np.array([[1., 0.], [1., 0.], [0., 1.], [-1., 0.]])
        indices = neighbor_indices(data, 2, 'euclidean')
        self.assertTrue(all(i not in row for i, row in enumerate(indices)))
        unit = np.array([[1., 0.], [.98, .2], [0., 1.], [-.2, .98]])
        unit /= np.linalg.norm(unit, axis=1, keepdims=True)
        self.assertEqual(neighbor_overlap(unit, unit, 1), 1.0)

    def test_cluster_metrics_handle_noise_and_missing_genres(self):
        values = np.array([[0, 0], [0, .1], [4, 4], [4, 4.1], [20, 20]])
        metrics = cluster_metrics(values, [0, 0, 1, 1, -1], ['a', 'a', 'b', 'b', None])
        self.assertGreater(metrics['silhouette'], .9)
        self.assertAlmostEqual(metrics['noise_rate'], .2)
        self.assertEqual(metrics['adjusted_rand_index'], 1)
        self.assertEqual(metrics['ari_n_labeled'], 4)
        noise_only = cluster_metrics(values, [-1] * 5)
        self.assertIsNone(noise_only['silhouette'])
        self.assertIsNone(noise_only['adjusted_rand_index'])

    def test_pca_is_repeatable(self):
        values = StandardScaler().fit_transform(np.random.RandomState(42).normal(size=(40, 5)))
        np.testing.assert_allclose(PCA(2, svd_solver='full').fit_transform(values),
                                   PCA(2, svd_solver='full').fit_transform(values))


if __name__ == '__main__':
    unittest.main()
