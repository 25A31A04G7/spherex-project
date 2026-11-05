import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

files = [
    ("AUGUST", "site/data/august_rebinned_psf.npy"),
    ("DECEMBER", "site/data/december_rebinned_psf.npy")
]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

for ax, (name, path) in zip(axes, files):

    psf = np.load(path)

    image = ax.imshow(
        psf,
        origin="lower",
        cmap="inferno",
        interpolation="nearest"
    )

    ax.set_title(f"{name}: Rebinned PSF")
    ax.set_xlabel("Science pixel X")
    ax.set_ylabel("Science pixel Y")

    fig.colorbar(image, ax=ax, fraction=0.046)

plt.tight_layout()
plt.savefig(
    "site/data/rebinned_psf_comparison.png",
    dpi=180,
    bbox_inches="tight"
)
plt.close()

print("Saved: site/data/rebinned_psf_comparison.png")
print("Both PSF models visualized.")