"""Create fake features to check the analysis workflow; this is not FMA data."""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.RandomState(42)
labels = np.repeat(np.arange(4), 20)
centers = rng.normal(size=(4, 6)) * 3
features = centers[labels] + rng.normal(size=(len(labels), 6))
data = pd.DataFrame(features, columns=[f'feature_{i}' for i in range(6)])
data.insert(0, 'genre', [f'synthetic_{i}' for i in labels])
data.insert(0, 'track_id', [f'{i:06d}' for i in range(len(labels))])
path = Path('synthetic_features.csv')
data.to_csv(path, index=False)
print(f'Created {path}; synthetic data only')
