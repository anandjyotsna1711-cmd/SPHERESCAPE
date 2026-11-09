
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from scipy.stats import pearsonr, t


# Load PSF data
df = pd.read_csv("data/raw/psf_wavelength_mapping.csv")

required = [
    "detector_x",
    "detector_y",
    "wavelength_um",
    "peak_intensity",
    "central_fraction"
]

if not all(column in df.columns for column in required):
    raise ValueError("Required columns are missing from the CSV.")

df = df[required].dropna().copy()

x = df["detector_x"].to_numpy()
y = df["detector_y"].to_numpy()

# Normalize detector coordinates
x = (x - x.mean()) / x.std()
y = (y - y.mean()) / y.std()


# Build different spatial models
spatial_models = {
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


pairs = [
    ("wavelength_um", "peak_intensity"),
    ("wavelength_um", "central_fraction"),
    ("peak_intensity", "central_fraction")
]


def remove_spatial_effect(values, spatial):
    coefficients = np.linalg.lstsq(
        spatial, values, rcond=None
    )[0]

    predicted = spatial @ coefficients
    residuals = values - predicted

    return residuals


def calculate_partial_correlation(a, b, spatial):
    residual_a = remove_spatial_effect(a, spatial)
    residual_b = remove_spatial_effect(b, spatial)

    correlation, _ = pearsonr(residual_a, residual_b)

    # Degrees of freedom after controlling for spatial terms
    rank = np.linalg.matrix_rank(spatial)
    degrees_freedom = len(a) - rank - 1

    if degrees_freedom <= 0:
        raise ValueError("Insufficient degrees of freedom.")

    t_value = correlation * np.sqrt(
        degrees_freedom / (1 - correlation**2)
    )

    p_value = 2 * t.sf(abs(t_value), degrees_freedom)

    return (
        correlation,
        p_value,
        degrees_freedom,
        residual_a,
        residual_b
    )


# Store all results
results = []

print("\nPSF SPATIAL ROBUSTNESS ANALYSIS\n")

for model_name, spatial in spatial_models.items():

    print(f"\n{model_name.upper()} SPATIAL MODEL")
    print("-" * 55)

    for a, b in pairs:

        result = calculate_partial_correlation(
            df[a].to_numpy(),
            df[b].to_numpy(),
            spatial
        )

        correlation, p_value, dfree, _, _ = result

        results.append({
            "spatial_model": model_name,
            "relationship": f"{a} vs {b}",
            "partial_correlation": correlation,
            "p_value": p_value,
            "degrees_freedom": dfree
        })

        print(f"\n{a} vs {b}")
        print(f"Partial correlation: {correlation:.4f}")
        print(f"Degrees of freedom: {dfree}")
        print(f"P-value: {p_value:.8g}")

# Bonferroni correction within each spatial model
results_df = pd.DataFrame(results)

results_df["bonferroni_p"] = (
    results_df.groupby("spatial_model")["p_value"]
    .transform(lambda values: np.minimum(values * 3, 1.0))
)

results_df.to_csv(
    "data/raw/psf_robustness_results.csv",
    index=False
)


# Create residual plots using the quadratic model
quadratic = spatial_models["Quadratic"]

fig, axes = plt.subplots(1, 3, figsize=(17, 5))

for ax, (a, b) in zip(axes, pairs):

    _, _, _, residual_a, residual_b = (
        calculate_partial_correlation(
            df[a].to_numpy(),
            df[b].to_numpy(),
            quadratic
        )
    )

    correlation, _ = pearsonr(residual_a, residual_b)

    ax.scatter(
        residual_a,
        residual_b,
        alpha=0.7
    )

    slope, intercept = np.polyfit(
        residual_a,
        residual_b,
        1
    )

    line_x = np.linspace(
        residual_a.min(),
        residual_a.max(),
        100
    )

    ax.plot(
        line_x,
        slope * line_x + intercept
    )

    ax.set_title(
        f"{a} vs {b}\nr = {correlation:.4f}"
    )

    ax.set_xlabel(f"{a} residuals")
    ax.set_ylabel(f"{b} residuals")
    ax.grid(alpha=0.25)

plt.suptitle(
    "SPHEREx PSF: Spatial-Controlled Relationships",
    fontsize=14
)

plt.tight_layout()

plt.savefig(
    "data/raw/psf_residual_relationships.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("\n\nBONFERRONI-CORRECTED RESULTS")
print("=" * 65)

print(
    results_df[
        [
            "spatial_model",
            "relationship",
            "partial_correlation",
            "p_value",
            "bonferroni_p",
            "degrees_freedom"
        ]
    ].to_string(index=False)
)

print("\nFiles generated:")
print("1. data/raw/psf_robustness_results.csv")
print("2. data/raw/psf_residual_relationships.png")

print("\nValidation analysis completed!")
