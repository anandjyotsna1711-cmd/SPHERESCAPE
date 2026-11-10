
"""
Export one SPHEREx image for the website's interactive viewer.

Writes two files to results/viewer/ (committed, so the viewer works without
the 70 MB FITS file):

- image.i16.gz  every pixel, compressed (~4 MB)
- meta.json     image size, how to decode the pixels, display defaults,
                coarse RA/Dec and wavelength grids for hover readouts,
                and the strongest detected sources

Encoding: q = round(asinh(value / SCALE) / STEP) as little-endian int16
(-32768 = no data), byte-shuffled (all low bytes, then all high bytes)
and gzipped. Decode with value = SCALE * sinh(q * STEP). The rounding
error is about 0.004 MJy/sr on the sky background (the noise is ~0.026)
and under 0.5% on anything brighter than 1 MJy/sr.

Run after detect_sources.py (for the source overlay). Uses the calibration
file from download_spectral_wcs.py for wavelengths if present.
"""

import gzip
import json
import os

import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.wcs import WCS


FITS_FILE = "data/raw/spherex_observation_may2026.fits"
CALIBRATION = "data/raw/spectral_wcs_D2.fits"
CANDIDATES = "data/raw/source_candidates.csv"
OUTPUT_DIR = "results/viewer"

SCALE = 0.05      # MJy/sr: where the asinh curve switches from linear to log
STEP = 0.01       # quantisation step in asinh space
NO_DATA = -32768
GRID_NODES = 31   # RA/Dec and wavelength sampled on a 31 x 31 grid
TOP_SOURCES = 2000


os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Loading SPHEREx image...", flush=True)

with fits.open(FITS_FILE) as hdul:
    header = hdul["IMAGE"].header
    image = hdul["IMAGE"].data.astype(np.float64)
    wcs = WCS(header).celestial

    wave_table = hdul["WCS-WAVE"].data

height, width = image.shape


# ==========================================
# 1. PIXELS
# ==========================================

print("Encoding pixels...", flush=True)

quantised = np.round(np.arcsinh(image / SCALE) / STEP)
quantised = np.where(np.isfinite(quantised), quantised, NO_DATA).astype("<i2")

as_bytes = np.frombuffer(quantised.tobytes(), dtype=np.uint8).reshape(-1, 2)
shuffled = np.concatenate([as_bytes[:, 0], as_bytes[:, 1]]).tobytes()

with open(os.path.join(OUTPUT_DIR, "image.i16.gz"), "wb") as file:
    file.write(gzip.compress(shuffled, 9))

finite = image[np.isfinite(image)]
percentiles = {
    str(p): float(np.percentile(finite, p))
    for p in [0.5, 1, 50, 99, 99.5, 99.9]
}


# ==========================================
# 2. RA/DEC AND WAVELENGTH GRIDS
# ==========================================

print("Sampling coordinate grids...", flush=True)

nodes_x = np.linspace(0, width - 1, GRID_NODES)
nodes_y = np.linspace(0, height - 1, GRID_NODES)
grid_x, grid_y = np.meshgrid(nodes_x, nodes_y)

sky = wcs.pixel_to_world(grid_x, grid_y)
centre = wcs.pixel_to_world((width - 1) / 2, (height - 1) / 2)

# Keep RA continuous around the centre so interpolation never jumps 360 deg.
ra = sky.ra.deg
ra = centre.ra.deg + ((ra - centre.ra.deg + 180) % 360 - 180)
dec = sky.dec.deg

if os.path.exists(CALIBRATION):
    with fits.open(CALIBRATION) as cal:
        cwave = np.asarray(cal["CWAVE"].data, dtype=float)
    wavelength = cwave[
        np.rint(grid_y).astype(int),
        np.rint(grid_x).astype(int)
    ]
    wavelength_source = "spectral WCS calibration (CWAVE)"
else:
    # Fall back to the coarse lookup table inside the image file.
    from scipy.interpolate import RegularGridInterpolator

    table_x = np.asarray(wave_table["X"][0], dtype=float) - 1
    table_y = np.asarray(wave_table["Y"][0], dtype=float) - 1
    values = np.asarray(wave_table["VALUES"][0], dtype=float)[:, :, 0]
    lookup = RegularGridInterpolator(
        (table_y, table_x), values, bounds_error=False, fill_value=None
    )
    wavelength = lookup(np.column_stack([grid_y.ravel(), grid_x.ravel()])).reshape(grid_x.shape)
    wavelength_source = "WCS-WAVE lookup table"


# ==========================================
# 3. STRONGEST DETECTED SOURCES
# ==========================================

sources = None

if os.path.exists(CANDIDATES):
    top = pd.read_csv(CANDIDATES).nlargest(TOP_SOURCES, "snr")
    sources = {
        "x": top["x"].astype(int).tolist(),
        "y": top["y"].astype(int).tolist(),
        "snr": top["snr"].round(1).tolist()
    }


# ==========================================
# 4. METADATA
# ==========================================

meta = {
    "observation": header.get("OBSID"),
    "date": header.get("DATE-OBS"),
    "detector": header.get("DETECTOR"),
    "unit": header.get("BUNIT", "MJy/sr"),
    "width": width,
    "height": height,
    "encoding": {
        "file": "image.i16.gz",
        "format": "int16 little-endian, byte-shuffled, gzip",
        "row_order": "row 0 is FITS row 0 (bottom of the image)",
        "scale": SCALE,
        "step": STEP,
        "no_data": NO_DATA
    },
    "percentiles": percentiles,
    "grid": {
        "x": np.round(nodes_x, 2).tolist(),
        "y": np.round(nodes_y, 2).tolist(),
        "ra": np.round(ra, 6).tolist(),
        "dec": np.round(dec, 6).tolist(),
        "wavelength_um": np.round(wavelength, 4).tolist(),
        "wavelength_source": wavelength_source
    },
    "sources": sources
}

with open(os.path.join(OUTPUT_DIR, "meta.json"), "w") as file:
    json.dump(meta, file, separators=(",", ":"))

for name in ["image.i16.gz", "meta.json"]:
    size = os.path.getsize(os.path.join(OUTPUT_DIR, name))
    print(f"Saved {OUTPUT_DIR}/{name} ({size / 1e6:.2f} MB)")
