"""End-to-end check with synthetic data; no conclusions about FMA are implied."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from timbrelio.evaluate import Config, run_experiment
from timbrelio.ui.data import read_coordinates


@unittest.skipUnless(importlib.util.find_spec('umap') and importlib.util.find_spec('hdbscan'),
                     'UMAP and HDBSCAN need the analysis dependencies')
class IntegrationTests(unittest.TestCase):
    def test_full_pipeline_repeatable_and_browser_compatible(self):
        rng = np.random.RandomState(123)
        labels = np.repeat(np.arange(3), 20)
        centers = rng.normal(size=(3, 6)) * 4
        data = pd.DataFrame(centers[labels] + rng.normal(size=(60, 6)),
                            columns=[f'f{i}' for i in range(6)])
        ids = [f'{i:06}' for i in range(60)]
        data.insert(0, 'genre', [f'genre_{i}' for i in labels])
        data.insert(0, 'track_id', ids)
        config = Config(clusters=3, min_cluster_size=5, min_samples=3)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'input.csv'
            data.to_csv(path, index=False)
            first = run_experiment(path, root / 'first', config)
            second = run_experiment(path, root / 'second', config)
            self.assertEqual(first['track_count'], 60)
            for proj in ('pca', 'umap'):
                for cluster in ('kmeans', 'hdbscan'):
                    filename = f'{proj}_{cluster}.csv'
                    a = read_coordinates(root / 'first' / filename)
                    b = read_coordinates(root / 'second' / filename)
                    self.assertEqual(a.track_id.tolist(), ids)
                    np.testing.assert_allclose(a[['x', 'y']], b[['x', 'y']], rtol=1e-5, atol=1e-5)
                    self.assertEqual(a.cluster.tolist(), b.cluster.tolist())
            with (root / 'first' / 'metrics.json').open() as f:
                saved = json.load(f)
            for metric in saved['projection_metrics'].values():
                self.assertTrue(0 <= metric['trustworthiness'] <= 1)
                self.assertTrue(0 <= metric['neighbor_overlap'] <= 1)
                self.assertGreaterEqual(metric['runtime_seconds'], 0)
            for metric in saved['cluster_metrics'].values():
                self.assertTrue(0 <= metric['noise_rate'] <= 1)
                self.assertIsNotNone(metric['adjusted_rand_index'])


if __name__ == '__main__':
    unittest.main()
