
from astropy.io import fits
import numpy as np

FILE = "data/raw/spherex_observation_may2026.fits"

with fits.open(FILE) as hdul:
    image = hdul["IMAGE"].data.astype(np.float64)

valid = np.isfinite(image)

# Use the 99th percentile as a brightness threshold
threshold = np.percentile(image[valid], 99)

# Identify pixels above the threshold
bright_mask = valid & (image > threshold)

y, x = np.where(bright_mask)

print("\n===== BRIGHT REGION ANALYSIS =====")
print("Brightness threshold:", threshold)
print("Bright pixels detected:", len(x))

print("\n===== BRIGHTEST PIXELS =====")

flat_indices = np.argsort(image[valid])[-10:]
valid_y, valid_x = np.where(valid)

for index in flat_indices[::-1]:
    row = valid_y[index]
    col = valid_x[index]

    print(
        f"X: {col}, Y: {row}, "
        f"Intensity: {image[row, col]:.4f}"
    )

print("\n===== ANALYSIS COMPLETE =====")
