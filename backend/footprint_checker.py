from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS

PROJECT_DIR = Path(__file__).resolve().parent.parent

FITS_FILE = (
    PROJECT_DIR
    / "data"
    / "raw"
    / "spherex_observation.fits"
)


def get_sky_footprint(fits_path=FITS_FILE):

    fits_path = Path(fits_path)

    if not fits_path.exists():
        raise FileNotFoundError(f"FITS file not found: {fits_path}")

    with fits.open(fits_path) as hdul:

        image_hdu = hdul["IMAGE"]
        image = image_hdu.data

        if image is None or image.ndim != 2:
            raise ValueError("Expected a two-dimensional FITS image.")

        height, width = image.shape

        wcs = WCS(image_hdu.header)

        if not wcs.has_celestial:
            raise ValueError("Celestial WCS coordinates are unavailable.")

        celestial_wcs = wcs.celestial

        pixel_corners = {
            "top_left": (0, 0),
            "top_right": (width - 1, 0),
            "bottom_right": (width - 1, height - 1),
            "bottom_left": (0, height - 1)
        }

        corners = {}

        for name, (x, y) in pixel_corners.items():

            sky = celestial_wcs.pixel_to_world(x, y)

            corners[name] = {
                "ra": float(sky.ra.deg),
                "dec": float(sky.dec.deg)
            }

        center = celestial_wcs.pixel_to_world(
            (width - 1) / 2,
            (height - 1) / 2
        )

    return {
        "file": fits_path.name,
        "image_width": width,
        "image_height": height,
        "center": {
            "ra": float(center.ra.deg),
            "dec": float(center.dec.deg)
        },
        "corners": corners
    }


if __name__ == "__main__":

    footprint = get_sky_footprint()

    print("\nSPHEREx SKY FOOTPRINT")
    print("---------------------")

    print("Image:", footprint["file"])
    print("Dimensions:",
          footprint["image_width"],
          "x",
          footprint["image_height"])

    print("\nCenter:")
    print(footprint["center"])

    print("\nCorners:")

    for name, coordinates in footprint["corners"].items():
        print(name, coordinates)