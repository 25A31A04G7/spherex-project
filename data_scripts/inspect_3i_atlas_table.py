from pathlib import Path
from astropy.table import Table

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CATALOGUE_FILE = (
    PROJECT_ROOT / "site" / "data" / "obscore_3I_Atlas.vot"
)


def main():
    print("SPHEREx 3I/ATLAS Catalogue Inspector")
    print("-" * 45)

    if not CATALOGUE_FILE.exists():
        raise FileNotFoundError(
            f"Catalogue not found: {CATALOGUE_FILE}"
        )

    print("Reading downloaded catalogue...")

    observations = Table.read(
        CATALOGUE_FILE,
        format="votable"
    )

    print(f"\nTotal observations: {len(observations)}")

    print("\nAvailable columns:")
    print(", ".join(observations.colnames))

    required_columns = [
        "obs_title",
        "spherex_detector",
        "comet_ra",
        "comet_dec",
        "em_min",
        "em_max",
        "access_estsize",
    ]

    missing = [
        column for column in required_columns
        if column not in observations.colnames
    ]

    if missing:
        raise ValueError(
            f"Missing expected columns: {missing}"
        )

    print("\nFirst 10 observations")
    print("=" * 60)

    for row in observations[:10]:

        wavelength_min = float(row["em_min"]) * 1_000_000
        wavelength_max = float(row["em_max"]) * 1_000_000

        size_kb = float(row["access_estsize"])

        print(f"\nObservation: {row['obs_title']}")
        print(f"Detector: {row['spherex_detector']}")

        print(
            f"Wavelength: {wavelength_min:.3f} - "
            f"{wavelength_max:.3f} microns"
        )

        print(f"Comet RA: {row['comet_ra']}")
        print(f"Comet Dec: {row['comet_dec']}")

        print(f"Estimated file size: {size_kb:.0f} KB")

    print("\n" + "=" * 60)
    print("SUCCESS: Catalogue read successfully!")
    print("No FITS images downloaded.")


if __name__ == "__main__":
    main()
