
from astroquery.ipac.irsa import Irsa
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.utils.data import conf

from pathlib import Path
import numpy as np

from observation_matcher import summarize_observations


# PROJECT CONFIGURATION

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "raw"

DATA_DIR.mkdir(parents=True, exist_ok=True)

COLLECTION = "spherex_qr2"

conf.remote_timeout = 180


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

    results = Irsa.query_sia(
        pos=(
            coordinate,
            float(radius_arcsec) * u.arcsec
        ),
        collection=COLLECTION
    )

    print("Observations found:", len(results))

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

    available_columns = [
        column
        for column in columns_to_return
        if column in results.colnames
    ]

    observations = []

    for row in results:

        observation = {}

        for column in available_columns:

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
        "collection": COLLECTION,
        "total_found": len(results),
        "returned": len(observations),
        "summary": summary,
        "observations": observations
    }
