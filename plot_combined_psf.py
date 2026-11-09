
import os
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/raw/psf_calibrated_mapping.csv")

os.makedirs("results/figures", exist_ok=True)

x = df["detector_x"]
y = df["detector_y"]

plots = [
    ("calibrated_wavelength_um",
     "Calibrated Wavelength",
     "Wavelength (µm)"),

    ("peak_intensity",
     "PSF Peak Intensity",
     "Peak Intensity"),

    ("central_fraction",
     "PSF Central Energy Fraction",
     "Central 21×21 Energy Fraction")
]

fig, axes = plt.subplots(1, 3, figsize=(19, 7))

for ax, (column, title, label) in zip(axes, plots):

    scatter = ax.scatter(
        x,
        y,
        c=df[column],
        cmap="viridis",
        s=150,
        marker="s",
        edgecolors="black",
        linewidths=0.35
    )

    fig.colorbar(scatter, ax=ax, shrink=0.78, label=label)

    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel("Detector X")
    ax.set_ylabel("Detector Y")
    ax.invert_yaxis()
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)

fig.suptitle(
    "SPHERESCAPE: Spatial Variation of PSF Properties",
    fontsize=17,
    fontweight="bold"
)

fig.text(
    0.5,
    0.025,
    "Measurements sampled at 121 PSF zone centres | Detector 2",
    ha="center",
    fontsize=10
)

plt.tight_layout(rect=[0, 0.06, 1, 0.92])

output = "results/figures/combined_psf_analysis.png"

plt.savefig(output, dpi=300, bbox_inches="tight")
plt.close()

print("Combined scientific figure saved:", output)
print("PSF zones included:", len(df))
print("Figure resolution: 300 DPI")
