
"""
SPHERESCAPE source detection.

Finds point sources (stars and galaxies) in one SPHEREx Level 2 image.

Why each step is here (checked against the 2MASS star catalogue with
validate_sources_2mass.py):

1. Mask bad pixels, including TRANSIENT and OUTLIER (cosmic rays, glitches).
2. Subtract the sky background. The image is dominated by zodiacal light
   and faint unresolved stars; without this, almost every pixel is "5 sigma".
3. Measure the noise from the image itself. In crowded fields the real
   pixel-to-pixel scatter is ~5x larger than the VARIANCE layer predicts,
   so a VARIANCE-based 5 sigma cut is really ~1 sigma.
4. Keep local peaks at >= 5 sigma that have at least one neighbouring pixel
   above 2 sigma. Single-pixel spikes match catalogued stars no more often
   than random positions do, so they are noise. (SPHEREx stars are only
   1-2 pixels wide, so we can't demand more than that.)
"""

import csv

import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from scipy.ndimage import label, maximum_filter, median_filter, zoom


FILE = "data/raw/spherex_observation_may2026.fits"
OUTPUT_CSV = "data/raw/source_candidates.csv"
OUTPUT_PNG = "data/raw/source_detection.png"

THRESHOLD = 5.0        # peak significance, in measured-noise sigma
GROW_THRESHOLD = 2.0   # a neighbour must be at least this significant
MIN_PIXELS = 2         # connected pixels above GROW_THRESHOLD
BOX = 34               # background / noise mesh size in pixels (2040 / 34 = 60)


# ==========================================
# 1. LOAD SPHEREx DATA
# ==========================================

print("Loading SPHEREx data...", flush=True)

with fits.open(FILE) as hdul:
    image = hdul["IMAGE"].data.astype(np.float64)
    variance = hdul["VARIANCE"].data.astype(np.float64)
    flags = hdul["FLAGS"].data.astype(np.uint32)
    wcs = WCS(hdul["IMAGE"].header).celestial

print("Data loaded successfully!", flush=True)


# ==========================================
# 2. DEFINE QUALITY FLAGS
# ==========================================

FLAG_BITS = {
    "TRANSIENT": 0,
    "OVERFLOW": 1,
    "SUR_ERROR": 2,
    "NONFUNC": 6,
    "DICHROIC": 7,
    "MISSING_DATA": 9,
    "HOT": 10,
    "COLD": 11,
    "NONLINEAR": 15,
    "PERSIST": 17,
    "OUTLIER": 19,
    "SOURCE": 21,
    "BLOOM": 26,
    "SNOWBALL": 27,
    "HALO": 28
}

BAD_FLAGS = [
    "TRANSIENT",
    "SUR_ERROR",
    "NONFUNC",
    "DICHROIC",
    "MISSING_DATA",
    "HOT",
    "COLD",
    "NONLINEAR",
    "PERSIST",
    "OUTLIER",
    "BLOOM",
    "SNOWBALL",
    "HALO"
]

print("Applying quality masks...", flush=True)

bad_mask = np.zeros(flags.shape, dtype=bool)

for name in BAD_FLAGS:
    bit = FLAG_BITS[name]
    bad_mask |= (flags & np.uint32(1 << bit)) != 0

valid = (
    np.isfinite(image) &
    np.isfinite(variance) &
    (variance > 0) &
    (~bad_mask)
)


# ==========================================
# 3. ESTIMATE BACKGROUND AND NOISE
# ==========================================

def mesh(values, statistic):
    """Apply `statistic` to BOX x BOX blocks, then smooth back to full size."""

    ny, nx = values.shape
    gy, gx = ny // BOX, nx // BOX

    blocks = (
        values[:gy * BOX, :gx * BOX]
        .reshape(gy, BOX, gx, BOX)
        .transpose(0, 2, 1, 3)
        .reshape(gy, gx, -1)
    )

    grid = statistic(blocks)
    grid = np.where(np.isfinite(grid), grid, np.nanmedian(grid))
    grid = median_filter(grid, size=3)

    return zoom(grid, (ny / gy, nx / gx), order=1)


def clipped_median(blocks):
    """Median of each block after removing stars (3-sigma clipping)."""

    blocks = blocks.copy()
    med = np.nanmedian(blocks, axis=2)

    for _ in range(3):
        spread = 1.4826 * np.nanmedian(np.abs(blocks - med[..., None]), axis=2)
        blocks[np.abs(blocks - med[..., None]) > 3 * spread[..., None]] = np.nan
        med = np.nanmedian(blocks, axis=2)

    return med


def robust_sigma(blocks):
    """Noise of each block from the median absolute deviation."""

    med = np.nanmedian(blocks, axis=2)
    return 1.4826 * np.nanmedian(np.abs(blocks - med[..., None]), axis=2)


print("Estimating sky background...", flush=True)

