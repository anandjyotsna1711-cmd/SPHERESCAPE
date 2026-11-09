
import numpy as np
from astropy.io import fits
from scipy.interpolate import RegularGridInterpolator

cal_file = "data/raw/spectral_wcs_D2.fits"
obs_file = "data/raw/spherex_observation_may2026.fits"

with fits.open(cal_file) as cal, fits.open(obs_file) as obs:

    cwave = np.asarray(cal["CWAVE"].data, dtype=float)
    cband = np.asarray(cal["CBAND"].data, dtype=float)

    table = obs["WCS-WAVE"].data[0]

    x_grid = np.asarray(table["X"], dtype=float)
    y_grid = np.asarray(table["Y"], dtype=float)
    values = np.asarray(table["VALUES"], dtype=float)

    # Interpolate the observation's approximate wavelength grid.
    wavelength_interp = RegularGridInterpolator(
        (y_grid, x_grid),
        values[:, :, 0],
        bounds_error=False
    )

    bandwidth_interp = RegularGridInterpolator(
        (y_grid, x_grid),
        values[:, :, 1],
        bounds_error=False
    )

    # Sample a regular grid of detector pixels.
    xs = np.linspace(50, 1989, 30).astype(int)
    ys = np.linspace(50, 1989, 30).astype(int)

    points = []

    for y in ys:
        for x in xs:
            points.append([y + 1, x + 1])

    points = np.array(points)

    approx_wave = wavelength_interp(points)
    approx_band = bandwidth_interp(points)

    exact_wave = cwave[
        points[:, 0].astype(int) - 1,
        points[:, 1].astype(int) - 1
    ]

    exact_band = cband[
        points[:, 0].astype(int) - 1,
        points[:, 1].astype(int) - 1
    ]

    wave_diff = exact_wave - approx_wave
    band_diff = exact_band - approx_band

    print("========== WAVELENGTH COMPARISON ==========")
    print("Number of sampled pixels:", len(points))

    print("\nWavelength difference (CWAVE - approximate):")
    print("Mean:", np.mean(wave_diff))
    print("Median:", np.median(wave_diff))
    print("Mean absolute difference:", np.mean(np.abs(wave_diff)))
    print("Maximum absolute difference:", np.max(np.abs(wave_diff)))
    print("95th percentile absolute difference:",
          np.percentile(np.abs(wave_diff), 95))

    print("\nBandwidth difference (CBAND - approximate):")
    print("Mean:", np.mean(band_diff))
    print("Median:", np.median(band_diff))
    print("Mean absolute difference:", np.mean(np.abs(band_diff)))
    print("Maximum absolute difference:", np.max(np.abs(band_diff)))

    print("\n========== OBSERVATION CALIBRATION KEYWORDS ==========")

    header = obs["IMAGE"].header

    for key in header:
        if any(word in key.upper() for word in [
            "CAL", "WCS", "SPEC", "REF"
        ]):
            print(f"{key}: {header[key]}")

    print("\nComparison complete.")
