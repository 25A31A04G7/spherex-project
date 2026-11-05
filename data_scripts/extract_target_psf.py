from astropy.io import fits
from astropy.wcs import WCS
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

observations = [
    ("AUGUST", "site/data/august_1D3.fits",
     252.66330208911876, -17.490409029955288),

    ("DECEMBER", "site/data/december_1D3.fits",
     166.978132820704, 5.226415441651617)
]

for name, path, ra, dec in observations:

    with fits.open(path) as h:

        x, y = WCS(h["IMAGE"].header).world_to_pixel_values(ra, dec)

        psf = h["PSF"].data
        header = h["PSF"].header

        candidates = []

        for i in range(1, 122):

            cx = header.get(f"XCTR_{i}")
            cy = header.get(f"YCTR_{i}")

            if cx is not None and cy is not None:

                distance = np.hypot(cx - x, cy - y)

                candidates.append((distance, i, cx, cy))

        distance, index, cx, cy = min(candidates)

        model = psf[index - 1]

        print("\n" + "=" * 50)
        print(name)
        print("=" * 50)

        print("Target pixel:", round(float(x), 3),
              round(float(y), 3))

        print("Nearest PSF model:", index)
        print("PSF grid centre:", cx, cy)
        print("Distance to grid centre:", round(distance, 3))

        print("PSF shape:", model.shape)
        print("PSF minimum:", np.nanmin(model))
        print("PSF maximum:", np.nanmax(model))
        print("PSF sum:", np.nansum(model))

        fig, ax = plt.subplots(figsize=(7, 6))

        ax.imshow(model, origin="lower", cmap="inferno")

        ax.set_title(f"{name}: Nearest SPHEREx PSF Model")
        ax.set_xlabel("PSF X pixel")
        ax.set_ylabel("PSF Y pixel")

        output = f"site/data/{name.lower()}_target_psf.png"

        plt.savefig(output, dpi=160, bbox_inches="tight")
        plt.close()

        print("Saved:", output)

print("\nPSF EXTRACTION COMPLETE")