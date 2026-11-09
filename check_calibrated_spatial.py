
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

df = pd.read_csv("data/raw/psf_calibrated_mapping.csv")

x = (df["detector_x"].values - 1020) / 1020
y = (df["detector_y"].values - 1020) / 1020

variables = {
    "wavelength": df["calibrated_wavelength_um"].values,
    "peak_intensity": df["peak_intensity"].values,
    "central_fraction": df["central_fraction"].values
}

def spatial_design(degree):
    columns = [np.ones(len(x)), x, y]

    if degree >= 2:
        columns.extend([x**2, y**2, x*y])

    if degree >= 3:
        columns.extend([x**3, y**3, x**2*y, x*y**2])

    return np.column_stack(columns)

def residualize(values, design):
    coefficients = np.linalg.lstsq(design, values, rcond=None)[0]
    return values - design @ coefficients

def morans_i(values, neighbors=8):
    tree = cKDTree(np.column_stack([x, y]))
    distances, indices = tree.query(
        np.column_stack([x, y]), k=neighbors + 1
    )

    indices = indices[:, 1:]

    z = values - np.mean(values)
    denominator = np.sum(z**2)

    numerator = np.sum(z[:, None] * z[indices])

    n = len(z)
    return (n / (n * neighbors)) * (numerator / denominator)

print("CALIBRATED SPATIAL AUTOCORRELATION")

for degree in [1, 2, 3]:
    design = spatial_design(degree)

    print(f"\nPolynomial degree {degree}")

    for name, values in variables.items():
        residuals = residualize(values, design)
        print(f"{name}: Moran's I = {morans_i(residuals):.6f}")

