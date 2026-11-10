
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from astropy.io import fits
from scipy.spatial import cKDTree

FITS_FILE = "data/raw/spherex_observation_may2026.fits"
CSV_FILE = "data/raw/source_candidates.csv"

df = pd.read_csv(CSV_FILE)
top = df.nlargest(12, "snr")

with fits.open(FITS_FILE) as hdul:
    image = hdul["IMAGE"].data.astype(float)

coords = df[["x", "y"]].to_numpy()
tree = cKDTree(coords)

fig, axes = plt.subplots(3, 4, figsize=(17, 13))
axes = axes.flatten()

half = 15

for ax, (_, source) in zip(axes, top.iterrows()):

    x = int(source["x"])
    y = int(source["y"])

    x1 = max(0, x - half)
    x2 = min(image.shape[1], x + half + 1)
    y1 = max(0, y - half)
    y2 = min(image.shape[0], y + half + 1)

    cutout = image[y1:y2, x1:x2]

    vmin, vmax = np.nanpercentile(cutout, [5, 99.5])

    ax.imshow(
        cutout,
        origin="lower",
        cmap="inferno",
        vmin=vmin,
        vmax=vmax
    )

    nearby = tree.query_ball_point([x, y], r=half)

    nearby_coords = coords[nearby]

    ax.scatter(
        nearby_coords[:, 0] - x1,
        nearby_coords[:, 1] - y1,
        s=20,
        facecolors="none",
        edgecolors="cyan"
    )

    ax.scatter(
        x - x1,
        y - y1,
        marker="x",
        color="lime",
        s=70
    )

    ax.set_title(
        f"SNR: {source['snr']:.1f} | other sources within 15 px: {len(nearby) - 1}",
        fontsize=10
    )

    ax.set_xticks([])
    ax.set_yticks([])

fig.suptitle(
    "SPHERESCAPE: 12 strongest detections (cyan circles: other detected sources)",
    fontsize=16
)

plt.tight_layout()

output = "results/figures/top_candidate_cutouts.png"
plt.savefig(output, dpi=250, bbox_inches="tight")
plt.close()

print("Saved:", output)
print("Candidates inspected:", len(top))
