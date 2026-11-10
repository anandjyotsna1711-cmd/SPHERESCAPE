
from pathlib import Path

import json

from flask import Flask, render_template, send_file, send_from_directory, jsonify, request

from astropy.coordinates import SkyCoord
from astropy.coordinates.name_resolve import NameResolveError, sesame_url

from nasa_api import search_spherex_observations

from fits_processor import get_fits_summary

from observation_matcher import group_observations

from name_search import find_closest_objects

PROJECT_DIR = Path(__file__).resolve().parent.parent

# Object-name lookup (Sesame): try the Harvard mirror first. The CDS
# server can hang for ~20 s on some networks before falling back.
sesame_url.set([
    "https://vizier.cfa.harvard.edu/viz-bin/nph-sesame/",
    "https://cds.unistra.fr/cgi-bin/nph-sesame/"
])

app = Flask(
    __name__,
    template_folder=str(PROJECT_DIR / "frontend" / "templates")
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/first-light")
def first_light():

    image_path = (
        PROJECT_DIR
        / "data"
        / "processed"
        / "spherex_first_light.png"
    )

    if not image_path.exists():
        return jsonify({"error": "First-light image not found"}), 404

    return send_file(image_path, mimetype="image/png")


@app.route("/api/observations")
def observations():

    try:
        ra = float(request.args.get("ra"))
        dec = float(request.args.get("dec"))

        radius = float(request.args.get("radius", 1))
        limit = int(request.args.get("limit", 50))

        if not 0 <= ra <= 360:
            return jsonify({"error": "RA must be between 0 and 360"}), 400

        if not -90 <= dec <= 90:
            return jsonify({"error": "DEC must be between -90 and 90"}), 400

        if not 0 < radius <= 3600:
            return jsonify({"error": "Radius must be greater than 0 and at most 3600 arcseconds"}), 400

        if not 1 <= limit <= 100:
            return jsonify({"error": "Limit must be between 1 and 100"}), 400

        result = search_spherex_observations(
            ra=ra,
            dec=dec,
            radius_arcsec=radius,
            limit=limit
        )

        return jsonify(result)

    except (TypeError, ValueError):
        return jsonify({
            "error": "Please provide valid RA and DEC coordinates."
        }), 400

    except Exception as error:
        print("SPHEREx API error:", repr(error))

        return jsonify({
            "error": "Could not retrieve observations from NASA/IPAC.",
            "details": str(error)
        }), 502
@app.route("/api/observations/matched")
def matched_observations():

    try:
        ra = float(request.args.get("ra"))
        dec = float(request.args.get("dec"))
        radius = float(request.args.get("radius", 1))
        limit = int(request.args.get("limit", 50))

        if not 0 <= ra <= 360:
            return jsonify({"error": "Invalid RA"}), 400

        if not -90 <= dec <= 90:
            return jsonify({"error": "Invalid DEC"}), 400

        if not 0 < radius <= 3600:
            return jsonify({"error": "Invalid search radius"}), 400

        if not 1 <= limit <= 100:
            return jsonify({"error": "Invalid result limit"}), 400

        result = search_spherex_observations(
            ra=ra,
            dec=dec,
            radius_arcsec=radius,
            limit=limit
        )

        grouped = group_observations(
            result["observations"]
        )

        return jsonify({
            "mission": "SPHEREx",
            "archive_total": result["total_found"],
            "returned_products": result["returned"],
            "archive_summary": result["summary"],
            "matching_results": grouped
        })

    except (TypeError, ValueError):
        return jsonify({
            "error": "Please provide valid coordinates."
        }), 400

    except Exception as error:
        print("Matching error:", repr(error))

        return jsonify({
            "error": "Could not group observations.",
            "details": str(error)
        }), 500
@app.route("/api/resolve")
def resolve_name():

    name = (request.args.get("name") or "").strip()

    if not name or len(name) > 100:
        return jsonify({
            "error": "Please enter an object name (e.g. M31 or Orion Nebula)."
        }), 400

    # 1. Exact name or catalogue ID (M31, NGC 224, Betelgeuse...).
    try:
        coordinate = SkyCoord.from_name(name)

        return jsonify({
            "name": name,
            "matched_name": name,
            "exact": True,
            "ra": float(coordinate.ra.deg),
            "dec": float(coordinate.dec.deg),
            "alternatives": []
        })

    except NameResolveError:
        pass

    except Exception as error:
        print("Exact name lookup error:", repr(error))

    # 2. Closest match: proper names containing every word typed,
    #    e.g. "Canis Major" -> "Canis Major Dwarf Galaxy".
    try:
        matches = find_closest_objects(name)

    except Exception as error:
        print("Closest-match lookup error:", repr(error))

        return jsonify({
            "error": "The name lookup service is unavailable right now. "
                     "Try again, or search by coordinates.",
            "details": str(error)
        }), 502

    if not matches:
        return jsonify({
            "error": f"Couldn't find anything called '{name}'. Check the "
                     "spelling, or try a catalogue name such as M31 or NGC 224."
        }), 404

    best = matches[0]

    return jsonify({
        "name": name,
        "matched_name": best["name"],
        "matched_type": best["type"],
        "exact": False,
        "ra": best["ra"],
        "dec": best["dec"],
        "alternatives": matches[1:]
    })


@app.route("/api/science")
def science_results():
    """Precomputed analysis results (see export_psf_web_data.py and
    validate_sources_2mass.py). Missing pieces come back as null."""

    results_dir = PROJECT_DIR / "results"
    payload = {}

    for key, filename in [
        ("psf", "psf_zones.json"),
        ("sources", "source_validation.json")
    ]:
        path = results_dir / filename
        payload[key] = (
            json.loads(path.read_text(encoding="utf-8"))
            if path.exists() else None
        )

    return jsonify(payload)


@app.route("/sky-dome.jpg")
def sky_dome_texture():
    """SPHEREx all-sky map re-projected to RA/Dec for the Cosmic Explorer
    sky dome (built by build_sky_dome_texture.py)."""

    path = PROJECT_DIR / "data" / "processed" / "sky_dome_spherex.jpg"

    if not path.exists():
        return jsonify({"error": "Sky texture not found. Run build_sky_dome_texture.py."}), 404

    return send_file(path, mimetype="image/jpeg", max_age=86400)


VIEWER_DIR = PROJECT_DIR / "results" / "viewer"


@app.route("/api/viewer/meta")
def viewer_meta():
    """Image size, decoding info and coordinate grids for the image viewer
    (written by export_viewer_data.py)."""

    path = VIEWER_DIR / "meta.json"

    if not path.exists():
        return jsonify({"error": "Viewer data not found. Run export_viewer_data.py."}), 404

    return send_file(path, mimetype="application/json", max_age=3600)


@app.route("/api/viewer/image")
def viewer_image():
    """All pixels of the viewer image: gzipped, byte-shuffled int16.
    Sent with Content-Encoding: gzip so the browser unzips it for free."""

    path = VIEWER_DIR / "image.i16.gz"

    if not path.exists():
        return jsonify({"error": "Viewer image not found. Run export_viewer_data.py."}), 404

    response = send_file(path, mimetype="application/octet-stream", max_age=3600)
    response.headers["Content-Encoding"] = "gzip"
    return response


@app.route("/figures/<path:filename>")
def figure(filename):
    """Serve images from results/figures/ (send_from_directory blocks ../)."""

    return send_from_directory(PROJECT_DIR / "results" / "figures", filename)


@app.route("/api/fits/summary")
def fits_summary():

    try:
        result = get_fits_summary()
        return jsonify(result)

    except FileNotFoundError as error:
        return jsonify({"error": str(error)}), 404

    except Exception as error:
        print("FITS processing error:", repr(error))

        return jsonify({
            "error": "Could not process SPHEREx FITS data.",
            "details": str(error)
        }), 500

if __name__ == "__main__":

    print("SPHERESCAPE is starting...")
    print("Homepage: http://127.0.0.1:5000")
    print("Observation API: http://127.0.0.1:5000/api/observations")

    app.run(debug=True)
