from astropy.io import fits
from astropy.wcs import WCS
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

observations = [
    ("AUGUST", "site/data/august_1D3.fits",
     "site/data/august_rebinned_psf.npy",
     252.66330208911876, -17.490409029955288),

    ("DECEMBER", "site/data/december_1D3.fits",
     "site/data/december_rebinned_psf.npy",
     166.978132820704, 5.226415441651617)
]

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

for row, (name, fits_path, psf_path, ra, dec) in enumerate(observations):

    with fits.open(fits_path) as h:
        image = h["IMAGE"].data
        x, y = WCS(h["IMAGE"].header).world_to_pixel_values(ra, dec)

        ix, iy = int(round(float(x))), int(round(float(y)))
        region = image[iy-5:iy+6, ix-5:ix+6]

    psf = np.load(psf_path)

    ax1 = axes[row, 0]
    im1 = ax1.imshow(region, origin="lower", cmap="inferno")
    ax1.set_title(f"{name}: Observed 11x11 Region")
    ax1.scatter(5, 5, marker="+", color="cyan", s=100)
    fig.colorbar(im1, ax=ax1)

    ax2 = axes[row, 1]
    im2 = ax2.imshow(psf, origin="lower", cmap="inferno")
    ax2.set_title(f"{name}: Rebinned PSF")
    fig.colorbar(im2, ax=ax2)

plt.tight_layout()
plt.savefig("site/data/psf_fit_preparation.png", dpi=160)
plt.close()

print("Saved: site/data/psf_fit_preparation.png")
print("PSF fitting preparation complete.")