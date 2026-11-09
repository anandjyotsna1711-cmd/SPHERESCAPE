
import numpy as np
import pandas as pd
from astropy.io import fits

psf_csv = "data/raw/psf_wavelength_mapping.csv"
cal_file = "data/raw/spectral_wcs_D2.fits"

df = pd.read_csv(psf_csv)

with fits.open(cal_file) as hdul:
    cwave = np.asarray(hdul["CWAVE"].data, dtype=float)
    cband = np.asarray(hdul["CBAND"].data, dtype=float)

# PSF centre coordinates are detector coordinates.
# Convert each centre to the nearest zero-based array index.
x = np.rint(df["detector_x"].values).astype(int)
y = np.rint(df["detector_y"].values).astype(int)

if np.any((x < 0) | (x >= cwave.shape[1])):
    raise ValueError("Some PSF X coordinates are outside the calibration map.")

if np.any((y < 0) | (y >= cwave.shape[0])):
    raise ValueError("Some PSF Y coordinates are outside the calibration map.")

df["calibrated_wavelength_um"] = cwave[y, x]
df["calibrated_bandwidth_um"] = cband[y, x]

output = "data/raw/psf_calibrated_mapping.csv"
df.to_csv(output, index=False)

print("========== CALIBRATED PSF MAPPING ==========")
print(df[[
    "psf_zone",
    "detector_x",
    "detector_y",
    "calibrated_wavelength_um",
    "calibrated_bandwidth_um"
]].head(10).to_string(index=False))

print("\n========== WAVELENGTH STATISTICS ==========")
print(df["calibrated_wavelength_um"].describe())

print("\n========== BANDWIDTH STATISTICS ==========")
print(df["calibrated_bandwidth_um"].describe())

print("\nSaved:", output)
