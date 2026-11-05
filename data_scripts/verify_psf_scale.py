from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales
import numpy as np

files = [
    ("AUGUST", "site/data/august_1D3.fits"),
    ("DECEMBER", "site/data/december_1D3.fits")
]

for name, path in files:

    print("\n" + "=" * 55)
    print(name)
    print("=" * 55)

    with fits.open(path) as h:

        image_header = h["IMAGE"].header
        psf_header = h["PSF"].header
        psf = h["PSF"].data

        # Science image pixel scale
        wcs = WCS(image_header)
        scales = proj_plane_pixel_scales(wcs) * 3600

        image_scale = np.mean(scales)

        print("\nSCIENCE IMAGE")
        print("Pixel scale X:", scales[0], "arcsec")
        print("Pixel scale Y:", scales[1], "arcsec")
        print("Mean pixel scale:", image_scale, "arcsec")

        print("\nPSF MODEL")
        print("PSF dimensions:", psf.shape)

        print("\nPSF HEADER")
        for key in psf_header:
            if key not in ("COMMENT", "HISTORY"):
                print(f"{key}: {psf_header[key]}")

        print("\nPOSSIBLE SAMPLING RATIOS")

        for scale in [0.615, 0.62, 0.6]:
            print(
                f"{scale} arcsec PSF sampling -> "
                f"{image_scale / scale:.3f} samples per image pixel"
            )

print("\nSCALE VERIFICATION COMPLETE")