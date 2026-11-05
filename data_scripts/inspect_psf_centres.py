import numpy as np

files = [
    ("AUGUST", "site/data/august_rebinned_psf.npy"),
    ("DECEMBER", "site/data/december_rebinned_psf.npy")
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
    print("Weighted centre X:", round(cx, 4))
    print("Weighted centre Y:", round(cy, 4))
    print("Geometric centre: 4.5, 4.5")

print("\nPSF CENTRE INVESTIGATION COMPLETE")