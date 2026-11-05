import numpy as np

files = [
    ("AUGUST", "site/data/august_interpolated_psf.npy"),
    ("DECEMBER", "site/data/december_interpolated_psf.npy")
]

for name, path in files:

    psf = np.load(path)

    y, x = np.indices(psf.shape)

    total = psf.sum()

    cx = np.sum(x * psf) / total
    cy = np.sum(y * psf) / total

    peak_y, peak_x = np.unravel_index(
        np.argmax(psf), psf.shape
    )

    print("\n" + "=" * 45)
    print(name)
    print("=" * 45)

    print("Shape:", psf.shape)
    print("Flux:", total)
    print("Peak pixel:", peak_x, peak_y)
    print("Weighted centre X:", cx)
    print("Weighted centre Y:", cy)
    print("Reference centre: 50, 50")
    print("Minimum:", psf.min())
    print("Maximum:", psf.max())

print("\nINTERPOLATED PSF VERIFICATION COMPLETE")