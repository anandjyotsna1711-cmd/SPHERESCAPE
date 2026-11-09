
import pandas as pd
from scipy.stats import pearsonr, spearmanr

df = pd.read_csv("data/raw/psf_wavelength_mapping.csv")

pairs = [
    ("wavelength_um", "peak_intensity"),
    ("wavelength_um", "central_fraction"),
    ("peak_intensity", "central_fraction")
]

print("\nPSF CORRELATION ANALYSIS\n")

for x, y in pairs:

    pearson, p1 = pearsonr(df[x], df[y])
    spearman, p2 = spearmanr(df[x], df[y])

    print(f"{x} vs {y}")
    print(f"Pearson correlation: {pearson:.4f}")
    print(f"Pearson p-value: {p1:.6f}")
    print(f"Spearman correlation: {spearman:.4f}")
    print(f"Spearman p-value: {p2:.6f}")
    print("-" * 45)
