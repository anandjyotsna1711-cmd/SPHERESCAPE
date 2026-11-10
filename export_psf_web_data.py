
"""
Bundle the PSF analysis into a small JSON file for the website.

Run after map_psf_calibrated.py and analyze_calibrated_psf.py.
Writes results/psf_zones.json (committed, ~20 KB), which backend/app.py
serves at /api/science.
"""

import json

import pandas as pd


ZONES = "data/raw/psf_calibrated_mapping.csv"
CORRELATIONS = "data/raw/calibrated_psf_results.csv"
OUTPUT = "results/psf_zones.json"

zones = pd.read_csv(ZONES)
correlations = pd.read_csv(CORRELATIONS)

records = [
    {
        "zone": int(row.psf_zone),
        "x": round(float(row.detector_x), 1),
        "y": round(float(row.detector_y), 1),
        "wavelength_um": round(float(row.calibrated_wavelength_um), 4),
        "bandwidth_um": round(float(row.calibrated_bandwidth_um), 4),
        "peak_intensity": round(float(row.peak_intensity), 6),
        "central_fraction": round(float(row.central_fraction), 5)
    }
    for row in zones.itertuples()
]

model_names = {
    "raw": "no correction",
    "degree_1": "straight-line position correction",
    "degree_2": "curved (quadratic) position correction",
    "degree_3": "most flexible (cubic) position correction"
}

relationships = {}

for row in correlations.itertuples():
    relationships.setdefault(row.relationship, []).append({
        "model": model_names.get(row.model, row.model),
        "correlation": round(float(row.correlation), 3),
        "bonferroni_p": float(row.bonferroni_p)
    })

with open(OUTPUT, "w") as file:
    json.dump({
        "detector": 2,
        "observation": "2026W20_2A_0191_4",
        "grid": 11,
        "zones": records,
        "relationships": relationships
    }, file, indent=1)

print("Saved:", OUTPUT, "with", len(records), "zones")
