
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("data/raw/psf_wavelength_mapping.csv")

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

maps = [
    ("wavelength_um", "Wavelength Distribution", "Wavelength (µm)"),
    ("peak_intensity", "PSF Peak Intensity", "Peak Intensity"),
    ("central_fraction", "PSF Central Concentration", "Central Fraction")
]

for ax, (column, title, colorbar_label) in zip(axes, maps):

    grid = df.pivot(
        index="zone_y",
        columns="zone_x",
        values=column
    )

    image = ax.imshow(
        grid.values,
        origin="lower",
        cmap="viridis"
    )

    ax.set_title(title)
    ax.set_xlabel("Detector X Zone")
    ax.set_ylabel("Detector Y Zone")

    plt.colorbar(
        image,
        ax=ax,
        label=colorbar_label
    )

plt.tight_layout()

plt.savefig(
    "data/raw/psf_spatial_maps.png",
    dpi=200,
    bbox_inches="tight"
)

plt.close()

print("Spatial maps generated successfully!")
