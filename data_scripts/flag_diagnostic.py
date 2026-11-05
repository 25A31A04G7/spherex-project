from astropy.io import fits
from astropy.wcs import WCS
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

observations = [
    ("AUGUST", "site/data/august_1D3.fits",
     252.66330208911876, -17.490409029955288),

    ("DECEMBER", "site/data/december_1D3.fits",
     166.978132820704, 5.226415441651617)
]

for name, path, ra, dec in observations:

    with fits.open(path) as h:

        image = h["IMAGE"].data
        flags = h["FLAGS"].data

        x, y = WCS(h["IMAGE"].header).world_to_pixel_values(ra, dec)

        ix = int(round(float(x)))
        iy = int(round(float(y)))

        region = image[iy-10:iy+11, ix-10:ix+11]
        flag_region = flags[iy-10:iy+11, ix-10:ix+11]

        yy, xx = np.indices(region.shape)

        distance = np.hypot(
            xx + ix - 10 - x,
            yy + iy - 10 - y
        )

        aperture = distance <= 2.0

        outlier = (flag_region & (1 << 19)) != 0
        persistence = (flag_region & (1 << 17)) != 0
        known_source = (flag_region & (1 << 21)) != 0

        fig, ax = plt.subplots(figsize=(8, 8))

        ax.imshow(region, origin="lower", cmap="inferno")

        ax.scatter(
            xx[aperture], yy[aperture],
            facecolors="none", edgecolors="cyan",
            s=150, label="Source aperture"
        )

        ax.scatter(
            xx[outlier], yy[outlier],
            marker="x", color="red",
            s=100, label="Outlier"
        )

        ax.scatter(
            xx[persistence], yy[persistence],
            marker="s", facecolors="none",
            edgecolors="yellow", s=130,
            label="Persistence"
        )

        ax.scatter(
            10, 10, marker="+",
            color="lime", s=180,
            label="Catalogue position"
        )

        ax.set_title(f"{name}: Target and Quality Flags")
        ax.set_xlabel("Pixel X")
        ax.set_ylabel("Pixel Y")
        ax.legend()

        output = f"site/data/{name.lower()}_flag_diagnostic.png"

        plt.savefig(output, dpi=160, bbox_inches="tight")
        plt.close()

        print("Saved:", output)

print("Diagnostic images created.")