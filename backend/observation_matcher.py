
from collections import defaultdict
from astropy.time import Time


def mjd_to_date(mjd):
    if mjd is None:
        return None

    return Time(float(mjd), format="mjd", scale="utc").isot


def group_observations(observations):

    grouped = defaultdict(list)

    for item in observations:

        observation_id = item.get("obs_id")
        start_time = item.get("t_min")

        if not observation_id or start_time is None:
            continue

        key = (observation_id, float(start_time))

        wavelength_min = item.get("em_min")
        wavelength_max = item.get("em_max")

        product = {
            "observation_id": observation_id,
            "date": mjd_to_date(start_time),
            "mjd": float(start_time),
            "wavelength_min_m": (
                float(wavelength_min)
                if wavelength_min is not None else None
            ),
            "wavelength_max_m": (
                float(wavelength_max)
                if wavelength_max is not None else None
            ),
            "center_ra": item.get("s_ra"),
            "center_dec": item.get("s_dec"),
            "access_url": item.get("access_url")
        }

        grouped[key].append(product)

    epochs = []

    for (observation_id, mjd), products in grouped.items():

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
