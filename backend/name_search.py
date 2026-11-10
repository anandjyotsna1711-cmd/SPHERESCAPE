"""
Forgiving object-name search.

Sesame (used by /api/resolve first) only understands exact names, so
"Canis Major" fails even though SIMBAD knows the "Canis Major Dwarf Galaxy".
This module asks SIMBAD for proper names containing every word the user typed
and ranks them so the best-known object comes first.
"""

import re
from functools import lru_cache

import requests


# The Harvard mirror answers in ~1 s; the main CDS server can hang on some
# networks. Both serve the same database.
SIMBAD_TAP_SERVERS = [
    "https://simbad.cfa.harvard.edu/simbad/sim-tap/sync",
    "https://simbad.cds.unistra.fr/simbad/sim-tap/sync",
]

# SIMBAD object-type codes -> plain words for the suggestions list.
OBJECT_TYPES = {
    "G": "galaxy", "GiG": "galaxy", "GiC": "galaxy", "BiC": "galaxy",
    "AGN": "galaxy", "SyG": "galaxy", "Sy1": "galaxy", "Sy2": "galaxy",
    "LIN": "galaxy", "SBG": "galaxy", "EmG": "galaxy", "rG": "galaxy",
    "H2G": "galaxy", "LSB": "galaxy", "QSO": "quasar",
    "GrG": "galaxy group", "ClG": "galaxy cluster", "SCG": "galaxy supercluster",
    "HII": "nebula", "RNe": "nebula", "ISM": "nebula", "Cld": "cloud",
    "MoC": "molecular cloud", "DNe": "dark nebula", "PN": "planetary nebula",
    "SNR": "supernova remnant", "OpC": "star cluster", "Cl*": "star cluster",
    "GlC": "globular cluster", "As*": "star group", "*": "star",
    "**": "double star", "PM*": "star", "V*": "variable star",
    "reg": "region of sky",
}


def _words(query):
    """Lower-case words safe to put inside an ADQL LIKE pattern."""

    cleaned = re.sub(r"[^a-z0-9+\-. ]", " ", query.lower())
    words = [word for word in cleaned.split() if len(word) >= 2]
    return words[:5]


def _tap_query(adql):
    last_error = None

    for server in SIMBAD_TAP_SERVERS:
        try:
            response = requests.get(
                server,
                params={
                    "REQUEST": "doQuery",
                    "LANG": "ADQL",
                    "FORMAT": "json",
                    "QUERY": adql,
                },
                timeout=(4, 15),
            )
            response.raise_for_status()
            return response.json()["data"]

        except (requests.RequestException, KeyError, ValueError) as error:
            last_error = error

    raise RuntimeError(f"SIMBAD is unavailable: {last_error}")


def _rank(name, query):
    """0 = exact name, 1 = starts with the query, 2 = a word starts with it, 3 = contains it."""

    name = name.lower()
    query = " ".join(query.lower().split())

    if name == query:
        return 0
    if name.startswith(query):
        return 1
    if re.search(r"\b" + re.escape(query), name):
        return 2
    return 3


@lru_cache(maxsize=256)
def find_closest_objects(query, limit=6):
    """
    Return up to `limit` objects whose proper name contains every word of
    `query`, best match first: [{"name", "ra", "dec", "type"}].
    """

    words = _words(query)

    if not words:
        return []

    conditions = " AND ".join(
        f"lowercase(i.id) LIKE '%{word}%'" for word in words
    )

    rows = _tap_query(
        "SELECT TOP 80 i.id, b.main_id, b.ra, b.dec, b.otype, b.nbref "
        "FROM ident AS i JOIN basic AS b ON i.oidref = b.oid "
        f"WHERE i.id LIKE 'NAME %' AND {conditions}"
    )

    best = {}

    for identifier, main_id, ra, dec, otype, references in rows:

        if ra is None or dec is None:
            continue

        name = identifier[5:].strip()  # drop the "NAME " prefix

        # Best match first, then the best-studied object (most papers),
        # then the fuller alias ("Canis Major Dwarf Galaxy" over
        # "Canis Major Galaxy").
        score = (_rank(name, query), -(references or 0), -len(name))

        # One entry per object, under its best-matching name.
        if main_id not in best or score < best[main_id]["score"]:
            best[main_id] = {
                "name": name,
                "ra": float(ra),
                "dec": float(dec),
                "type": OBJECT_TYPES.get(otype),
                "score": score,
            }

    ranked = sorted(best.values(), key=lambda item: item["score"])

    for item in ranked:
        del item["score"]

    return ranked[:limit]
