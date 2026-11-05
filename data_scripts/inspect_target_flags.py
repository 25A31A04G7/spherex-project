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
        image = h["IMAGE"].data
        flags = h["FLAGS"].data

        wcs = WCS(h["IMAGE"].header)
        x, y = wcs.world_to_pixel_values(ra, dec)

        ix = int(round(float(x)))
        iy = int(round(float(y)))

        flag = int(flags[iy, ix])

        region = flags[iy-10:iy+11, ix-10:ix+11]

        print("\n", name)
        print("=" * 45)
        print("Centre flag value:", flag)
        print("Known-source flag:", bool(flag & (1 << 21)))
        print("Transient flag:", bool(flag & (1 << 0)))
        print("Overflow flag:", bool(flag & (1 << 1)))
        print("SUR error flag:", bool(flag & (1 << 2)))
        print("Persistent flag:", bool(flag & (1 << 17)))
        print("Outlier flag:", bool(flag & (1 << 19)))
        print("Source-flagged pixels in region:",
              int(np.count_nonzero(region & (1 << 21))))
        print("Transient-flagged pixels in region:",
              int(np.count_nonzero(region & (1 << 0))))