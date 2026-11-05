from astropy.io import fits
from astropy.wcs import WCS
import numpy as np

observations = [
    ("AUGUST", "site/data/august_1D3.fits",
     252.66330208911876, -17.490409029955288),

    ("DECEMBER", "site/data/december_1D3.fits",
     166.978132820704, 5.226415441651617)
]

bad_bits = {
    1: "Overflow",
    2: "Surface error",
    6: "Nonfunctional",
    9: "Missing data",
    10: "Hot pixel",
    11: "Cold pixel",
    15: "Nonlinear",
    17: "Persistence",
    19: "Outlier"
}

print("APERTURE EXCLUSION INVESTIGATION")
print("=" * 55)

for name, path, ra, dec in observations:

    with fits.open(path) as h:

        image = h["IMAGE"].data
        variance = h["VARIANCE"].data
        flags = h["FLAGS"].data

        wcs = WCS(h["IMAGE"].header)
        x, y = wcs.world_to_pixel_values(ra, dec)

        ix = int(round(float(x)))
        iy = int(round(float(y)))

        y0, y1 = iy - 7, iy + 8
        x0, x1 = ix - 7, ix + 8

        data = image[y0:y1, x0:x1]
        var = variance[y0:y1, x0:x1]
        flag = flags[y0:y1, x0:x1]

        yy, xx = np.indices(data.shape)

        distance = np.hypot(
            xx + x0 - float(x),
            yy + y0 - float(y)
        )

        aperture = distance <= 2.0

        print(f"\n{name}")
        print("-" * 45)

        print("Total aperture pixels:",
              int(np.count_nonzero(aperture)))

        print("Non-finite image pixels:",
              int(np.count_nonzero(aperture & ~np.isfinite(data))))

        print("Non-finite variance pixels:",
              int(np.count_nonzero(aperture & ~np.isfinite(var))))

        print("Non-positive variance pixels:",
              int(np.count_nonzero(aperture & (var <= 0))))

        print("\nIndividual quality flags:")

        for bit, label in bad_bits.items():

            count = np.count_nonzero(
                aperture & ((flag & (1 << bit)) != 0)
            )

            print(f"{label}: {count}")

        print("\nPixel-by-pixel details:")

        for py, px in zip(*np.where(aperture)):

            value = int(flag[py, px])

            print(
                f"Pixel ({px+x0}, {py+y0})"
                f" | Brightness: {data[py, px]:.4f}"
                f" | Variance: {var[py, px]:.6f}"
                f" | Flags: {value}"
            )

print("\n" + "=" * 55)
print("INVESTIGATION COMPLETE")