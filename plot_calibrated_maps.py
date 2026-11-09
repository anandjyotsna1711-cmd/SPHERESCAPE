
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("data/raw/psf_calibrated_mapping.csv")

os.makedirs("results/figures", exist_ok=True)

x = df["detector_x"]
y = df["detector_y"]

plots = [
    {
        "column": "calibrated_wavelength_um",
        "title": "Calibrated Wavelength Distribution",
        "label": "Wavelength (µm)",
        "filename": "calibrated_wavelength_map.png"
    },
    {
        "column": "peak_intensity",
        "title": "PSF Peak Intensity Distribution",
        "label": "Peak Intensity",
        "filename": "psf_peak_intensity_map.png"
    },
    {
        "column": "central_fraction",
        "title": "PSF Central Energy Fraction",
        "label": "Energy Fraction in Central 21x21 Region",
        "filename": "psf_central_fraction_map.png"
    }
]

for plot in plots:
    fig, ax = plt.subplots(figsize=(9, 7))

    values = df[plot["column"]]

    scatter = ax.scatter(
        x, y,
        c=values,
        cmap="viridis",
        s=180,
        marker="s",
        edgecolors="black",
        linewidths=0.3
    )

    fig.colorbar(scatter, ax=ax, label=plot["label"])

    ax.set_title(plot["title"], fontsize=15)
    ax.set_xlabel("Detector X Coordinate")
    ax.set_ylabel("Detector Y Coordinate")
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)

    plt.tight_layout()

    path = os.path.join("results/figures", plot["filename"])
    plt.savefig(path, dpi=300)
    plt.close()

    print("Saved:", path)

print("\nAll three calibrated maps generated successfully!")
