import json
import tempfile
import unittest
from pathlib import Path

from timbrelio.report import result_tables


class ReportTests(unittest.TestCase):
    def test_paired_denominator_and_id_alignment(self):
        with tempfile.TemporaryDirectory() as tmp:
            folders = []
            for name, scores in [("Conventional", "001,1\n002,0\n"), ("OpenL3", "001,0.4\n")]:
                folder = Path(tmp) / name
                (folder / "baseline").mkdir(parents=True)
                (folder / "study.json").write_text(json.dumps({"representation": name, "configurations": {"baseline": {"seed": 42}}}))
                (folder / "baseline/pca_kmeans.csv").write_text("track_id,genre\n001,jazz\n002,rock\n")
                (folder / "retrieval_by_seed.csv").write_text("track_id,precision_at_5\n" + scores)
                (folder / "projection_metrics.csv").write_text("run,method,trustworthiness,neighbor_overlap,runtime_seconds\nbaseline,pca,0.9,0.6,0.01\n")
                (folder / "cluster_metrics.csv").write_text("run,method,silhouette,adjusted_rand_index,noise_rate,runtime_seconds\nbaseline,hdbscan,,,1,0.03\n")
                folders.append(folder)
            tex = result_tables(*folders)
            self.assertIn("Conventional & 2 & 1 & 1.000", tex)
            self.assertIn("OpenL3 & 2 & 1 & 0.400", tex)
            self.assertIn("HDBSCAN & -- & -- & 1.000", tex)
            (folders[1] / "baseline/pca_kmeans.csv").write_text("track_id,genre\n001,jazz\n2,rock\n")
            with self.assertRaisesRegex(ValueError, "matching"):
                result_tables(*folders)
