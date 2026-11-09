
from astropy.io import fits
import numpy as np

file_path = "data/raw/spherex_observation_may2026.fits"

with fits.open(file_path) as hdul:

    print("===== PSF HEADER =====")
    print(repr(hdul["PSF"].header))

    print("\n===== WCS-WAVE HEADER =====")
    print(repr(hdul["WCS-WAVE"].header))

    wave_data = hdul["WCS-WAVE"].data

    wavelengths = wave_data["VALUES"][0, :, :, 0]
    uncertainties = wave_data["VALUES"][0, :, :, 1]

    print("\n===== WAVELENGTH GRID =====")
    print("Shape:", wavelengths.shape)
    print("Minimum:", np.min(wavelengths))
    print("Maximum:", np.max(wavelengths))
    print("Mean:", np.mean(wavelengths))

    print("\n===== UNCERTAINTY GRID =====")
    print("Minimum:", np.min(uncertainties))
    print("Maximum:", np.max(uncertainties))
    print("Mean:", np.mean(uncertainties))

    print("\n===== WAVELENGTH GRID VALUES =====")
    print(wavelengths)

print("\nINSPECTION COMPLETE")

