
from pathlib import Path

from astropy.io import fits
from astropy.visualization import ImageNormalize, AsinhStretch, PercentileInterval
import matplotlib.pyplot as plt
import numpy as np

PROJECT_DIR = Path(__file__).resolve().parent.parent

FITS_FILE = PROJECT_DIR / "data" / "raw" / "spherex_observation.fits"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "spherex_first_light.png"

# Automatically create the output folder
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Opening SPHEREx observation...")

with fits.open(FITS_FILE) as hdul:
    image = hdul["IMAGE"].data.astype(float)

print("Image dimensions:", image.shape)

image[~np.isfinite(image)] = np.nan

norm = ImageNormalize(
    image,
    interval=PercentileInterval(99.5),
    stretch=AsinhStretch()
)

fig, ax = plt.subplots(figsize=(10, 10))

display = ax.imshow(
    image,
    cmap="inferno",
    origin="lower",
    norm=norm
)

fig.colorbar(display, ax=ax, label="Signal intensity")

ax.set_title("SPHEREx QR2 - First Observation")
ax.set_xlabel("Pixel X")
ax.set_ylabel("Pixel Y")

fig.tight_layout()

fig.savefig(OUTPUT_FILE, dpi=200)

print("\nIMAGE SUCCESSFULLY SAVED!")
print("Location:", OUTPUT_FILE)

plt.show()
