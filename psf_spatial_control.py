
import pandas as pd
import numpy as np
from scipy.stats import pearsonr

df = pd.read_csv("data/raw/psf_wavelength_mapping.csv")

x = df["detector_x"].to_numpy()
y = df["detector_y"].to_numpy()

# Normalize detector coordinates
x = (x - x.mean()) / x.std()
y = (y - y.mean()) / y.std()

# Model spatial variation
spatial = np.column_stack([
    np.ones(len(df)),
    x, y,
    x**2, y**2,
    x*y
])

def remove_spatial_effect(values):

    coefficients = np.linalg.lstsq(
        spatial, values, rcond=None
    )[0]

    predicted = spatial @ coefficients

    return values - predicted


pairs = [
    ("wavelength_um", "peak_intensity"),
    ("wavelength_um", "central_fraction"),
    ("peak_intensity", "central_fraction")
]

print("\nSPATIAL-CONTROLLED CORRELATION ANALYSIS\n")

for a, b in pairs:

    residual_a = remove_spatial_effect(
        df[a].to_numpy()
    )

    residual_b = remove_spatial_effect(
        df[b].to_numpy()
    )

    correlation, p_value = pearsonr(
        residual_a, residual_b
    )

    print(f"{a} vs {b}")
    print(f"Partial correlation: {correlation:.4f}")
    print(f"P-value: {p_value:.8g}")
    print("-" * 45)

print("\nAnalysis completed!")
