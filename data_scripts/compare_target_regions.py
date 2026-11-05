from astropy.io import fits
from astropy.wcs import WCS
import numpy as np

observations = [
    (
        "AUGUST",
        "site/data/august_1D3.fits",
        252.66330208911876,
        -17.490409029955288
    ),
    (
        "DECEMBER",
        "site/data/december_1D3.fits",
        166.978132820704,
        5.226415441651617
    )
]

print("SPHEREx TARGET REGION COMPARISON")
print("=" * 60)

for name, path, ra, dec in observations:

    with fits.open(path) as h:

        image = h["IMAGE"].data
        variance = h["VARIANCE"].data
        flags = h["FLAGS"].data
        header = h["IMAGE"].header

        # Convert catalogue coordinates to image pixels
        wcs = WCS(header)
        x, y = wcs.world_to_pixel_values(ra, dec)

        ix = int(round(float(x)))
        iy = int(round(float(y)))

        # Check image boundaries
        if not (0 <= ix < image.shape[1] and
                0 <= iy < image.shape[0]):
            print(f"\n{name}: Target outside image")
            continue

        # Extract 21x21 target region
        region = image[iy-10:iy+11, ix-10:ix+11]

        # Central pixel measurements
        centre_brightness = float(image[iy, ix])
        centre_variance = float(variance[iy, ix])

        if centre_variance > 0:
            centre_noise = float(np.sqrt(centre_variance))
            centre_snr = centre_brightness / centre_noise
        else:
            centre_noise = float("nan")
            centre_snr = float("nan")

        # Find brightest pixel in region
        peak_index = np.unravel_index(
            np.nanargmax(region),
            region.shape
        )

        peak_y = iy - 10 + peak_index[0]
        peak_x = ix - 10 + peak_index[1]

        peak_brightness = float(image[peak_y, peak_x])

        peak_distance = float(
            np.hypot(peak_x - x, peak_y - y)
        )

        # Central pixel quality flags
        centre_flag = int(flags[iy, ix])

        print(f"\n{name}")
        print("-" * 45)

        print("Observation ID:", header.get("OBSID"))
        print("Date:", header.get("DATE-OBS"))
        print("FINAST:", header.get("FINAST"))

        print("\nCENTRAL PIXEL")
        print("Catalogue pixel X:", round(float(x), 3))
        print("Catalogue pixel Y:", round(float(y), 3))
        print("Brightness:", centre_brightness)
        print("Variance:", centre_variance)
        print("Noise:", centre_noise)
        print("SNR:", centre_snr)

        print("\nTARGET REGION")
        print("Median brightness:", float(np.nanmedian(region)))
        print("Maximum brightness:", peak_brightness)
        print("Peak distance:", round(peak_distance, 2), "pixels")

        print("\nQUALITY FLAGS")
        print("Flag value:", centre_flag)
        print("Known source:", bool(centre_flag & (1 << 21)))
        print("Transient:", bool(centre_flag & (1 << 0)))
        print("Overflow:", bool(centre_flag & (1 << 1)))
        print("SUR error:", bool(centre_flag & (1 << 2)))
        print("Persistent:", bool(centre_flag & (1 << 17)))
        print("Outlier:", bool(centre_flag & (1 << 19)))

print("\n" + "=" * 60)
print("COMPARISON COMPLETE")