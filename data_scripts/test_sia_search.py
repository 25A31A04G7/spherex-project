from astroquery.ipac.irsa import Irsa
from astropy import units as u

RA = 252.66330208911876
DEC = -17.490409029955288

print("SPHEREx SIA2 Search")
print("-" * 45)
print("Searching around the August 1 comet position...")
print("Collection: spherex_qr2")

try:
    results = Irsa.query_sia(
        pos=(RA, DEC, 0.1),
        collection="spherex_qr2",
        max_records=10,
    )

    print("\nSearch completed.")
    print("Number of returned records:", len(results))

    print("\nAvailable columns:")
    print(results.colnames)

    if len(results) > 0:
        print("\nFirst returned records:")
        print(results[:5])

        output_file = "site/data/sia_search_results.csv"

        results.write(
            output_file,
            format="csv",
            overwrite=True,
        )

        print("\nResults saved to:", output_file)
    else:
        print("\nNo matching images returned.")

except Exception as error:
    print("\nSIA2 SEARCH FAILED")
    print(type(error).__name__, error)