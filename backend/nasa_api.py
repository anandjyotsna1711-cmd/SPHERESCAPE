
from astroquery.ipac.irsa import Irsa
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.utils.data import conf

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np

from observation_matcher import summarize_observations


# PROJECT CONFIGURATION

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "raw"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# NASA retired the "spherex_qr2" quick release in Nov 2026. Its data now
# lives in Data Release 1 (first passes, Jul 2025 - Jan 2026) and the newest
# quick release (from Jul 2026). Searching both covers every pass so far.
COLLECTIONS = ["spherex_dr1", "spherex_qr3"]

conf.remote_timeout = 180


def _query_collection(coordinate, radius, collection):
    try:
        return collection, Irsa.query_sia(pos=(coordinate, radius), collection=collection), None
    except Exception as error:
        return collection, None, error


# SEARCH SPHEREX ARCHIVE

def search_spherex_observations(
    ra,
    dec,
    radius_arcsec=1,
    limit=50
):

    print("\nSearching NASA SPHEREx archive...")

    coordinate = SkyCoord(
        ra=float(ra),
        dec=float(dec),
        unit="deg"
    )

    radius = float(radius_arcsec) * u.arcsec

    # Query the collections in parallel so two searches take no longer than one.
    with ThreadPoolExecutor(max_workers=len(COLLECTIONS)) as pool:
        answers = list(pool.map(
            lambda name: _query_collection(coordinate, radius, name),
            COLLECTIONS
        ))

    tables = [table for _, table, _ in answers if table is not None]
    errors = [f"{name}: {error}" for name, _, error in answers if error is not None]

    for message in errors:
        print("Collection query failed:", message)

    if not tables:
        raise RuntimeError("All SPHEREx archive queries failed. " + "; ".join(errors))

    total_found = sum(len(table) for table in tables)

    print("Observations found:", total_found)

    # Archive metadata fields
    columns_to_return = [
        "facility_name",
        "instrument_name",
        "obs_id",
        "obs_collection",
        "s_ra",
        "s_dec",
        "s_region",
        "t_min",
        "t_max",
        "em_min",
        "em_max",
        "dataproduct_type",
        "access_format",
        "access_estsize",
        "access_url"
    ]

    observations = []

    for row in (row for table in tables for row in table):

        observation = {}

        for column in columns_to_return:

            if column not in row.colnames:
                continue

            value = row[column]

            if np.ma.is_masked(value):
                value = None

            elif isinstance(value, bytes):
                value = value.decode(
                    "utf-8",
                    errors="replace"
                )

            elif isinstance(value, np.generic):
                value = value.item()

            if isinstance(value, float):
                if not np.isfinite(value):
                    value = None

            observation[column] = value

        observations.append(observation)

    # Newest first, so a limited response shows the latest visits.
    observations.sort(
        key=lambda item: item.get("t_min") or 0,
        reverse=True
    )

    # Summarise every match before trimming to the limit.
    summary = summarize_observations(observations)

    observations = observations[:limit]

    print("Products returned:", len(observations))

    return {
        "mission": "SPHEREx",
        "collection": ", ".join(COLLECTIONS),
        "total_found": total_found,
        "returned": len(observations),
        "summary": summary,
        "observations": observations
    }
