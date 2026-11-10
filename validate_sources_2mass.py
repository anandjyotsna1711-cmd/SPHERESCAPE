
"""
Check detect_sources.py against the 2MASS star catalogue.

2MASS observed the whole sky at 1.25 and 1.65 micrometres, almost the same
wavelengths as SPHEREx detector 2 (1.1-1.64 micrometres), so most real
sources we detect should sit on a 2MASS star.

Reports:
- purity: share of our detections within MATCH_RADIUS of a 2MASS star,
  compared with random positions (the chance rate in this crowded field)
- completeness: share of 2MASS stars we recover, by brightness

Run detect_sources.py first. Needs internet the first time (2MASS is
fetched from NASA/IPAC IRSA and cached in data/raw/).
"""

import json
import os

import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS
from scipy.spatial import cKDTree


FITS_FILE = "data/raw/spherex_observation_may2026.fits"
CANDIDATES = "data/raw/source_candidates.csv"
CATALOGUE_CACHE = "data/raw/twomass_field.ecsv"
OUTPUT = "results/source_validation.json"

MATCH_RADIUS = 1.5     # pixels (about 9 arcseconds)
MAG_LIMIT = 15.0       # 2MASS J magnitude limit for the comparison


# ==========================================
# 1. LOAD IMAGE GEOMETRY AND DETECTIONS
# ==========================================

with fits.open(FITS_FILE) as hdul:
    header = hdul["IMAGE"].header
    wcs = WCS(header).celestial
    shape = hdul["IMAGE"].data.shape
    observation = header.get("OBSID", "unknown")

ny, nx = shape
centre = wcs.pixel_to_world((nx - 1) / 2, (ny - 1) / 2)
radius = max(
    centre.separation(wcs.pixel_to_world(x, y)).deg
    for x, y in [(0, 0), (nx - 1, 0), (0, ny - 1), (nx - 1, ny - 1)]
) + 0.05

detections = pd.read_csv(CANDIDATES)
det_xy = detections[["x", "y"]].to_numpy(dtype=float)

print("Detections:", len(det_xy))


# ==========================================
# 2. FETCH 2MASS STARS (CACHED)
# ==========================================

if os.path.exists(CATALOGUE_CACHE):
    stars = Table.read(CATALOGUE_CACHE)
    print("Loaded cached 2MASS catalogue:", len(stars), "stars")

else:
    from astroquery.ipac.irsa import Irsa

    print(f"Fetching 2MASS stars (J < {MAG_LIMIT}) within {radius:.2f} deg... "
          "this takes about a minute.", flush=True)

    stars = Irsa.query_tap(
        "SELECT ra, dec, j_m, h_m FROM fp_psc WHERE "
        f"CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', "
        f"{centre.ra.deg}, {centre.dec.deg}, {radius}))=1 "
        f"AND j_m < {MAG_LIMIT}"
    ).to_table()

    stars.write(CATALOGUE_CACHE, overwrite=True)
    print("Fetched and cached", len(stars), "stars")

px, py = wcs.world_to_pixel_values(stars["ra"], stars["dec"])
inside = (px > -0.5) & (px < nx - 0.5) & (py > -0.5) & (py < ny - 0.5)

star_xy = np.column_stack([px[inside], py[inside]])
star_j = np.asarray(stars["j_m"], dtype=float)[inside]

print("2MASS stars inside the image:", len(star_xy))


# ==========================================
# 3. PURITY: DO DETECTIONS SIT ON STARS?
# ==========================================

star_tree = cKDTree(star_xy)


def match_rate(xy):
    if len(xy) == 0:
        return float("nan")
    distance, _ = star_tree.query(xy, distance_upper_bound=MATCH_RADIUS)
    return float(np.isfinite(distance).mean())


rng = np.random.default_rng(1)
random_xy = rng.uniform(0, [nx - 1, ny - 1], size=(20000, 2))

chance = match_rate(random_xy)
purity_all = match_rate(det_xy)

purity_top = {
    str(n): match_rate(det_xy[:n])
    for n in [100, 1000, 10000]
    if len(det_xy) >= n
}


# ==========================================
# 4. COMPLETENESS: DO WE FIND THE STARS?
# ==========================================

det_tree = cKDTree(det_xy)
distance, _ = det_tree.query(star_xy, distance_upper_bound=MATCH_RADIUS)
found = np.isfinite(distance)

completeness = []
edges = [-np.inf, 10, 11, 12, 13, 14, MAG_LIMIT]

for low, high in zip(edges[:-1], edges[1:]):
    in_bin = (star_j >= low) & (star_j < high)
    completeness.append({
        "j_min": None if np.isinf(low) else low,
        "j_max": high,
        "stars": int(in_bin.sum()),
        "recovered": float(found[in_bin].mean()) if in_bin.any() else None
    })


# ==========================================
# 5. REPORT AND SAVE
# ==========================================

print(f"\n===== 2MASS VALIDATION (match radius {MATCH_RADIUS} px) =====")
print(f"Random positions on a 2MASS star (chance): {chance:.1%}")
print(f"All detections on a 2MASS star:            {purity_all:.1%}")

for n, rate in purity_top.items():
    print(f"Top {n:>5} detections:                       {rate:.1%}")

print("\nShare of 2MASS stars recovered, by J magnitude:")

for row in completeness:
    label = f"J < {row['j_max']:g}" if row["j_min"] is None else f"{row['j_min']} <= J < {row['j_max']}"
    print(f"  {label:<14} {row['recovered']:.0%} of {row['stars']} stars")

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(OUTPUT, "w") as file:
    json.dump({
        "observation": observation,
        "detections": int(len(det_xy)),
        "catalogue": f"2MASS Point Source Catalog, J < {MAG_LIMIT:g}",
        "catalogue_stars_in_image": int(len(star_xy)),
        "match_radius_pixels": MATCH_RADIUS,
        "chance_match_rate": chance,
        "match_rate_all": purity_all,
        "match_rate_top": purity_top,
        "completeness_by_j_mag": completeness
    }, file, indent=2)

print("\nSaved:", OUTPUT)
