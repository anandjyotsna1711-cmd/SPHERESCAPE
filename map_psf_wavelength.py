
from astropy.io import fits
import pandas as pd
import numpy as np

fits_file = "data/raw/spherex_observation_may2026.fits"

psf_df = pd.read_csv("data/raw/psf_analysis.csv")

def bilinear_interpolate(x_grid, y_grid, values, x, y):

    ix = np.searchsorted(x_grid, x) - 1
    iy = np.searchsorted(y_grid, y) - 1

    ix = np.clip(ix, 0, len(x_grid) - 2)
    iy = np.clip(iy, 0, len(y_grid) - 2)

    x0, x1 = x_grid[ix], x_grid[ix + 1]
    y0, y1 = y_grid[iy], y_grid[iy + 1]

    tx = (x - x0) / (x1 - x0)
    ty = (y - y0) / (y1 - y0)

    f00 = values[iy, ix]
    f10 = values[iy, ix + 1]
    f01 = values[iy + 1, ix]
    f11 = values[iy + 1, ix + 1]

    return (
        (1 - tx) * (1 - ty) * f00
        + tx * (1 - ty) * f10
        + (1 - tx) * ty * f01
        + tx * ty * f11
    )


with fits.open(fits_file) as hdul:

    header = hdul["PSF"].header
    wave_data = hdul["WCS-WAVE"].data

    x_grid = np.asarray(wave_data["X"][0], dtype=float)
    y_grid = np.asarray(wave_data["Y"][0], dtype=float)

    values = wave_data["VALUES"][0]

    wavelengths = values[:, :, 0]
    bandwidths = values[:, :, 1]

    mapped_data = []

    for i in range(121):

        detector_x = float(header[f"XCTR_{i+1}"])
        detector_y = float(header[f"YCTR_{i+1}"])

        # PSF header coordinates are 0-based.
        # WCS-WAVE lookup coordinates use FITS 1-based coordinates.
        lookup_x = detector_x + 1
        lookup_y = detector_y + 1

        wavelength = bilinear_interpolate(
            x_grid, y_grid,
            wavelengths,
            lookup_x, lookup_y
        )

        bandwidth = bilinear_interpolate(
            x_grid, y_grid,
            bandwidths,
            lookup_x, lookup_y
        )

        mapped_data.append({
            "psf_zone": i,
            "detector_x": detector_x,
            "detector_y": detector_y,
            "wavelength_um": wavelength,
            "bandwidth_um": bandwidth,
            "peak_intensity": psf_df.loc[i, "peak_intensity"],
            "central_fraction": psf_df.loc[i, "central_fraction"]
        })


result = pd.DataFrame(mapped_data)

result.to_csv(
    "data/raw/psf_wavelength_mapping.csv",
    index=False
)

print("\nCORRECTED PSF-WAVELENGTH MAPPING\n")
print(result.head(10).to_string(index=False))

print("\nWAVELENGTH STATISTICS")
print(result["wavelength_um"].describe())

print("\nBANDWIDTH STATISTICS")
print(result["bandwidth_um"].describe())

print("\nCorrected mapping saved successfully!")
