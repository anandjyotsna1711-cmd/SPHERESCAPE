
import pandas as pd
import numpy as np

from scipy.spatial import cKDTree


# Load data
df = pd.read_csv("data/raw/psf_wavelength_mapping.csv")

columns = [
    "detector_x",
    "detector_y",
    "wavelength_um",
    "peak_intensity",
    "central_fraction"
]

df = df[columns].dropna().copy()

coordinates = df[["detector_x", "detector_y"]].to_numpy()

x = coordinates[:, 0]
y = coordinates[:, 1]

x = (x - x.mean()) / x.std()
y = (y - y.mean()) / y.std()


# Define spatial models
models = {
    "Linear": np.column_stack([
        np.ones(len(df)),
        x, y
    ]),

    "Quadratic": np.column_stack([
        np.ones(len(df)),
        x, y,
        x**2, y**2, x*y
    ]),

    "Cubic": np.column_stack([
        np.ones(len(df)),
        x, y,
        x**2, y**2, x*y,
        x**3, y**3,
        x**2*y, x*y**2
    ])
}


# Build a symmetric 8-nearest-neighbour spatial matrix
tree = cKDTree(coordinates)

_, neighbours = tree.query(coordinates, k=9)

n = len(df)

weights = np.zeros((n, n))

for i in range(n):
    for j in neighbours[i, 1:]:
        weights[i, j] = 1
        weights[j, i] = 1

weight_sum = weights.sum()


def morans_i(values):
    values = np.asarray(values, dtype=float)
    centered = values - values.mean()

    denominator = np.sum(centered**2)

    if denominator == 0:
        return np.nan

    numerator = centered @ weights @ centered

    return (n / weight_sum) * (numerator / denominator)


def permutation_test(values, permutations=9999):

    observed = morans_i(values)

    expected = -1 / (n - 1)

    rng = np.random.default_rng(42)

    simulated = np.empty(permutations)

    for i in range(permutations):
        shuffled = rng.permutation(values)
        simulated[i] = morans_i(shuffled)

    extreme = np.sum(
        np.abs(simulated - expected)
        >= abs(observed - expected)
    )

    p_value = (extreme + 1) / (permutations + 1)

    return observed, expected, p_value


# Variables to investigate
variables = [
    "wavelength_um",
    "peak_intensity",
    "central_fraction"
]


print("\nSPHERESCAPE SPATIAL RESIDUAL DIAGNOSTICS")
print("=" * 65)

results = []

for model_name, spatial in models.items():

    print(f"\n{model_name.upper()} MODEL")
    print("-" * 65)

    for variable in variables:

        values = df[variable].to_numpy()

        coefficients = np.linalg.lstsq(
            spatial, values, rcond=None
        )[0]

        predicted = spatial @ coefficients
        residuals = values - predicted

        observed, expected, p_value = permutation_test(
            residuals
        )

        results.append({
            "model": model_name,
            "variable": variable,
            "morans_I": observed,
            "expected_I": expected,
            "permutation_p": p_value
        })

        print(f"\nVariable: {variable}")
        print(f"Moran's I: {observed:.5f}")
        print(f"Expected I: {expected:.5f}")
        print(f"Permutation p-value: {p_value:.5f}")

        if p_value < 0.05:
            print("Result: Significant spatial autocorrelation")
        else:
            print("Result: No significant spatial autocorrelation detected")


# Save results
results_df = pd.DataFrame(results)

results_df.to_csv(
    "data/raw/psf_spatial_autocorrelation.csv",
    index=False
)

print("\n" + "=" * 65)
print("Saved: data/raw/psf_spatial_autocorrelation.csv")
print("Spatial residual diagnostics completed!")
