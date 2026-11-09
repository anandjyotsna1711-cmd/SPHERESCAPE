
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS


PROJECT_DIR = Path(__file__).resolve().parent.parent

FITS_FILE = (
    PROJECT_DIR
    / "data"
    / "raw"
    / "spherex_observation.fits"
)


def get_fits_summary():

    if not FITS_FILE.exists():
        raise FileNotFoundError("SPHEREx FITS file not found.")

    print("Opening SPHEREx FITS observation...")

    with fits.open(FITS_FILE, memmap=True) as hdul:

        image_hdu = hdul["IMAGE"]
        image = image_hdu.data

        if image is None:
            raise ValueError("IMAGE extension contains no data.")

        image = np.asarray(image)

        finite_pixels = image[np.isfinite(image)]

        if finite_pixels.size == 0:
            raise ValueError("No valid image pixels found.")

        percentiles = np.percentile(
            finite_pixels,
            [1, 50, 99]
        )

        image_info = {
            "width": int(image.shape[1]),
            "height": int(image.shape[0]),
            "dimensions": list(image.shape),
            "data_type": str(image.dtype),
            "valid_pixels": int(finite_pixels.size),
            "invalid_pixels": int(image.size - finite_pixels.size),
            "minimum": float(np.min(finite_pixels)),
            "maximum": float(np.max(finite_pixels)),
            "mean": float(np.mean(finite_pixels)),
            "median": float(percentiles[1]),
            "percentile_1": float(percentiles[0]),
            "percentile_99": float(percentiles[2])
        }

        # Image metadata
        header = image_hdu.header

        metadata_keys = [
            "DATE-OBS",
            "MJD-OBS",
            "BUNIT",
            "TELESCOP",
            "INSTRUME",
            "OBJECT",
            "FILTER",
            "OBS_ID"
        ]

        metadata = {}

        for key in metadata_keys:
            if key in header:
                metadata[key] = str(header[key])

        # WCS information
        wcs_info = {
            "available": False
        }

        try:
            wcs = WCS(header)

            if wcs.has_celestial:
                height, width = image.shape[-2:]

                ra, dec = wcs.celestial.pixel_to_world_values(
                    width / 2,
                    height / 2
                )

                wcs_info = {
                    "available": True,
                    "center_ra": float(ra),
                    "center_dec": float(dec)
                }

        except Exception as error:
            print("WCS information unavailable:", error)

        # Flags information
        flags_info = {
            "available": False
        }

        if "FLAGS" in hdul and hdul["FLAGS"].data is not None:

            flags = hdul["FLAGS"].data

            flags_info = {
                "available": True,
                "dimensions": list(flags.shape),
                "flagged_pixels": int(np.count_nonzero(flags)),
                "total_pixels": int(flags.size)
            }

        # Variance information
        variance_info = {
            "available": False
        }

        if "VARIANCE" in hdul and hdul["VARIANCE"].data is not None:

            variance = np.asarray(hdul["VARIANCE"].data)
            valid_variance = variance[np.isfinite(variance)]

            if valid_variance.size > 0:

                variance_info = {
                    "available": True,
                    "dimensions": list(variance.shape),
                    "minimum": float(np.min(valid_variance)),
                    "maximum": float(np.max(valid_variance)),
                    "mean": float(np.mean(valid_variance))
                }

        # Other extensions
        extensions = {}

        for hdu in hdul:

            name = hdu.name

            if name in ["PRIMARY", "IMAGE", "FLAGS", "VARIANCE"]:
                continue

            if hdu.data is not None:
                extensions[name] = {
                    "type": type(hdu).__name__,
                    "dimensions": list(hdu.data.shape)
                    if hasattr(hdu.data, "shape")
                    else None
                }

                if name == "WCS-WAVE":
                    extensions[name]["columns"] = (
                        list(hdu.columns.names)
                        if hasattr(hdu, "columns")
                        else []
                    )

    print("FITS analysis complete.")

    return {
        "mission": "SPHEREx",
        "observation_id": "2025W43_1A_0516_1",
        "file": FITS_FILE.name,
        "image": image_info,
        "metadata": metadata,
        "wcs": wcs_info,
        "flags": flags_info,
        "variance": variance_info,
        "other_extensions": extensions,
        "image_url": "/first-light"
    }
