
from astropy.io import fits
from astropy.wcs import WCS
from scipy.ndimage import maximum_filter, label
import numpy as np
import csv
import matplotlib.pyplot as plt

# ==========================================
# 1. LOAD SPHEREx DATA
# ==========================================

FILE = "data/raw/spherex_observation_may2026.fits"

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
    "SUR_ERROR",
    "NONFUNC",
    "DICHROIC",
    "MISSING_DATA",
    "HOT",
    "COLD",
    "NONLINEAR",
    "PERSIST",
    "BLOOM",
    "SNOWBALL",
    "HALO"
]

print("Applying quality masks...", flush=True)

bad_mask = np.zeros(flags.shape, dtype=bool)

for name in BAD_FLAGS:
    bit = FLAG_BITS[name]
    bad_mask |= (
        flags & np.uint32(1 << bit)
    ) != 0


# ==========================================
# 3. CALCULATE SIGNAL-TO-NOISE RATIO
# ==========================================

print("Calculating signal-to-noise ratio...", flush=True)

valid = (
    np.isfinite(image) &
    np.isfinite(variance) &
    (variance > 0) &
    (~bad_mask)
)

snr = np.full(image.shape, np.nan)

snr[valid] = (
    image[valid] / np.sqrt(variance[valid])
)

print("SNR calculation complete!", flush=True)

threshold = 5.0


# ==========================================
# 4. DETECT LOCAL PEAKS
# ==========================================

print("Detecting candidate peaks...", flush=True)

safe_snr = np.where(valid, snr, -np.inf)

local_max = maximum_filter(
    safe_snr,
    size=5
)

peak_mask = (
    valid &
    (snr >= threshold) &
    (snr == local_max)
)

print(
    "Peak pixels detected:",
    np.count_nonzero(peak_mask),
    flush=True
)


# ==========================================
# 5. GROUP NEARBY PEAKS
# ==========================================

print("Grouping nearby peaks...", flush=True)

labels, number = label(peak_mask)

candidates = []

ys, xs = np.where(peak_mask)

if len(xs) > 0:

    region_ids = labels[ys, xs]
    peak_snrs = snr[ys, xs]

    order = np.lexsort(
        (-peak_snrs, region_ids)
    )

    sorted_ids = region_ids[order]

    first = np.r_[
        True,
        sorted_ids[1:] != sorted_ids[:-1]
    ]

    best_indices = order[first]

    best_y = ys[best_indices]
    best_x = xs[best_indices]

    print("Converting coordinates...", flush=True)

    sky = wcs.pixel_to_world(
        best_x,
        best_y
    )

    for i in range(len(best_indices)):

        y = int(best_y[i])
        x = int(best_x[i])

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
            "snr": float(snr[y, x]),
            "ra": float(sky.ra.deg[i]),
            "dec": float(sky.dec.deg[i]),
            "flags": pixel_flags,
            "flag_names": ",".join(active_flags)
        })


# ==========================================
# 6. SORT CANDIDATES
# ==========================================

candidates.sort(
    key=lambda item: item["snr"],
    reverse=True
)


# ==========================================
# 7. SAVE CSV CATALOGUE
# ==========================================

print("Saving candidate catalogue...", flush=True)

output_file = "data/raw/source_candidates.csv"

with open(output_file, "w", newline="") as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "x",
            "y",
            "intensity",
            "snr",
            "ra",
            "dec",
            "flags",
            "flag_names"
        ]
    )

    writer.writeheader()
    writer.writerows(candidates)


# ==========================================
# 8. DISPLAY RESULTS
# ==========================================

print("\n===== SPHERESCAPE SOURCE DETECTION =====")

print("SNR threshold:", threshold)
print("Excluded pixels:", np.count_nonzero(bad_mask))
print("Valid pixels:", np.count_nonzero(valid))
print("Peak pixels:", np.count_nonzero(peak_mask))
print("Candidate regions detected:", len(candidates))

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
# 9. VISUALIZE DETECTED CANDIDATES
# ==========================================

print("\nCreating visualization...", flush=True)

display_image = np.where(
    valid,
    image,
    np.nan
)

fig, ax = plt.subplots(figsize=(12, 9))

vmin = np.nanpercentile(display_image, 1)
vmax = np.nanpercentile(display_image, 99.5)

image_plot = ax.imshow(
    display_image,
    origin="lower",
    cmap="inferno",
    vmin=vmin,
    vmax=vmax,
    interpolation="nearest"
)

# Show only the 500 strongest candidates
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

ax.set_title(
    "SPHERESCAPE - Top 500 Candidate Peaks"
)

ax.set_xlabel("X Pixel")
ax.set_ylabel("Y Pixel")

fig.colorbar(
    image_plot,
    ax=ax,
    label="Image Intensity"
)

plt.savefig(
    "data/raw/source_detection.png",
    dpi=200,
    bbox_inches="tight"
)

plt.show()

print("\nSaved: data/raw/source_candidates.csv")
print("Saved: data/raw/source_detection.png")

print("\n===== SOURCE DETECTION COMPLETE =====")
