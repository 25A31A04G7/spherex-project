from astropy.io import fits
import numpy as np

observations = [
    ("AUGUST", "site/data/august_1D3.fits", 48),
    ("DECEMBER", "site/data/december_1D3.fits", 114)
]

for name, path, index in observations:

    with fits.open(path) as h:

        psf = h["PSF"].data[index - 1].astype(float)

        cropped = psf[:100, :100]

        original_flux = psf.sum()
        retained_flux = cropped.sum()
        lost_flux = original_flux - retained_flux

        print("\n", name)
        print("-" * 40)
        print("Original flux:", original_flux)
        print("Retained flux:", retained_flux)
        print("Discarded flux:", lost_flux)
        print("Discarded percentage:",
              lost_flux / original_flux * 100)

print("\nREBINNING LOSS CHECK COMPLETE")