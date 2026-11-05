from astropy.io import fits
import numpy as np

files = [
    ("AUGUST", "site/data/august_1D3.fits"),
    ("DECEMBER", "site/data/december_1D3.fits")
]

for name, path in files:

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    with fits.open(path) as h:

        flags_header = h["FLAGS"].header
        psf_header = h["PSF"].header
        psf = h["PSF"].data

        print("\nQUALITY FLAG DEFINITIONS")
        print("-" * 40)

        for key in flags_header:
            if key.startswith("MP_"):
                print(f"{key}: {flags_header[key]}")

        print("\nPSF EXTENSION")
        print("-" * 40)

        print("Shape:", psf.shape)
        print("Data type:", psf.dtype)
        print("Finite values:", np.isfinite(psf).sum())
        print("Minimum:", np.nanmin(psf))
        print("Maximum:", np.nanmax(psf))
        print("Mean:", np.nanmean(psf))

        print("\nPSF HEADER")
        print("-" * 40)

        for key in psf_header:
            if key not in ("COMMENT", "HISTORY"):
                print(f"{key}: {psf_header[key]}")

print("\nINSPECTION COMPLETE")