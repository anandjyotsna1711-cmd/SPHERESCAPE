
from astropy.io import fits

FILE = "data/raw/spherex_observation_may2026.fits"

keywords = [
    "CAL", "WCS", "PSF", "VERSION", "PROC",
    "DETECTOR", "OBSID", "DATE", "BAND"
]

with fits.open(FILE, memmap=True) as hdul:

    for hdu_name in ["PRIMARY", "IMAGE", "PSF", "WCS-WAVE"]:

        header = hdul[hdu_name].header

        print(f"\n========== {hdu_name} ==========")

        for key, value in header.items():
            if any(word in key.upper() for word in keywords):
                print(f"{key}: {value}")
