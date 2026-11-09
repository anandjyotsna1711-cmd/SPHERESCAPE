
from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np

file_path = "data/raw/spherex_observation_may2026.fits"

with fits.open(file_path) as hdul:
    psf = hdul["PSF"].data.astype(float)

print("PSF shape:", psf.shape)

planes = [0, 30, 60, 90, 120]

fig, axes = plt.subplots(1, 5, figsize=(18, 4))

for ax, index in zip(axes, planes):
    image = psf[index]

    ax.imshow(image, origin="lower", cmap="inferno")
    ax.set_title(f"PSF Plane {index}")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")

plt.suptitle("SPHEREx Point Spread Function Across Wavelength Planes")
plt.tight_layout()

plt.savefig("data/raw/psf_comparison.png", dpi=200)
plt.show()

print("\nPSF plane statistics:")

for index in planes:
    image = psf[index]

    print(
        f"Plane {index}: "
        f"Min={np.min(image):.8f}, "
        f"Max={np.max(image):.8f}, "
        f"Mean={np.mean(image):.8f}"
    )
