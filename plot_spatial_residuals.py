
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

df = pd.read_csv("data/raw/psf_wavelength_mapping.csv")

variables = [
    "wavelength_um",
    "peak_intensity",
    "central_fraction"
]

x = df["detector_x"].to_numpy()
y = df["detector_y"].to_numpy()

x = (x - x.mean()) / x.std()
y = (y - y.mean()) / y.std()

models = {
    "Linear": np.column_stack([
        np.ones(len(df)), x, y
    ]),

    "Quadratic": np.column_stack([
        np.ones(len(df)),
        x, y, x**2, y**2, x*y
    ]),

    "Cubic": np.column_stack([
        np.ones(len(df)),
        x, y,
        x**2, y**2, x*y,
        x**3, y**3,
        x**2*y, x*y**2
    ])
}

output_dir = Path("data/raw/residual_maps")
output_dir.mkdir(parents=True, exist_ok=True)

for variable in variables:

    values = df[variable].to_numpy()

    for model_name, design in models.items():

        coefficients = np.linalg.lstsq(
            design, values, rcond=None
        )[0]

        residuals = values - design @ coefficients

        fig, ax = plt.subplots(figsize=(9, 7))

        scatter = ax.scatter(
            df["detector_x"],
            df["detector_y"],
            c=residuals,
            cmap="coolwarm",
            s=90,
            edgecolors="black",
            linewidths=0.4
        )

        ax.set_title(
            f"{variable.replace('_', ' ').title()}\n"
            f"{model_name} Spatial Residuals",
            fontsize=15,
            pad=15
        )

        ax.set_xlabel("Detector X", fontsize=12)
        ax.set_ylabel("Detector Y", fontsize=12)

        ax.tick_params(labelsize=10)
        ax.set_aspect("equal")

        colorbar = fig.colorbar(scatter, ax=ax)
        colorbar.set_label("Residual value", fontsize=11)

        fig.tight_layout()

        filename = f"{variable}_{model_name.lower()}.png"

        fig.savefig(
            output_dir / filename,
            dpi=300,
            bbox_inches="tight"
        )

        plt.close(fig)

        print(f"Saved: {filename}")

print("\nAll 9 individual residual maps generated!")
print(f"Location: {output_dir}")
