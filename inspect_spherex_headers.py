
from astropy.io import fits

FILE = "data/raw/spherex_observation_may2026.fits"

with fits.open(FILE, memmap=True) as hdul:

    print("\n========== FITS EXTENSIONS ==========")
    hdul.info()

    print("\n========== OBSERVATION METADATA ==========")

    for i, hdu in enumerate(hdul):
        print(f"\nHDU {i}: {hdu.name}")

        for key in hdu.header:
            if any(word in key.upper() for word in
                   ["DETECTOR", "BAND", "OBS", "DATE",
                    "VERSION", "PROC", "ARRAY"]):
                print(f"{key}: {hdu.header[key]}")

    print("\n========== PSF ZONE COORDINATES ==========")

    psf = hdul["PSF"]
    header = psf.header

    print("PSF shape:", psf.data.shape)

    for i in list(range(1, 16)) + [21, 22, 23, 111, 112, 121]:
        x_key = f"XCTR_{i}"
        y_key = f"YCTR_{i}"

        if x_key in header and y_key in header:
            print(
                f"Zone {i:3d}: "
                f"X = {header[x_key]:.4f}, "
                f"Y = {header[y_key]:.4f}"
            )

    print("\n========== WCS-WAVE GRID ==========")

    wave = hdul["WCS-WAVE"].data[0]

    print("X control points:", wave["X"])
    print("Y control points:", wave["Y"])
    print("VALUES shape:", wave["VALUES"].shape)

print("\nInspection complete!")
