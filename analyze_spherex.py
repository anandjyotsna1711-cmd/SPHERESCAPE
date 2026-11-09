
from astropy.io import fits
import numpy as np

file_path = "data/raw/spherex_observation_may2026.fits"

with fits.open(file_path) as hdul:
    image = hdul["IMAGE"].data.astype(np.float64)

pixels = image[np.isfinite(image)]

print("\n========== SPHEREx ANALYSIS ==========")
print("Image dimensions:", image.shape)
print("Valid pixels:", len(pixels))
print("Minimum intensity:", np.min(pixels))
print("Maximum intensity:", np.max(pixels))
print("Mean intensity:", np.mean(pixels))
print("Median intensity:", np.median(pixels))
print("Standard deviation:", np.std(pixels))

print("\n========== PERCENTILES ==========")

for p in [1, 5, 25, 50, 75, 95, 99]:
    print(f"{p}%:", np.percentile(pixels, p))

print("\n========== ANALYSIS COMPLETE ==========")
