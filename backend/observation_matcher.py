
from collections import Counter, defaultdict
from astropy.time import Time


# SPHEREx has six detectors, each covering one slice of the
# 0.75-5.0 micron range (values from the archive's em_min/em_max).
SPHEREX_BANDS = [
    (1, 0.75, 1.11),
    (2, 1.11, 1.64),
    (3, 1.64, 2.42),
    (4, 2.42, 3.82),
    (5, 3.82, 4.42),
    (6, 4.42, 5.01),
]


def mjd_to_date(mjd):
    if mjd is None:
        return None

    return Time(float(mjd), format="mjd", scale="utc").isot


def wavelength_to_band(wavelength_min_m, wavelength_max_m):
    """Return the SPHEREx band number (1-6) for a wavelength range in metres."""

    if wavelength_min_m is None or wavelength_max_m is None:
        return None

    middle_um = (float(wavelength_min_m) + float(wavelength_max_m)) / 2 * 1e6

    for band, low, high in SPHEREX_BANDS:
        if low <= middle_um < high:
            return band

    return None


def parse_footprint(region):
    """
    Turn an archive s_region like "POLYGON ICRS 6.96 41.75 11.28 43.13 ..."
    into [[ra, dec], ...]. Returns None if it isn't a polygon.
    """

    if not region or "POLYGON" not in str(region).upper():
        return None

    numbers = []
    for token in str(region).split():
        try:
            numbers.append(round(float(token), 4))
        except ValueError:
            continue

    if len(numbers) < 6 or len(numbers) % 2:
        return None

    points = [numbers[i:i + 2] for i in range(0, len(numbers), 2)]

    # Drop a repeated closing vertex.
    if len(points) > 3 and points[0] == points[-1]:
        points = points[:-1]

    return points


def summarize_observations(observations):
    """Summarise every archive product: when it was seen and in which bands."""

    visits = Counter()
    bands = {}

    for item in observations:

        start_time = item.get("t_min")

        if start_time is not None:
            visits[mjd_to_date(start_time)[:10]] += 1

        wavelength_min = item.get("em_min")
        wavelength_max = item.get("em_max")
        band = wavelength_to_band(wavelength_min, wavelength_max)

        if band is None:
            continue

        if band not in bands:
            bands[band] = {
                "band": band,
                "wavelength_min_um": round(float(wavelength_min) * 1e6, 3),
                "wavelength_max_um": round(float(wavelength_max) * 1e6, 3),
                "images": 0
            }

        bands[band]["images"] += 1

    visit_list = [
        {"date": date, "images": count}
        for date, count in sorted(visits.items())
    ]

    return {
        "total_images": len(observations),
        "first_date": visit_list[0]["date"] if visit_list else None,
        "last_date": visit_list[-1]["date"] if visit_list else None,
        "visit_dates": visit_list,
        "bands": [bands[band] for band in sorted(bands)]
    }


def group_observations(observations):

    grouped = defaultdict(list)

    for item in observations:

        observation_id = item.get("obs_id")
        start_time = item.get("t_min")

        if not observation_id or start_time is None:
            continue

        # One observation = one pointing. Its detectors can start a
        # fraction of a second apart, so group by ID, not start time.
        key = observation_id

        wavelength_min = item.get("em_min")
        wavelength_max = item.get("em_max")
        size_kb = item.get("access_estsize")

        product = {
            "observation_id": observation_id,
            "date": mjd_to_date(start_time),
            "mjd": float(start_time),
            "band": wavelength_to_band(wavelength_min, wavelength_max),
            "wavelength_min_m": (
                float(wavelength_min)
                if wavelength_min is not None else None
            ),
            "wavelength_max_m": (
                float(wavelength_max)
                if wavelength_max is not None else None
            ),
            "size_mb": (
                round(float(size_kb) / 1024, 1)
                if size_kb is not None else None
            ),
            "center_ra": item.get("s_ra"),
            "center_dec": item.get("s_dec"),
            "footprint": parse_footprint(item.get("s_region")),
            "access_url": item.get("access_url")
        }

        grouped[key].append(product)

    epochs = []

    for observation_id, products in grouped.items():

        products.sort(key=lambda product: product["band"] or 0)

        mjd = min(product["mjd"] for product in products)

        wavelengths = [
            product for product in products
            if product["wavelength_min_m"] is not None
            and product["wavelength_max_m"] is not None
        ]

        epochs.append({
            "observation_id": observation_id,
            "date": mjd_to_date(mjd),
            "mjd": mjd,
            "product_count": len(products),
            "wavelength_product_count": len(wavelengths),
            "products": products
        })

    epochs.sort(key=lambda item: item["mjd"])

    return {
        "total_products": len(observations),
        "unique_epochs": len(epochs),
        "epochs": epochs
    }
