
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree

df = pd.read_csv("data/raw/source_candidates.csv")

print("========== CATALOGUE AUDIT ==========")

print("Total candidates:", len(df))
print("Unique pixel coordinates:",
      df[["x", "y"]].drop_duplicates().shape[0])

print("\n========== SNR DISTRIBUTION ==========")
print(df["snr"].describe())

for threshold in [5, 10, 20, 30, 50, 100]:
    count = (df["snr"] >= threshold).sum()
    print(f"SNR >= {threshold}: {count}")

print("\n========== FLAG ANALYSIS ==========")

print("Flag value frequencies:")
print(df["flags"].value_counts().head(15))

print("\nCandidates with SOURCE flag:",
      ((df["flags"].astype("uint32") & (1 << 21)) != 0).sum())

print("\n========== NEAREST NEIGHBOUR DISTANCE ==========")

coords = df[["x", "y"]].to_numpy()

tree = cKDTree(coords)
distances, indices = tree.query(coords, k=2)

nearest = distances[:, 1]

print(pd.Series(nearest).describe())

for radius in [3, 5, 8, 10]:
    print(
        f"Candidates with another candidate within "
        f"{radius} pixels:",
        np.sum(nearest <= radius)
    )

print("\n========== AUDIT COMPLETE ==========")
