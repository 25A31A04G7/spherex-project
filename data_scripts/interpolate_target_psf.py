from astropy.io import fits
from astropy.wcs import WCS
import numpy as np

observations = [
    ("AUGUST", "site/data/august_1D3.fits",
     252.66330208911876, -17.490409029955288),

    ("DECEMBER", "site/data/december_1D3.fits",
     166.978132820704, 5.226415441651617)
]

for name, path, ra, dec in observations:

    with fits.open(path) as h:

        psfs = h["PSF"].data.astype(float)
        header = h["PSF"].header

        x, y = WCS(h["IMAGE"].header).world_to_pixel_values(ra, dec)

        models = []

        for i in range(1, 122):
            cx = header[f"XCTR_{i}"]
            cy = header[f"YCTR_{i}"]

            models.append((i, cx, cy))

        xs = np.unique([m[1] for m in models])
        ys = np.unique([m[2] for m in models])

        xlo = xs[xs <= x].max()
        xhi = xs[xs >= x].min()
        ylo = ys[ys <= y].max()
        yhi = ys[ys >= y].min()

        def get_model(gx, gy):
            for i, cx, cy in models:
                if np.isclose(cx, gx) and np.isclose(cy, gy):
                    return i, psfs[i - 1]
            raise ValueError("PSF grid model not found")

        corners = [
            (xlo, ylo),
            (xhi, ylo),
            (xlo, yhi),
            (xhi, yhi)
        ]

        if xhi == xlo:
            wx = 0.0
        else:
            wx = (x - xlo) / (xhi - xlo)

        if yhi == ylo:
            wy = 0.0
        else:
            wy = (y - ylo) / (yhi - ylo)

        weights = [
            (1 - wx) * (1 - wy),
            wx * (1 - wy),
            (1 - wx) * wy,
            wx * wy
        ]

        result = np.zeros_like(psfs[0])

        print("\n" + "=" * 55)
        print(name)
        print("=" * 55)

        print("Target position:", x, y)

        for (gx, gy), weight in zip(corners, weights):

            index, model = get_model(gx, gy)

            result += weight * model

            print(
                f"Model {index}: "
                f"Grid=({gx:.2f}, {gy:.2f}), "
                f"Weight={weight:.5f}"
            )

        result /= result.sum()

        print("Interpolated PSF shape:", result.shape)
        print("Interpolated PSF flux:", result.sum())

        output = f"site/data/{name.lower()}_interpolated_psf.npy"

        np.save(output, result)

        print("Saved:", output)

print("\nSPATIAL PSF INTERPOLATION COMPLETE")