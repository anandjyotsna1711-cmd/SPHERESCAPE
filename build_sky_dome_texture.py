
"""
Build the sky texture for Cosmic Explorer's sky dome.

NASA's SPHEREx all-sky map is published as a Mollweide (oval) projection in
Galactic coordinates: the Galactic centre in the middle, Galactic longitude
increasing to the LEFT. The dome needs a plain RA/Dec map instead, so this
script re-projects it:

    output pixel (RA, Dec) -> Galactic (l, b) -> Mollweide (x, y) -> source pixel

Output: data/processed/sky_dome_spherex.jpg, 4096 x 2048, equirectangular,
RA 0 -> 360 degrees from left to right, Dec +90 at the top.

Orientation check: the Large Magellanic Cloud (RA 80.9, Dec -69.8) and the
Orion Nebula region (RA 83.8, Dec -5.4) should appear at those coordinates.

Image: NASA/JPL-Caltech (SPHEREx all-sky map).
"""

import os
import urllib.request

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from astropy.coordinates import SkyCoord
from scipy.ndimage import map_coordinates


SOURCE_URL = (
    "https://d2pn8kiwq2w21t.cloudfront.net/original_images/"
    "e1a-SPHEREx_all_sky_stars_and_gas-dust.jpg"
)
SOURCE = "data/raw/spherex_all_sky_mollweide.jpg"
OUTPUT = "data/processed/sky_dome_spherex.jpg"

WIDTH, HEIGHT = 4096, 2048
BRIGHTNESS_THRESHOLD = 12     # source pixels darker than this are outside the oval
EDGE_SHRINK = 0.996           # stay just inside the oval's thin border line


# ==========================================
# 1. SOURCE IMAGE AND OVAL GEOMETRY
# ==========================================

if not os.path.exists(SOURCE):
    os.makedirs(os.path.dirname(SOURCE), exist_ok=True)
    print("Downloading the SPHEREx all-sky map...", flush=True)
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "SPHERESCAPE"})
    with urllib.request.urlopen(request, timeout=120) as response, open(SOURCE, "wb") as file:
        file.write(response.read())

source = mpimg.imread(SOURCE)[..., :3].astype(np.float32)
grey = source.mean(axis=2)

rows = np.nonzero((grey > BRIGHTNESS_THRESHOLD).any(axis=1))[0]
cols = np.nonzero((grey > BRIGHTNESS_THRESHOLD).any(axis=0))[0]

centre_x = (cols[0] + cols[-1]) / 2
centre_y = (rows[0] + rows[-1]) / 2
semi_x = (cols[-1] - cols[0]) / 2 * EDGE_SHRINK
semi_y = (rows[-1] - rows[0]) / 2 * EDGE_SHRINK

print(f"Source {source.shape[1]}x{source.shape[0]}, oval centre ({centre_x:.1f}, {centre_y:.1f}), "
      f"semi-axes {semi_x:.1f} x {semi_y:.1f} (ratio {semi_x / semi_y:.3f}, Mollweide = 2)")


# ==========================================
# 2. OUTPUT GRID: RA/DEC -> GALACTIC
# ==========================================

print("Converting coordinates...", flush=True)

ra = (np.arange(WIDTH) + 0.5) / WIDTH * 360.0
dec = 90.0 - (np.arange(HEIGHT) + 0.5) / HEIGHT * 180.0
ra_grid, dec_grid = np.meshgrid(ra, dec)

galactic = SkyCoord(ra=ra_grid.ravel(), dec=dec_grid.ravel(), unit="deg", frame="icrs").galactic
l = np.radians(((galactic.l.deg + 180) % 360) - 180).reshape(HEIGHT, WIDTH)   # -pi..pi
b = np.radians(galactic.b.deg).reshape(HEIGHT, WIDTH)


# ==========================================
# 3. GALACTIC -> MOLLWEIDE -> SOURCE PIXELS
# ==========================================

# Solve 2t + sin(2t) = pi sin(b) for the auxiliary angle t (Newton's method).
theta = b.copy()
target = np.pi * np.sin(b)

for _ in range(30):
    f = 2 * theta + np.sin(2 * theta) - target
    derivative = 2 + 2 * np.cos(2 * theta)
    theta -= np.where(derivative > 1e-9, f / np.maximum(derivative, 1e-9), 0)

x = -(l / np.pi) * np.cos(theta)    # longitude increases to the LEFT
y = np.sin(theta)

source_x = centre_x + x * semi_x
source_y = centre_y - y * semi_y

print("Resampling...", flush=True)

output = np.empty((HEIGHT, WIDTH, 3), dtype=np.float32)
for channel in range(3):
    output[..., channel] = map_coordinates(
        source[..., channel], [source_y, source_x], order=1, mode="nearest"
    )

plt.imsave(OUTPUT, np.clip(output, 0, 255).astype(np.uint8), format="jpg", pil_kwargs={"quality": 88})

print(f"Saved {OUTPUT} ({os.path.getsize(OUTPUT) / 1e6:.2f} MB)")
