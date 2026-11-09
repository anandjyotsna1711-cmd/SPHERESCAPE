
from astropy.io import fits
import numpy as np

FILE = "data/raw/spherex_observation_may2026.fits"

FLAG_BITS = {
    "TRANSIENT": 0,
    "OVERFLOW": 1,
    "SUR_ERROR": 2,
    "PHANTOM": 4,
    "REFERENCE": 5,
    "NONFUNC": 6,
    "DICHROIC": 7,
    "MISSING_DATA": 9,
    "HOT": 10,
    "COLD": 11,
    "FULLSAMPLE": 12,
    "PHANMISS": 14,
    "NONLINEAR": 15,
    "PERSIST": 17,
    "OUTLIER": 19,
    "SOURCE": 21,
    "GHOST": 22,
    "GHOST_FPA": 23,
    "GHOST_EXT": 24,
    "BLOOM": 26,
    "SNOWBALL": 27,
    "HALO": 28
}

with fits.open(FILE) as hdul:
    image = hdul["IMAGE"].data
    flags = hdul["FLAGS"].data.astype(np.uint32)

valid = np.isfinite(image)

threshold = np.percentile(image[valid], 99)
bright = valid & (image > threshold)

print("\n===== FULL IMAGE FLAG ANALYSIS =====")

for name, bit in FLAG_BITS.items():
    mask = np.uint32(1 << bit)

    count = np.count_nonzero((flags & mask) != 0)

    if count > 0:
        print(f"{name}: {count} pixels")

print("\n===== BRIGHT PIXEL FLAG ANALYSIS =====")

for name, bit in FLAG_BITS.items():
    mask = np.uint32(1 << bit)

    count = np.count_nonzero(
        bright & ((flags & mask) != 0)
    )

    if count > 0:
        print(f"{name}: {count} bright pixels")

print("\n===== FLAG DECODING COMPLETE =====")
