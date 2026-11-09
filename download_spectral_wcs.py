
import requests
from pathlib import Path
from astropy.io import fits

url = (
    "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/"
    "qr2/spectral_wcs/cal-wcs-v4-2025-254/2/"
    "spectral_wcs_D2_spx_cal-wcs-v4-2025-254.fits"
)

output = Path("data/raw/spectral_wcs_D2.fits")
output.parent.mkdir(parents=True, exist_ok=True)

print("Downloading calibration file...")

with requests.get(url, stream=True, timeout=(30, 180)) as response:
    response.raise_for_status()

    with open(output, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)

print("Download complete!")

print("\n========== CALIBRATION FILE ==========")

with fits.open(output) as hdul:
    hdul.info()

    for hdu in hdul:
        print(f"\n--- {hdu.name} ---")
        print("Shape:", getattr(hdu.data, "shape", None))

        for key in [
            "VERSION", "DETECTOR", "DATE", "DATE-OBS",
            "CAL_VER", "ORIGIN", "PRODTYPE"
        ]:
            if key in hdu.header:
                print(f"{key}: {hdu.header[key]}")
