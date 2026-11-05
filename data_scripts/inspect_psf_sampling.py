from astropy.io import fits
import numpy as np

files = [
    ("AUGUST", "site/data/august_1D3.fits", 48),
    ("DECEMBER", "site/data/december_1D3.fits", 114)
]

for name, path, index in files:

    with fits.open(path) as h:

        psf = h["PSF"].data[index - 1]
        header = h["PSF"].header

        print("\n" + "=" * 50)
        print(name)
        print("=" * 50)

        print("Original PSF shape:", psf.shape)

        for key in header:
            if any(word in key.upper() for word in
                   ["OVERSAMP", "PIX", "SCALE", "CENT", "XCTR", "YCTR"]):
                print(f"{key}: {header[key]}")

        y, x = np.indices(psf.shape)
        total = np.nansum(psf)

        cx = np.nansum(x * psf) / total
        cy = np.nansum(y * psf) / total

        print("Original PSF weighted centre X:", cx)
        print("Original PSF weighted centre Y:", cy)
        print("Original PSF peak:", np.unravel_index(
            np.nanargmax(psf), psf.shape
        ))

print("\nORIGINAL PSF SAMPLING INSPECTION COMPLETE")