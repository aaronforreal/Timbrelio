"""Convert Nick's Track.save JSON export into the analysis feature table."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def convert(records):
    rows = []
    seen = set()
    for record in records:
        track = record["track id"]
        if not isinstance(track, str) or not track.strip() or track.strip() in seen:
            raise ValueError("Expected unique, nonempty string track IDs")
        seen.add(track.strip())
        row = {"track_id": track.strip(), "title": record.get("title")}
        # Nick exports a list of genre tags. The evaluation requires a separate
        # verified FMA top-level genre, so these tags cannot supply its labels.
        for feature, size in (("mfcc", 20), ("centroid", 1), ("zcr", 1), ("rms", 1)):
            for stat in ("mean", "std"):
                key = f"{feature}_{stat}"
                values = np.asarray(record[key], dtype=float)
                if values.shape != (size,) or not np.isfinite(values).all():
                    raise ValueError(f"{track}: expected {size} finite values in {key}")
                row.update({f"{key}_{i}": value for i, value in enumerate(values)})
        rows.append(row)
    if not rows:
        raise ValueError("Empty track export")
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    convert(json.loads(args.source.read_text())).to_csv(args.output, index=False, mode="x")


if __name__ == "__main__":
    main()
