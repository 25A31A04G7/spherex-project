from pathlib import Path
from astropy.table import Table

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE = ROOT / "site" / "data" / "obscore_3I_Atlas.vot"

observations = Table.read(CATALOGUE, format="votable")

targets = {
    "2025-08-01": None,
    "2025-12-14": None,
}

for row in observations:
    title = str(row["obs_title"])
    detector = str(row["spherex_detector"])

    if detector != "D3":
        continue

    for date in targets:
        if date in title and targets[date] is None:
            targets[date] = row

for date, row in targets.items():
    print("\n" + "=" * 65)
    print("DATE:", date)

    if row is None:
        print("No matching D3 observation found.")
        continue

    print("Observation:", row["obs_title"])
    print("DataLink URL:", row["access_url"])
    print("Comet RA:", row["comet_ra"])
    print("Comet Dec:", row["comet_dec"])

print("\nInspection complete.")