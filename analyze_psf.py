
from astropy.io import fits
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

file_path = "data/raw/spherex_observation_may2026.fits"

with fits.open(file_path) as hdul:
    psf = hdul["PSF"].data.astype(float)

results = []

for i in range(psf.shape[0]):
    image = psf[i]

    total = np.sum(image)
    peak = np.max(image)

    central = image[40:61, 40:61]
    central_fraction = np.sum(central) / total if total != 0 else 0

    results.append({
        "plane": i,
        "peak_intensity": peak,
        "total_intensity": total,
        "central_fraction": central_fraction
    })

df = pd.DataFrame(results)

df.to_csv("data/raw/psf_analysis.csv", index=False)

print("\nPSF ANALYSIS")
print(df.describe())

print("\nFirst 10 planes:")
print(df.head(10).to_string(index=False))

plt.figure(figsize=(10, 5))
plt.plot(df["plane"], df["peak_intensity"])
plt.xlabel("PSF Plane")
plt.ylabel("Peak Intensity")
plt.title("PSF Peak Intensity Across 121 Planes")
plt.grid()
plt.savefig("data/raw/psf_peak_variation.png", dpi=200)
plt.show()

plt.figure(figsize=(10, 5))
plt.plot(df["plane"], df["central_fraction"])
plt.xlabel("PSF Plane")
plt.ylabel("Central Intensity Fraction")
plt.title("PSF Central Concentration Across 121 Planes")
plt.grid()
plt.savefig("data/raw/psf_central_variation.png", dpi=200)
plt.show()

print("\nSaved PSF analysis files!")
print("\nPSF PEAK INTENSITY VALUES")
print(df[["plane", "peak_intensity"]].to_string(index=False))

print("\nHIGHEST PEAK:")
print(df.loc[df["peak_intensity"].idxmax()])

print("\nLOWEST PEAK:")
print(df.loc[df["peak_intensity"].idxmin()])
print("\nLAST 10 PLANES:")
print(df.tail(10).to_string(index=False))

print("\nHIGHEST PEAK:")
print(df.loc[df["peak_intensity"].idxmax()].to_string())

print("\nLOWEST PEAK:")
print(df.loc[df["peak_intensity"].idxmin()].to_string())
print("\nLAST 10 PLANES:")
print(df.tail(10).to_string(index=False))

print("\nHIGHEST PEAK:")
print(df.loc[df["peak_intensity"].idxmax()].to_string())

print("\nLOWEST PEAK:")
print(df.loc[df["peak_intensity"].idxmin()].to_string())