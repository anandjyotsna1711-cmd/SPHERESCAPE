
from astropy.io import fits
from astropy.wcs import WCS
import numpy as np

FILE = "data/raw/spherex_observation_may2026.fits"

with fits.open(FILE) as hdul:
    image = hdul["IMAGE"].data.astype(np.float64)
    header = hdul["IMAGE"].header
    flags = hdul["FLAGS"].data.astype(np.uint32)

# Build celestial coordinate system
wcs = WCS(header).celestial

# Find brightest 10 pixels
valid = np.isfinite(image)

flat_indices = np.argpartition(
    image[valid].ravel(), -10
)[-10:]

valid_y, valid_x = np.where(valid)

# Sort brightest first
flat_indices = flat_indices[
    np.argsort(image[valid].ravel()[flat_indices])[::-1]
]

print("\n===== SPHEREx CELESTIAL COORDINATES =====")

for index in flat_indices:
    y = valid_y[index]
    x = valid_x[index]

    # Convert pixel position to sky position
    sky = wcs.pixel_to_world(x, y)

    print("\nPixel position:")
    print("X:", x, "Y:", y)

    print("Intensity:", image[y, x])

    print("Right Ascension:", sky.ra.deg)
    print("Declination:", sky.dec.deg)

    print("Flag value:", flags[y, x])

print("\n===== COORDINATE CONVERSION COMPLETE =====")
