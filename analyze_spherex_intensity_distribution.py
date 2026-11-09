
from astropy.io import fits
import numpy as np
import matplotlib.pyplot as plt

FILE = "data/raw/spherex_observation_may2026.fits"

# Load observation
with fits.open(FILE) as hdul:
    image = hdul["IMAGE"].data.astype(np.float64)

# Keep only valid pixels
valid_pixels = image[np.isfinite(image)]

# Calculate statistics
print("\n===== SPHEREx SCIENTIFIC DATA ANALYSIS =====")

print("Image dimensions:", image.shape)
print("Valid pixels:", len(valid_pixels))
print("Minimum intensity:", np.min(valid_pixels))
print("Maximum intensity:", np.max(valid_pixels))
print("Mean intensity:", np.mean(valid_pixels))
print("Median intensity:", np.median(valid_pixels))
print("Standard deviation:", np.std(valid_pixels))

print("\n===== INTENSITY PERCENTILES =====")

for p in [1, 5, 25, 50, 75, 95, 99]:
    print(f"{p}th percentile:", np.percentile(valid_pixels, p))

# Plot intensity distribution
plt.figure(figsize=(10, 6))

plt.hist(valid_pixels, bins=150)

plt.title("SPHEREx Pixel Intensity Distribution")
plt.xlabel("Pixel Intensity")
plt.ylabel("Number of Pixels")

plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    "data/raw/spherex_intensity_histogram.png",
    dpi=200
)

plt.show()

print("\nHistogram saved successfully!")
