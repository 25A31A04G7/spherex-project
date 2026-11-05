from pathlib import Path
from collections import Counter
import re

from astropy.table import Table

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CATALOGUE_FILE = (
    PROJECT_ROOT / "site" / "data" / "obscore_3I_Atlas.vot"
)


def main():
    observations = Table.read(
        CATALOGUE_FILE,
        format="votable"
    )

    date_counts = Counter()
    detector_counts = Counter()
    target_counts = Counter()
    moving_counts = Counter()

    for row in observations:

        title = str(row["obs_title"])

        match = re.search(
            r"\((\d{4}-\d{2}-\d{2})T",
            title
        )

        if match:
            date_counts[match.group(1)] += 1

        detector_counts[
            str(row["spherex_detector"])
        ] += 1

        target_counts[
            str(row["target_name"])
        ] += 1

        moving_counts[
            str(row["target_moving"])
        ] += 1

    print("=" * 55)
    print("SPHEREx 3I/ATLAS CATALOGUE SUMMARY")
    print("=" * 55)

    print(f"\nTotal observations: {len(observations)}")

    print("\nOBSERVATIONS BY DATE")
    print("-" * 35)

    for date, count in sorted(date_counts.items()):
        print(f"{date}: {count} observations")

    print("\nOBSERVATIONS BY DETECTOR")
    print("-" * 35)

    for detector, count in sorted(detector_counts.items()):
        print(f"{detector}: {count} observations")

    print("\nTARGET NAMES")
    print("-" * 35)

    for target, count in target_counts.items():
        print(f"{target}: {count}")

    print("\nMOVING TARGET FLAG")
    print("-" * 35)

    for value, count in moving_counts.items():
        print(f"{value}: {count}")

    print("\n" + "=" * 55)
    print("SUCCESS: Catalogue summary generated.")
    print("=" * 55)


if __name__ == "__main__":
    main()