
import numpy as np
import pandas as pd
from scipy import stats

INPUT = "data/raw/psf_calibrated_mapping.csv"
OUTPUT = "data/raw/calibrated_psf_results.csv"

df = pd.read_csv(INPUT)

x = (df["detector_x"].values - 1020) / 1020
y = (df["detector_y"].values - 1020) / 1020

variables = {
    "wavelength": df["calibrated_wavelength_um"].values,
    "peak_intensity": df["peak_intensity"].values,
    "central_fraction": df["central_fraction"].values
}

pairs = [
    ("wavelength", "peak_intensity"),
    ("wavelength", "central_fraction"),
    ("peak_intensity", "central_fraction")
]

def spatial_design(degree):
    columns = [np.ones(len(x)), x, y]

    if degree >= 2:
        columns.extend([x**2, y**2, x*y])

    if degree >= 3:
        columns.extend([x**3, y**3, x**2*y, x*y**2])

    return np.column_stack(columns)

def residualize(values, design):
    coefficients = np.linalg.lstsq(
        design, values, rcond=None
    )[0]
    return values - design @ coefficients

def correlation_pvalue(r, dfree):
    r = np.clip(r, -0.999999999, 0.999999999)
    t_value = r * np.sqrt(dfree / (1 - r**2))
    return 2 * stats.t.sf(abs(t_value), dfree)

results = []

print("========== RAW CORRELATIONS ==========")

for a, b in pairs:
    pearson = stats.pearsonr(variables[a], variables[b])
    spearman = stats.spearmanr(variables[a], variables[b])

    print(f"\n{a} vs {b}")
    print(f"Pearson r: {pearson.statistic:+.6f}")
    print(f"Pearson p: {pearson.pvalue:.8g}")
    print(f"Spearman rho: {spearman.statistic:+.6f}")
    print(f"Spearman p: {spearman.pvalue:.8g}")

    results.append({
        "model": "raw",
        "relationship": f"{a} vs {b}",
        "correlation": pearson.statistic,
        "p_value": pearson.pvalue,
        "bonferroni_p": min(pearson.pvalue * 3, 1.0)
    })

print("\n========== SPATIAL-ADJUSTED CORRELATIONS ==========")

for degree in [1, 2, 3]:
    design = spatial_design(degree)
    rank = np.linalg.matrix_rank(design)
    dfree = len(x) - rank - 1

    print(f"\n--- Polynomial degree {degree} ---")

    for a, b in pairs:
        ra = residualize(variables[a], design)
        rb = residualize(variables[b], design)

        r = np.corrcoef(ra, rb)[0, 1]
        p = correlation_pvalue(r, dfree)
        adjusted_p = min(p * 3, 1.0)

        print(f"\n{a} vs {b}")
        print(f"Partial correlation: {r:+.6f}")
        print(f"p-value: {p:.8g}")
        print(f"Bonferroni p-value: {adjusted_p:.8g}")

        results.append({
            "model": f"degree_{degree}",
            "relationship": f"{a} vs {b}",
            "correlation": r,
            "p_value": p,
            "bonferroni_p": adjusted_p
        })

pd.DataFrame(results).to_csv(OUTPUT, index=False)

print("\nSaved results to:", OUTPUT)
