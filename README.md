# SPHERESCAPE

**Beyond what the eyes can see.** SPHERESCAPE is an exploration platform by team **ASTRAVIA** for the **NASA Space Apps Challenge 2026**. It brings real infrared observations from NASA's [SPHEREx](https://www.jpl.nasa.gov/missions/spherex) sky survey to everyone.

The repository has two parts:

| Part | Where | What it does |
|---|---|---|
| **Web app** | `backend/`, `frontend/` | A Flask server and landing page. It shows a processed SPHEREx observation and has API routes that search the NASA/IPAC (IRSA) archive by sky position. |
| **Science scripts** | repo root (`*.py`) | Standalone analysis of one SPHEREx Level 2 image: source detection, quality flags, PSF behaviour across the detector, and wavelength calibration. |

---

## 1. Setup

You need **Python 3.10–3.13**. Tested on 3.12.

> On a very new Python such as 3.15, `pip install` fails because PyYAML (an astropy dependency) has no prebuilt wheel yet and needs a C compiler. If you have [uv](https://docs.astral.sh/uv/), it can fetch a supported Python for you: `uv venv -p 3.12 --seed venv`. (`--seed` installs `pip` into the environment so the steps below work.)

```bash
git clone https://github.com/anandjyotsna1711-cmd/SPHERESCAPE.git
cd SPHERESCAPE
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows (PowerShell)
venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

> Run everything from the **repo root**. The scripts use relative paths such as `data/raw/...`.

---

## 2. Get the data

FITS files are large (~70 MB each), so they are **not** in git (`data/raw/` is gitignored). Download them into `data/raw/`:

| File | Used by | How to get it |
|---|---|---|
| `data/raw/spherex_observation_may2026.fits` | All root-level science scripts | `python download_spherex.py` (observation `2026W20_2A_0191_4`, detector 2) |
| `data/raw/spectral_wcs_D2.fits` | Wavelength-calibration scripts | `python download_spectral_wcs.py` |
| `data/raw/spherex_observation.fits` | Web app's `/api/fits/summary` and `backend/visualize_fits.py` | Manual download, see below |

**Web app observation** (`2025W43_1A_0516_1`). The archive has this observation for several detectors (D2, D4, D5, D6). Ask the team which one was used for the first-light image. Detector 2 matches the rest of the project:

```
https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/qr2/level2/2025W43_1A/l2b-v20-2025-299/2/level2_2025W43_1A_0516_1D2_spx_l2b-v20-2025-299.fits
```

Save it as `data/raw/spherex_observation.fits`.

> The homepage works without this file because `data/processed/spherex_first_light.png` is already committed. Only `/api/fits/summary` needs it.

---

## 3. Run the web app

```bash
python backend/app.py
```

Open http://127.0.0.1:5000.

| Route | Description |
|---|---|
| `/` | Landing page |
| `/first-light` | Processed observation image (PNG) |
| `/api/observations?ra=<deg>&dec=<deg>&radius=<arcsec>&limit=<n>` | Searches the IRSA SPHEREx archive (`spherex_qr2`) at a sky position |
| `/api/observations/matched?ra=...&dec=...` | The same search, grouped into observation epochs by date |
| `/api/fits/summary` | Pixel stats, metadata, WCS centre, flags and variance for the local FITS file |

Example: `http://127.0.0.1:5000/api/observations/matched?ra=10.68&dec=41.27&radius=10`

The archive search needs internet access and can take up to a minute.

---

## 4. Run the science pipeline

Many scripts call `plt.show()`. Close the plot window for the script to finish. Outputs go to `data/raw/`, and the final figures go to `results/figures/`.

**Source detection**
1. `detect_sources.py` finds peaks above SNR 5 after masking bad quality flags. It writes `source_candidates.csv`.
2. `inspect_candidate_cutouts.py` writes `results/figures/top_candidate_cutouts.png`.
3. `audit_source_candidates.py` summarises the candidate catalogue.

**PSF vs wavelength.** SPHEREx's filter wavelength changes across the detector, so each of the 121 PSF zones sees a different wavelength.
1. `analyze_psf.py` measures peak intensity and central energy fraction for each PSF zone. It writes `psf_analysis.csv`.
2. `map_psf_wavelength.py` maps each zone to a wavelength using `WCS-WAVE`. It writes `psf_wavelength_mapping.csv`.
3. `map_psf_calibrated.py` remaps using the calibration file `spectral_wcs_D2.fits`. It writes `psf_calibrated_mapping.csv`.
4. `plot_calibrated_maps.py` and `plot_combined_psf.py` write the figures in `results/figures/`.
5. `validate_psf_correlations.py` and `check_spatial_residuals.py` test whether the correlations survive after removing position-on-detector trends.

**Inspection helpers** (run any time after downloading the data): `inspect_spherex_headers.py`, `inspect_flags.py`, `decode_flags.py`, `sky_coordinates.py`, `visualize_spherex.py`, `validate_spectral_wcs.py`, `compare_wavelength_maps.py`.

---

## 5. Project structure

```
backend/
  app.py                  Flask server and API routes
  nasa_api.py             IRSA SIA archive search
  observation_matcher.py  Groups archive products into observation epochs
  fits_processor.py       FITS summary for /api/fits/summary
  footprint_checker.py    Sky footprint (corner RA/Dec) of the image
  visualize_fits.py       Builds data/processed/spherex_first_light.png
frontend/templates/
  index.html              Landing page
data/processed/           Committed images served by the app
results/figures/          Committed analysis figures
*.py                      Science scripts (see section 4)
```

---

## 6. Roadmap

The landing page lists four modules, all **in development**:

- **Cosmic Explorer**: search and browse observations by sky position. `/api/observations/matched` already exists, but the front end doesn't call it yet.
- **Time Traveller**: compare observations from different dates (uses the epoch grouping).
- **Change Detector**: highlight differences between aligned observations.
- **Spectral Explorer**: show how each wavelength reveals different features.

Known issues:
- The web app and the scripts use two different observations (see section 2).
- The source detector doesn't mask the `TRANSIENT` or `OUTLIER` flags and has no minimum source size. Many top candidates are single-pixel spikes and may be cosmic rays or hot pixels.

---

*Imagery credit: NASA / JPL-Caltech. SPHEREx data from NASA/IPAC Infrared Science Archive (IRSA).*
