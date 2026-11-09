
import numpy as np
from astropy.io import fits

cal_file = "data/raw/spectral_wcs_D2.fits"
obs_file = "data/raw/spherex_observation_may2026.fits"

with fits.open(cal_file) as cal, fits.open(obs_file) as obs:

    print("========== CALIBRATION PROVENANCE ==========")

    for key, value in cal[0].header.items():
        if key not in ["", "COMMENT", "HISTORY"]:
            print(f"{key}: {value}")

    print("\n========== CWAVE HEADER ==========")

    for key, value in cal["CWAVE"].header.items():
        if key not in ["", "COMMENT", "HISTORY"]:
            print(f"{key}: {value}")

    print("\n========== CALIBRATION MAP STATISTICS ==========")

    for name in ["CWAVE", "CBAND"]:
        data = np.asarray(cal[name].data, dtype=float)
        valid = data[np.isfinite(data)]

        print(f"\n{name}")
        print("Shape:", data.shape)
        print("Valid pixels:", len(valid))
        print("Invalid pixels:", np.size(data) - len(valid))
        print("Minimum:", np.min(valid))
        print("Maximum:", np.max(valid))
        print("Mean:", np.mean(valid))
        print("Median:", np.median(valid))
        print("Standard deviation:", np.std(valid))

    print("\n========== OBSERVATION COMPARISON ==========")

    print("Observation version:", obs[0].header.get("VERSION"))
    print("Observation date:", obs["IMAGE"].header.get("DATE-OBS"))
    print("Observation detector:", obs["IMAGE"].header.get("DETECTOR"))
    print("Observation ID:", obs["IMAGE"].header.get("OBSID"))

    print("\n========== CALIBRATION / OBSERVATION MATCH ==========")

    print("Calibration detector:", cal["CWAVE"].header.get("DETECTOR"))
    print("Calibration date:", cal[0].header.get("DATE"))
    print("Calibration dimensions:", cal["CWAVE"].data.shape)
    print("Observation dimensions:", obs["IMAGE"].data.shape)

    print("\n========== SAMPLE PIXEL VALUES ==========")

    positions = [
        (100, 100),
        (500, 500),
        (1020, 1020),
        (1500, 1500),
        (1900, 1900)
    ]

    for y, x in positions:
        wavelength = cal["CWAVE"].data[y, x]
        bandwidth = cal["CBAND"].data[y, x]

        print(
            f"Pixel ({x}, {y}): "
            f"CWAVE={wavelength:.6f}, "
            f"CBAND={bandwidth:.6f}"
        )
