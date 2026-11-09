
from astropy.io import fits
import numpy as np

FILE = "data/raw/spherex_observation_may2026.fits"

with fits.open(FILE) as hdul:
    flags = hdul["FLAGS"].data
    image = hdul["IMAGE"].data

print("\n===== SPHEREx FLAG ANALYSIS =====")

print("Flag image dimensions:", flags.shape)
print("Flag data type:", flags.dtype)

values, counts = np.unique(flags, return_counts=True)

print("\n===== FLAG VALUE DISTRIBUTION =====")

for value, count in zip(values, counts):
    print(f"Flag value {value}: {count} pixels")

print("\n===== BRIGHT PIXEL QUALITY =====")

threshold = np.nanpercentile(image, 99)
bright = np.isfinite(image) & (image > threshold)

bright_flags, bright_counts = np.unique(
    flags[bright],
    return_counts=True
)

for value, count in zip(bright_flags, bright_counts):
    print(f"Flag value {value}: {count} bright pixels")

print("\n===== FLAGS HEADER =====")

with fits.open(FILE) as hdul:
    print(repr(hdul["FLAGS"].header))

print("\nFLAG ANALYSIS COMPLETE!")
