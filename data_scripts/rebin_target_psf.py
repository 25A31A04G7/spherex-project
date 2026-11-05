from astropy.io import fits
import numpy as np

observations = [
    ("AUGUST", "site/data/august_1D3.fits", 48),
    ("DECEMBER", "site/data/december_1D3.fits", 114)
]

for name, path, index in observations:

    with fits.open(path) as h:

        psf = h["PSF"].data[index - 1].astype(float)
        header = h["PSF"].header

        oversampling = int(header["OVERSAMP"])

        print("\n" + "=" * 50)
        print(name)
        print("=" * 50)

        print("Original shape:", psf.shape)
        print("Oversampling:", oversampling)
        print("Original flux:", psf.sum())

        # Keep the central 100 x 100 samples.
        # This is a preliminary centred-grid approximation.
        start = (psf.shape[0] - 100) // 2

        cropped = psf[
            start:start + 100,
            start:start + 100
        ]

        rebinned = cropped.reshape(
            10, oversampling,
            10, oversampling
        ).sum(axis=(1, 3))

        rebinned /= rebinned.sum()

        print("Rebinned shape:", rebinned.shape)
        print("Rebinned flux:", rebinned.sum())
        print("Peak value:", rebinned.max())

        output = f"site/data/{name.lower()}_rebinned_psf.npy"

        np.save(output, rebinned)

        print("Saved:", output)

print("\nPRELIMINARY PSF REBINNING COMPLETE")