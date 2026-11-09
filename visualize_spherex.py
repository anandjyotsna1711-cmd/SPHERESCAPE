
from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np

# Load SPHEREx observation
file_path = "data/raw/spherex_observation_may2026.fits"

with fits.open(file_path) as hdul:
    image = hdul["IMAGE"].data.astype(np.float32)

# Remove invalid values
image = np.nan_to_num(image, nan=0.0, posinf=0.0, neginf=0.0)

# Display image statistics
print("\n===== SPHEREx IMAGE ANALYSIS =====")
print("Shape:", image.shape)
print("Minimum:", np.min(image))
print("Maximum:", np.max(image))
print("Mean:", np.mean(image))
print("Standard deviation:", np.std(image))

percentiles = np.percentile(image, [1, 25, 50, 75, 99])

print("\nPercentiles:")
print("1%:", percentiles[0])
print("25%:", percentiles[1])
print("50%:", percentiles[2])
print("75%:", percentiles[3])
print("99%:", percentiles[4])

# Improve image contrast
vmin, vmax = percentiles[0], percentiles[4]

if vmax <= vmin:
    print("\nWARNING: Image has no useful intensity range.")
else:
    # Plot original and enhanced images
    fig, axes = plt.subplots(1, 2, figsize=(15, 7))

    axes[0].imshow(image, cmap="inferno", origin="lower")
    axes[0].set_title("Original SPHEREx Observation")
    axes[0].set_xlabel("Pixel X")
    axes[0].set_ylabel("Pixel Y")

    axes[1].imshow(
        image,
        cmap="inferno",
        origin="lower",
        vmin=vmin,
        vmax=vmax
    )
    axes[1].set_title("Contrast-Enhanced SPHEREx Observation")
    axes[1].set_xlabel("Pixel X")
    axes[1].set_ylabel("Pixel Y")

    plt.tight_layout()

    plt.savefig(
        "data/raw/spherex_enhanced.png",
        dpi=200,
        bbox_inches="tight"
    )

    plt.show()

    print("\nEnhanced image saved successfully!")
