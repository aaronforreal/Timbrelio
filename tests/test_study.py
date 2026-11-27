import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from timbrelio.nick_features import convert
from timbrelio.study import retrieval, study
from timbrelio.usability import summarize


class StudyTests(unittest.TestCase):
    def test_converter(self):
        row = {"track id": "000002", "genres": ["Hip-Hop"]}
        for feat, size in [("mfcc", 20), ("centroid", 1), ("zcr", 1), ("rms", 1)]:
            for stat in ("mean", "std"):
                row[f"{feat}_{stat}"] = [0.] * size
        converted = convert([row])
        self.assertEqual(converted.shape, (1, 48))
        self.assertEqual(converted.track_id[0], "000002")
        self.assertNotIn("genre", converted)
        with self.assertRaises(ValueError):
            convert([row, row])

    def test_ranked_ties_do_not_include_seed_and_missing_labels_are_excluded(self):
        ids = ["06", "05", "04", "03", "02", "01"]
        meta = pd.DataFrame({"track_id": ids, "genre": ["a"] * 5 + ["b"]})
        raw = np.array([[1, 1]] * 3 + [[0, 0]] * 3)
        neighbours, scores = retrieval(meta, raw, "Conventional")
        first = neighbours.iloc[:5]
        self.assertEqual(first.neighbour_track_id.tolist(), ["04", "05", "01", "02", "03"])
        self.assertEqual(first["rank"].tolist(), list(range(1, 6)))
        self.assertAlmostEqual(scores.precision_at_5.mean(), 2/3)
        meta.loc[0, "genre"] = None
        self.assertTrue(retrieval(meta, raw, "OpenL3")[1].empty)

    def test_task_summary(self):
        rows = [dict(participant=str(i), task=t, completed="yes" if i else "no", seconds=str(i))
                for i in range(4) for t in ("filter", "listen", "projection")]
        self.assertEqual(list(summarize(rows))[0], ("filter", 4, 3, 2))
        with self.assertRaises(ValueError):
            list(summarize(rows[:-1]))
        with self.assertRaises(ValueError):
            list(summarize(rows + rows[:1]))

    @unittest.skipUnless(importlib.util.find_spec("umap") and importlib.util.find_spec("hdbscan"),
                         "requires analysis extras")
    def test_complete_study(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = pd.DataFrame(np.random.default_rng(42).normal(size=(40, 6)))
            data["track_id"] = [f"{i:06}" for i in range(40)]
            data.to_csv(root / "features.csv", index=False)
            out = root / "out"
            study(root / "features.csv", out, "OpenL3", 42)
            summary = json.loads((out / "study.json").read_text())
            self.assertIsNone(summary["precision_at_5"])
            self.assertEqual(len(summary["configurations"]), 5)
            self.assertEqual(len(pd.read_csv(out / "projection_metrics.csv")), 10)
            self.assertEqual(len(pd.read_csv(out / "cluster_metrics.csv")), 10)
            self.assertEqual(len(pd.read_csv(out / "neighbours.csv")), 200)