masked_image = np.where(valid, image, np.nan)
background = mesh(masked_image, clipped_median)
residual = masked_image - background

print("Measuring noise from the image...", flush=True)

measured_noise = mesh(residual, robust_sigma)
noise = np.maximum(np.sqrt(np.where(valid, variance, np.nan)), measured_noise)

snr = residual / noise

print(
    "Median VARIANCE noise:", round(float(np.nanmedian(np.sqrt(variance[valid]))), 4),
    "| median measured noise:", round(float(np.nanmedian(measured_noise)), 4),
    flush=True
)


# ==========================================
# 4. DETECT PEAKS
# ==========================================

print("Detecting candidate peaks...", flush=True)

safe_snr = np.where(valid, snr, -np.inf)
local_max = maximum_filter(safe_snr, size=3)

peak_mask = valid & (snr >= THRESHOLD) & (snr == local_max)

# Connected regions of significant pixels; drop peaks whose region is a
# single pixel (cosmic-ray-like spikes).
regions, _ = label(valid & (snr >= GROW_THRESHOLD), structure=np.ones((3, 3)))
region_sizes = np.bincount(regions.ravel())

ys, xs = np.nonzero(peak_mask)
npix = region_sizes[regions[ys, xs]]

keep = npix >= MIN_PIXELS
rejected_single = int(np.count_nonzero(~keep))

ys, xs, npix = ys[keep], xs[keep], npix[keep]

print("Peaks kept:", len(xs), "| single-pixel spikes rejected:", rejected_single, flush=True)


# ==========================================
# 5. BUILD CATALOGUE
# ==========================================

print("Converting coordinates...", flush=True)

sky = wcs.pixel_to_world(xs, ys)

candidates = []

for i in range(len(xs)):

    y = int(ys[i])
    x = int(xs[i])

    pixel_flags = int(flags[y, x])

    active_flags = [
        name
        for name, bit in FLAG_BITS.items()
        if pixel_flags & (1 << bit)
    ]

    candidates.append({
        "x": x,
        "y": y,
        "intensity": float(image[y, x]),
        "background": float(background[y, x]),
        "snr": float(snr[y, x]),
        "npix": int(npix[i]),
        "ra": float(sky.ra.deg[i]),
        "dec": float(sky.dec.deg[i]),
        "flags": pixel_flags,
        "flag_names": ",".join(active_flags)
    })

candidates.sort(key=lambda item: item["snr"], reverse=True)


# ==========================================
# 6. SAVE CSV CATALOGUE
# ==========================================

print("Saving candidate catalogue...", flush=True)

with open(OUTPUT_CSV, "w", newline="") as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "x", "y", "intensity", "background", "snr", "npix",
            "ra", "dec", "flags", "flag_names"
        ]
    )

    writer.writeheader()
    writer.writerows(candidates)


# ==========================================
# 7. DISPLAY RESULTS
# ==========================================

print("\n===== SPHERESCAPE SOURCE DETECTION =====")

print("Detection threshold:", THRESHOLD, "sigma (measured noise)")
print("Excluded pixels:", np.count_nonzero(~valid))
print("Valid pixels:", np.count_nonzero(valid))
print("Single-pixel spikes rejected:", rejected_single)
print("Sources detected:", len(candidates))

print("\n===== TOP 15 CANDIDATES =====")

for i, source in enumerate(candidates[:15], 1):

    print(f"\nCandidate {i}")
    print("Pixel:", source["x"], source["y"])
    print("Intensity:", round(source["intensity"], 4))
    print("SNR:", round(source["snr"], 2))
    print("RA:", round(source["ra"], 6))
    print("Dec:", round(source["dec"], 6))
    print("Flags:", source["flag_names"])


# ==========================================
# 8. VISUALIZE DETECTED CANDIDATES
# ==========================================

print("\nCreating visualization...", flush=True)

fig, ax = plt.subplots(figsize=(12, 9))

vmin, vmax = np.nanpercentile(residual, [1, 99.5])

image_plot = ax.imshow(
    residual,
    origin="lower",
    cmap="inferno",
    vmin=vmin,
    vmax=vmax,
    interpolation="nearest"
)

top_candidates = candidates[:500]

if top_candidates:
    ax.scatter(
        [s["x"] for s in top_candidates],
        [s["y"] for s in top_candidates],
        s=5,
        facecolors="none",
        edgecolors="cyan",
        linewidths=0.5
    )

ax.set_title("SPHERESCAPE - Top 500 Sources (background subtracted)")
ax.set_xlabel("X Pixel")
ax.set_ylabel("Y Pixel")

fig.colorbar(image_plot, ax=ax, label="Intensity above background (MJy/sr)")

plt.savefig(OUTPUT_PNG, dpi=200, bbox_inches="tight")
plt.show()

print("\nSaved:", OUTPUT_CSV)
print("Saved:", OUTPUT_PNG)

print("\n===== SOURCE DETECTION COMPLETE =====")
