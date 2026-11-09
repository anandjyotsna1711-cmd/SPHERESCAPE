
from astropy.io import fits
import pandas as pd
import os

FILE = "data/raw/spherex_observation_may2026.fits"

print("===== SPHERESCAPE SPECTRAL INSPECTION =====")

with fits.open(FILE) as hdul:

    # Inspect wavelength extension
    wave = hdul["WCS-WAVE"]

    print("\n--- WCS-WAVE HEADER ---")
    print(wave.header)

    print("\n--- WCS-WAVE STRUCTURE ---")

    print("HDU type:", type(wave).__name__)
    print("Data shape:", wave.data.shape if wave.data is not None else None)

    if hasattr(wave, "columns") and wave.columns:

        for column in wave.columns:
            print(
                "Column:",
                column.name,
                "| Format:",
                column.format,
                "| Unit:",
                column.unit
            )

        for name in wave.columns.names:
            values = wave.data[name]

            print("\nColumn:", name)
            print("Shape:", values.shape)
            print("First values:", values[0])

    # Inspect PSF
    psf = hdul["PSF"]

    print("\n--- PSF INFORMATION ---")
    print("PSF shape:", psf.data.shape)
    print("PSF dtype:", psf.data.dtype)
    print("PSF minimum:", psf.data.min())
    print("PSF maximum:", psf.data.max())

    print("\n--- IMAGE HEADER WAVELENGTH REFERENCES ---")

    image_header = hdul["IMAGE"].header

    for key in image_header:
        if "WAVE" in key or "BAND" in key:
            print(key, "=", image_header[key])


# Inspect our candidate catalogue
csv_file = "data/raw/source_candidates.csv"

print("\n--- CANDIDATE CATALOGUE ---")

if os.path.exists(csv_file):

    df = pd.read_csv(csv_file)

    print("Total candidates:", len(df))
    print("\nSNR statistics:")
    print(df["snr"].describe())

    print("\nTop 10 candidates:")
    print(
        df[
            ["x", "y", "intensity", "snr", "ra", "dec", "flag_names"]
        ].head(10).to_string(index=False)
    )

else:
    print("Candidate catalogue not found!")

print("\n===== INSPECTION COMPLETE =====")
