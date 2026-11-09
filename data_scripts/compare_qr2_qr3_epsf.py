#!/usr/bin/env python3
"""
SPHEREx Explorer — QR2 vs QR3 ePSF Scientific Comparison (Version 2 - Updated Terminology)
Rigorous comparative analysis of the QR2 exposure-averaged effective PSF (10x oversampled)
with the official QR3 empirical pixel-convolved effective PSF (5x oversampled ePSF)
at validated 3I/ATLAS coordinates on Detector 3 (D3).

Official Calibration Context & Approved Terminology:
1. QR2 exposure-averaged effective PSF:
   Official SPHEREx Explanatory Supplement: QR2 PSF is an exposure-averaged effective PSF
   that incorporates the optical response and average in-flight pointing-jitter contribution,
   deconvolved for the detector pixel response function.
2. QR2 reconstructed pixel-convolved model:
   Our methodological reconstruction: QR2 exposure-averaged PSF convolved with a centered,
   idealized 1x1 native pixel boxcar kernel to re-incorporate pixel integration.
   Note: This is an idealized educational reconstruction, NOT an official calibration product.
3. QR3 empirical pixel-convolved ePSF:
   Official QR3 calibration product: Subpixel-resolved, empirical ePSF derived from on-sky
   stellar observations, inherently incorporating on-sky detector pixel integration.
   IRSA Recommendation: QR3 ePSF officially supersedes QR2 PSF and is recommended for all
   images, including QR2 images.

Educational & Methodological Scope:
This comparison is strictly educational and methodological, illustrating the physical effect
of pixel response convolution and comparing empirical vs. modeled PSFs. It does NOT imply
that QR2 and QR3 models are interchangeable for quantitative photometry.

Cometary Target Caveat:
Comet 3I/ATLAS possesses a diffuse, extended cometary coma. Neither QR2 point-spread models
nor QR3 ePSFs account for extended cometary morphology; point-source profile fitting will
systematically underestimate total coma flux.
"""

import json
from pathlib import Path

from astropy.table import Table
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import convolve2d

# Project Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
QR2_AUG_PATH = PROJECT_ROOT / "site" / "data" / "august_interpolated_psf.npy"
QR2_DEC_PATH = PROJECT_ROOT / "site" / "data" / "december_interpolated_psf.npy"
QR3_FITS_PATH = PROJECT_ROOT / "calibration" / "qr3" / "epsf_D3_spx_cal-epsf-v2-2026-191.fits"
OUT_DIR = PROJECT_ROOT / "site" / "data" / "qr3_comparison_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Nominal physical detector scale
NOMINAL_PIXEL_SCALE_ARCSEC = 6.15  # arcseconds per native detector pixel

# Validated Target Zones on Detector 3 (D3)
TARGETS = [
    {
        "epoch": "August 2025",
        "obs_id": "2025W31_2A_0156_1D3",
        "qr2_path": QR2_AUG_PATH,
        "qr3_row": 179,
        "binx": 3,
        "biny": 16,
        "xcenter": 648.591,
        "ycenter": 820.476,
        "cwave": 2.0655,
        "target_x": 734.302,
        "target_y": 840.148,
        "tag": "august",
    },
    {
        "epoch": "December 2025",
        "obs_id": "2025W50_2A_0741_1D3",
        "qr2_path": QR2_DEC_PATH,
        "qr3_row": 410,
        "binx": 3,
        "biny": 37,
        "xcenter": 648.591,
        "ycenter": 1865.354,
        "cwave": 1.6759,
        "target_x": 674.783,
        "target_y": 1886.315,
        "tag": "december",
    },
]


def create_pixel_boxcar_kernel_10x():
    """
    Constructs an exact 1x1 native detector pixel integration kernel for 10x oversampled arrays.
    Physical footprint: [-0.5, +0.5] native detector pixels = [-5.0, +5.0] subpixels.
    Spans 11 subpixel samples (-5 to +5): 9 inner full subpixels (weight 1.0) and
    2 boundary half subpixels (weight 0.5).
    Odd size (11x11) ensures exact symmetry around center index (5, 5) with zero phase offset.
    Normalized to sum to 1.0.
    """
    w1d = np.array([0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5], dtype=float) / 10.0
    k2d = np.outer(w1d, w1d)
    return k2d


def create_10x_to_5x_area_kernel():
    """
    Constructs a 2D separable subpixel cell-integration kernel to downsample from 10x to 5x.
    A 5x subpixel (width 0.2 native px) spans exactly two 10x subpixels (width 0.1 native px).
    Interval [-0.1, +0.1] covers 1 central subpixel and two half-subpixels at boundaries:
    1D weights = [0.5, 1.0, 0.5] (sum = 2.0).
    2D weights = [0.5, 1.0, 0.5] outer [0.5, 1.0, 0.5] (sum = 4.0 = area ratio).
    """
    w1d = np.array([0.5, 1.0, 0.5], dtype=float)
    return np.outer(w1d, w1d)


def resample_qr2_10x_to_5x(qr2_101):
    """
    Integrates QR2 (101x101 at 10x, center at 50) onto the 33x33 grid of QR3 (5x, center at 16).
    Uses exact area integration over each 5x cell footprint.
    Preserves total integrated flux partition without point-sampling bias.
    """
    kernel_area = create_10x_to_5x_area_kernel()
    integrated_conv = convolve2d(qr2_101, kernel_area, mode="same")
    
    # 5x grid sample indices in 10x array: center is 50, step is 2 subpixels
    # Range: 50 + (np.arange(33) - 16) * 2 = [18, 20, ..., 50, ..., 82]
    sample_indices = 50 + (np.arange(33) - 16) * 2
    resampled_33 = integrated_conv[np.ix_(sample_indices, sample_indices)]
    return resampled_33


def measure_psf_metrics(arr, oversampling, center, max_aperture_r=3.0):
    """
    Computes rigorous physical metrics for a PSF array:
    - Array total flux and aperture flux within r <= max_aperture_r native pixels.
    - Raw subpixel peak and physical surface brightness density peak.
    - Centroids computed strictly within the common aperture r <= max_aperture_r.
    - Gaussian core FWHM (fitted to r <= 1.5 native px).
    - Empirical FWHM (measured directly from azimuthal profile half-maximum crossing).
    """
    ny, nx = arr.shape
    y_idx, x_idx = np.indices((ny, nx))
    total_flux = float(np.sum(arr))

    # Offsets in native detector pixels
    dx = (x_idx - center[0]) / oversampling
    dy = (y_idx - center[1]) / oversampling
    r = np.hypot(dx, dy)

    # Surface brightness density: flux / (native detector pixel)^2
    pix_area = (1.0 / oversampling) ** 2
    density = arr / pix_area
    peak_density = float(np.max(density))
    raw_peak = float(np.max(arr))

    # Matched aperture mask (r <= 3.0 native pixels)
    aperture_mask = r <= max_aperture_r
    aperture_flux = float(np.sum(arr[aperture_mask]))
    aperture_fraction = aperture_flux / total_flux

    # Centroid measured strictly within the matched aperture
    cx_ap = float(np.sum(dx[aperture_mask] * arr[aperture_mask]) / aperture_flux)
    cy_ap = float(np.sum(dy[aperture_mask] * arr[aperture_mask]) / aperture_flux)

    # Full-array centroid (for diagnostic check)
    cx_full = float(np.sum(dx * arr) / total_flux)
    cy_full = float(np.sum(dy * arr) / total_flux)

    # 1. Gaussian Core FWHM Fit (r <= 1.5 native pixels)
    r_flat = r.ravel()
    d_flat = density.ravel()
    mask_fit = r_flat <= 1.5

    def gaussian_profile(radius, amp, sigma):
        return amp * np.exp(-0.5 * (radius / sigma) ** 2)

    try:
        popt, _ = curve_fit(
            gaussian_profile,
            r_flat[mask_fit],
            d_flat[mask_fit],
            p0=[peak_density, 0.8 / 2.355],
            maxfev=5000,
        )
        sigma = abs(popt[1])
        fwhm_gaussian_px = float(2.355 * sigma)
        gaussian_status = "OK"
    except Exception as exc:
        fwhm_gaussian_px = float("nan")
        gaussian_status = f"Fit failed: {str(exc)}"

    # 2. Empirical FWHM (Non-parametric Half-Maximum Crossing)
    half_max = peak_density * 0.5
    rounded_r = np.round(r_flat, 4)
    unique_r = np.unique(rounded_r)
    unique_means = np.array([np.mean(d_flat[rounded_r == ur]) for ur in unique_r])

    sub_half = np.where(unique_means <= half_max)[0]
    if len(sub_half) > 0 and sub_half[0] > 0:
        k = sub_half[0]
        r1, r2 = unique_r[k - 1], unique_r[k]
        m1, m2 = unique_means[k - 1], unique_means[k]
        r_half = r1 + (half_max - m1) * (r2 - r1) / (m2 - m1)
        fwhm_empirical_px = float(2.0 * r_half)
        empirical_status = "OK"
    else:
        fwhm_empirical_px = float("nan")
        empirical_status = "Half-maximum crossing not detected"

    return {
        "total_flux": total_flux,
        "aperture_flux_3px": aperture_flux,
        "aperture_containment_fraction": aperture_fraction,
        "raw_peak_subpixel": raw_peak,
        "peak_surface_density": peak_density,
        "centroid_aperture_px": (round(cx_ap, 4), round(cy_ap, 4)),
        "centroid_aperture_arcsec": (
            round(cx_ap * NOMINAL_PIXEL_SCALE_ARCSEC, 3),
            round(cy_ap * NOMINAL_PIXEL_SCALE_ARCSEC, 3),
        ),
        "centroid_full_array_px": (round(cx_full, 4), round(cy_full, 4)),
        "fwhm_gaussian_px": round(fwhm_gaussian_px, 4) if not np.isnan(fwhm_gaussian_px) else None,
        "fwhm_gaussian_arcsec": round(fwhm_gaussian_px * NOMINAL_PIXEL_SCALE_ARCSEC, 3) if not np.isnan(fwhm_gaussian_px) else None,
        "gaussian_fit_status": gaussian_status,
        "fwhm_empirical_px": round(fwhm_empirical_px, 4) if not np.isnan(fwhm_empirical_px) else None,
        "fwhm_empirical_arcsec": round(fwhm_empirical_px * NOMINAL_PIXEL_SCALE_ARCSEC, 3) if not np.isnan(fwhm_empirical_px) else None,
        "empirical_fwhm_status": empirical_status,
    }


def compute_radial_and_ee(arr, oversampling, center, max_r=3.0, n_bins=20):
    """
    Computes azimuthal mean surface brightness profile and enclosed energy (EE) curve.
    Both profiles are computed over matched physical radii r in [0, max_r] native pixels.
    Enclosed energy is normalized to the flux within r <= max_r native pixels (EE(max_r) = 1.0).
    Bin width delta_r = 3.0 / 20 = 0.15 native px ensures all bins are populated on 5x grids.
    """
    ny, nx = arr.shape
    y_idx, x_idx = np.indices((ny, nx))
    dx = (x_idx - center[0]) / oversampling
    dy = (y_idx - center[1]) / oversampling
    r = np.hypot(dx, dy)

    pix_area = (1.0 / oversampling) ** 2
    density = arr / pix_area

    bin_edges = np.linspace(0, max_r, n_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    radial_mean = []
    enclosed_energy = []

    r_flat = r.ravel()
    d_flat = density.ravel()
    arr_flat = arr.ravel()

    # Normalization flux within the common aperture r <= max_r
    aperture_flux_norm = np.sum(arr_flat[r_flat <= max_r])

    for k in range(len(bin_centers)):
        in_annulus = (r_flat >= bin_edges[k]) & (r_flat < bin_edges[k + 1])
        if np.any(in_annulus):
            radial_mean.append(float(np.mean(d_flat[in_annulus])))
        else:
            radial_mean.append(float("nan"))

        in_circle = r_flat <= bin_edges[k + 1]
        ee_val = float(np.sum(arr_flat[in_circle]) / aperture_flux_norm)
        enclosed_energy.append(ee_val)

    return {
        "radii_px": bin_centers.tolist(),
        "radii_arcsec": (bin_centers * NOMINAL_PIXEL_SCALE_ARCSEC).tolist(),
        "surface_brightness_density": radial_mean,
        "ee_edges_px": bin_edges[1:].tolist(),
        "ee_edges_arcsec": (bin_edges[1:] * NOMINAL_PIXEL_SCALE_ARCSEC).tolist(),
        "enclosed_energy_normalized": enclosed_energy,
        "aperture_normalization_radius_px": max_r,
        "aperture_normalization_radius_arcsec": max_r * NOMINAL_PIXEL_SCALE_ARCSEC,
    }


def rebin_centered_native(arr, oversampling, box_size_native=5):
    """
    Performs centered native detector pixel binning.
    Box size is 5x5 native detector pixels (spanning [-2.5, +2.5] native pixels),
    completely inscribed inside both QR2 (span [-5, 5]) and QR3 (span [-3.2, 3.2]).
    The central native pixel (index 2, 2) is symmetric around the origin (0, 0).
    """
    half_box = box_size_native // 2
    rebinned = np.zeros((box_size_native, box_size_native), dtype=float)
    center_idx = arr.shape[0] // 2

    for i in range(box_size_native):
        offset_i = i - half_box
        # Start and end subpixel indices
        if oversampling == 5:
            # For 5x, 5 subpixels per native pixel: [-2, +2] around center
            si = center_idx + offset_i * 5 - 2
            ei = si + 5
            for j in range(box_size_native):
                offset_j = j - half_box
                sj = center_idx + offset_j * 5 - 2
                ej = sj + 5
                rebinned[i, j] = np.sum(arr[si:ei, sj:ej])
        elif oversampling == 10:
            # For 10x, 10 subpixels per native pixel: [-5, +5] subpixels
            # Using exact half-subpixel trapezoidal weights at +/- 5 boundaries
            w1d = np.array([0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5])
            w2d = np.outer(w1d, w1d)
            si = center_idx + offset_i * 10 - 5
            ei = si + 11
            for j in range(box_size_native):
                offset_j = j - half_box
                sj = center_idx + offset_j * 10 - 5
                ej = sj + 11
                rebinned[i, j] = np.sum(arr[si:ei, sj:ej] * w2d)
        else:
            raise ValueError(f"Unsupported oversampling: {oversampling}")

    return rebinned


def run_comparison():
    print("=" * 88)
    print("SPHEREx EXPLORER — QR2 vs QR3 ePSF COMPARISON (APPROVED TERMINOLOGY)")
    print("=" * 88)
    print(f"Nominal science detector pixel scale : {NOMINAL_PIXEL_SCALE_ARCSEC} arcsec/pixel")
    print(f"Output directory                    : {OUT_DIR.relative_to(PROJECT_ROOT)}")

    # 1. Load QR3 Calibration FITS
    if not QR3_FITS_PATH.exists():
        raise FileNotFoundError(f"QR3 ePSF FITS file not found: {QR3_FITS_PATH}")
    qr3_table = Table.read(QR3_FITS_PATH, hdu="EPSF")

    # 2. Kernel Setup
    boxcar_kernel_11 = create_pixel_boxcar_kernel_10x()

    # Pre-verification: Verify zero centroid shift of symmetric boxcar kernel
    ky, kx = np.indices(boxcar_kernel_11.shape)
    k_shift_x = np.sum((kx - 5) * boxcar_kernel_11)
    k_shift_y = np.sum((ky - 5) * boxcar_kernel_11)
    print(f"\n[KERNEL AUDIT] 1x1 Native Pixel Boxcar Kernel (11x11, odd):")
    print(f"  Shape = {boxcar_kernel_11.shape}, Sum = {np.sum(boxcar_kernel_11):.8f}")
    print(f"  Centroid phase shift: dx = {k_shift_x:.2e} px, dy = {k_shift_y:.2e} px (ZERO SHIFT)")

    summary_results = {
        "metadata": {
            "title": "SPHEREx Detector D3: QR2 vs QR3 ePSF Methodological Comparison",
            "calibration_hierarchy_note": (
                "The official QR3 empirical pixel-convolved ePSF supersedes the legacy QR2 PSF "
                "and is recommended by IRSA for all SPHEREx scientific analysis, including QR2 images."
            ),
            "educational_methodological_disclaimer": (
                "This comparison is strictly educational and methodological, illustrating the physical "
                "effect of detector pixel response convolution. It does NOT imply that QR2 and QR3 models "
                "are scientifically interchangeable."
            ),
            "reconstruction_note": (
                "The QR2 reconstructed pixel-convolved model is an idealized methodological reconstruction "
                "produced by convolving the QR2 exposure-averaged PSF with a 1x1 native pixel boxcar kernel. "
                "It is NOT an official calibration product."
            ),
            "comet_target_caveat": (
                "Comet 3I/ATLAS possesses a diffuse, extended cometary coma. Neither QR2 point-spread models "
                "nor QR3 ePSFs account for extended cometary morphology; point-source profile fitting will "
                "systematically underestimate total coma flux."
            ),
            "nominal_pixel_scale_arcsec": NOMINAL_PIXEL_SCALE_ARCSEC,
            "approved_model_names": {
                "model_1": "QR2 exposure-averaged effective PSF",
                "model_2": "QR2 reconstructed pixel-convolved model",
                "model_3": "QR3 empirical pixel-convolved ePSF",
            },
        },
        "epochs": {},
    }

    for target in TARGETS:
        epoch = target["epoch"]
        tag = target["tag"]
        obs_id = target["obs_id"]
        qr2_file = target["qr2_path"]
        qr3_row = target["qr3_row"]

        print("\n" + "=" * 88)
        print(f"PROCESSING EPOCH: {epoch} ({obs_id})")
        print("=" * 88)
        print(f"Target detector coordinates : (x = {target['target_x']:.3f}, y = {target['target_y']:.3f})")
        print(f"QR3 matched zone row index  : {qr3_row} (BINX = {target['binx']}, BINY = {target['biny']})")
        print(f"Zone center pixel           : ({target['xcenter']:.3f}, {target['ycenter']:.3f})")
        print(f"Zone central wavelength     : {target['cwave']:.4f} µm")

        # Load models
        qr2_orig = np.load(qr2_file).astype(float)
        qr3_orig = np.array(qr3_table["EPSF"][qr3_row], dtype=float)

        # Validation: Verify input normalizations
        qr2_orig_flux = float(np.sum(qr2_orig))
        qr3_orig_flux = float(np.sum(qr3_orig))
        print(f"\nInput Normalization Check:")
        print(f"  QR2 original flux sum : {qr2_orig_flux:.10f}")
        print(f"  QR3 original flux sum : {qr3_orig_flux:.10f}")
        assert np.isclose(qr2_orig_flux, 1.0, atol=1e-5), "QR2 flux not normalized to 1.0"
        assert np.isclose(qr3_orig_flux, 1.0, atol=1e-5), "QR3 flux not normalized to 1.0"

        # Baseline metrics
        qr2_metrics = measure_psf_metrics(qr2_orig, oversampling=10, center=(50.0, 50.0))
        qr3_metrics = measure_psf_metrics(qr3_orig, oversampling=5, center=(16.0, 16.0))

        # 1. Area-Integrated Downsampling of QR2 to 5x (33x33)
        qr2_resampled_33 = resample_qr2_10x_to_5x(qr2_orig)
        qr2_resampled_flux = float(np.sum(qr2_resampled_33))
        qr2_resampled_metrics = measure_psf_metrics(qr2_resampled_33, oversampling=5, center=(16.0, 16.0))

        # 2. Symmetric 1x1 Pixel Convolution of QR2 (Reconstructed Pixel-Convolved Model)
        qr2_convolved_10x = convolve2d(qr2_orig, boxcar_kernel_11, mode="same")
        # Measure centroid before and after convolution
        y_10, x_10 = np.indices(qr2_orig.shape)
        orig_cx = np.sum((x_10 - 50.0) * qr2_orig) / qr2_orig_flux
        orig_cy = np.sum((y_10 - 50.0) * qr2_orig) / qr2_orig_flux
        conv_cx = np.sum((x_10 - 50.0) * qr2_convolved_10x) / np.sum(qr2_convolved_10x)
        conv_cy = np.sum((y_10 - 50.0) * qr2_convolved_10x) / np.sum(qr2_convolved_10x)
        delta_cent_conv = (conv_cx - orig_cx, conv_cy - orig_cy)
        print(f"\nConvolution Centroid Verification (10x):")
        print(f"  Before conv centroid offset : ({orig_cx:.6f}, {orig_cy:.6f}) subpixels")
        print(f"  After conv centroid offset  : ({conv_cx:.6f}, {conv_cy:.6f}) subpixels")
        print(f"  Centroid change from conv   : dx = {delta_cent_conv[0]:.2e}, dy = {delta_cent_conv[1]:.2e} subpixels")

        # Downsample convolved QR2 to 5x (33x33) via area integration
        qr2_eff_33 = resample_qr2_10x_to_5x(qr2_convolved_10x)
        qr2_eff_metrics = measure_psf_metrics(qr2_eff_33, oversampling=5, center=(16.0, 16.0))

        # 3. Residual Maps on Common 33x33 5x Grid
        diff_optical = qr3_orig - qr2_resampled_33
        diff_effective = qr3_orig - qr2_eff_33

        # 4. Centered Native Detector Pixel Rebinning (5x5 Science Pixels)
        qr2_nat_5 = rebin_centered_native(qr2_orig, oversampling=10, box_size_native=5)
        qr3_nat_5 = rebin_centered_native(qr3_orig, oversampling=5, box_size_native=5)
        qr2_eff_nat_5 = rebin_centered_native(qr2_eff_33, oversampling=5, box_size_native=5)
        diff_nat_5 = qr3_nat_5 - qr2_eff_nat_5

        # 5. Radial Surface Brightness & Enclosed Energy Profiles
        qr2_radial = compute_radial_and_ee(qr2_orig, oversampling=10, center=(50.0, 50.0))
        qr3_radial = compute_radial_and_ee(qr3_orig, oversampling=5, center=(16.0, 16.0))
        qr2_eff_radial = compute_radial_and_ee(qr2_eff_33, oversampling=5, center=(16.0, 16.0))

        # Check for unexpected NaNs in metric dictionaries
        nan_issues = []
        for m_name, m_dict in [("QR2 Exp-Avg", qr2_metrics), ("QR2 Reconstructed", qr2_eff_metrics), ("QR3 ePSF", qr3_metrics)]:
            for k_met, v_met in m_dict.items():
                if v_met is None or (isinstance(v_met, float) and np.isnan(v_met)):
                    nan_issues.append(f"{m_name}.{k_met}")
        print(f"\nNaN Audit: {len(nan_issues)} unexpected NaN fields found: {nan_issues}")

        # Summary Record per Epoch
        epoch_record = {
            "epoch": epoch,
            "obs_id": obs_id,
            "target_coords": (target["target_x"], target["target_y"]),
            "cwave_microns": target["cwave"],
            "validation": {
                "qr2_orig_flux": qr2_orig_flux,
                "qr3_orig_flux": qr3_orig_flux,
                "qr2_resampled_33_flux": qr2_resampled_flux,
                "qr2_effective_33_flux": float(np.sum(qr2_eff_33)),
                "conv_centroid_shift_subpixels": delta_cent_conv,
                "nan_issues": nan_issues,
            },
            # Explicit approved scientific model metadata
            "qr2_exposure_averaged_psf": {
                "model_description": "QR2 exposure-averaged effective PSF (10x, deconvolved for pixel response)",
                "metrics": qr2_metrics,
            },
            "qr2_reconstructed_pixel_convolved_model": {
                "model_description": "QR2 reconstructed pixel-convolved model (5x, methodological reconstruction)",
                "metrics": qr2_eff_metrics,
            },
            "qr3_empirical_pixel_convolved_epsf": {
                "model_description": "QR3 empirical pixel-convolved ePSF (5x, official recommended calibration product)",
                "metrics": qr3_metrics,
            },
            # Backward-compatibility aliases
            "qr2_optical_metrics": qr2_metrics,
            "qr2_effective_metrics": qr2_eff_metrics,
            "qr3_epsf_metrics": qr3_metrics,
            "residual_statistics": {
                "diff_deconvolved_rms": float(np.sqrt(np.mean(diff_optical ** 2))),
                "diff_deconvolved_max_abs": float(np.max(np.abs(diff_optical))),
                "diff_reconstructed_rms": float(np.sqrt(np.mean(diff_effective ** 2))),
                "diff_reconstructed_max_abs": float(np.max(np.abs(diff_effective))),
                # Legacy keys
                "diff_optical_rms": float(np.sqrt(np.mean(diff_optical ** 2))),
                "diff_effective_rms": float(np.sqrt(np.mean(diff_effective ** 2))),
            },
            "native_5x5_rebinned": {
                "qr2_exposure_averaged_central_pix_fraction": float(qr2_nat_5[2, 2]),
                "qr2_reconstructed_central_pix_fraction": float(qr2_eff_nat_5[2, 2]),
                "qr3_empirical_central_pix_fraction": float(qr3_nat_5[2, 2]),
                "qr2_exposure_averaged_5x5_sum": float(np.sum(qr2_nat_5)),
                "qr3_empirical_5x5_sum": float(np.sum(qr3_nat_5)),
                "diff_native_rms": float(np.sqrt(np.mean(diff_nat_5 ** 2))),
                # Legacy keys
                "qr2_optical_central_pix_fraction": float(qr2_nat_5[2, 2]),
                "qr2_effective_central_pix_fraction": float(qr2_eff_nat_5[2, 2]),
                "qr3_epsf_central_pix_fraction": float(qr3_nat_5[2, 2]),
                "qr2_optical_5x5_sum": float(np.sum(qr2_nat_5)),
                "qr3_epsf_5x5_sum": float(np.sum(qr3_nat_5)),
            },
            "radial_profiles": {
                "radii_arcsec": qr3_radial["radii_arcsec"],
                "radii_native_px": qr3_radial["radii_px"],
                "qr2_exposure_averaged_sb": qr2_radial["surface_brightness_density"],
                "qr2_reconstructed_sb": qr2_eff_radial["surface_brightness_density"],
                "qr3_empirical_sb": qr3_radial["surface_brightness_density"],
                "ee_radii_arcsec": qr3_radial["ee_edges_arcsec"],
                "ee_radii_native_px": qr3_radial["ee_edges_px"],
                "qr2_exposure_averaged_ee": qr2_radial["enclosed_energy_normalized"],
                "qr2_reconstructed_ee": qr2_eff_radial["enclosed_energy_normalized"],
                "qr3_empirical_ee": qr3_radial["enclosed_energy_normalized"],
                # Legacy keys
                "qr2_optical_sb": qr2_radial["surface_brightness_density"],
                "qr2_effective_sb": qr2_eff_radial["surface_brightness_density"],
                "qr3_epsf_sb": qr3_radial["surface_brightness_density"],
                "qr2_optical_ee": qr2_radial["enclosed_energy_normalized"],
                "qr2_effective_ee": qr2_eff_radial["enclosed_energy_normalized"],
                "qr3_epsf_ee": qr3_radial["enclosed_energy_normalized"],
            },
        }

        summary_results["epochs"][tag] = epoch_record
        summary_results[tag] = epoch_record  # backward-compatibility alias

        # Print Numerical Comparison Table with Approved Headings
        print("\nNUMERICAL METRIC COMPARISON TABLE:")
        print("-" * 92)
        print(f"{'Metric':<34} | {'QR2 Exp-Avg (10x)':<18} | {'QR2 Reconst (5x)':<18} | {'QR3 ePSF (5x)':<14}")
        print("-" * 92)
        print(f"{'Array Dimensions':<34} | {'101 x 101':<18} | {'33 x 33':<18} | {'33 x 33':<14}")
        print(f"{'Total Integrated Flux':<34} | {qr2_orig_flux:<18.6f} | {np.sum(qr2_eff_33):<18.6f} | {qr3_orig_flux:<14.6f}")
        print(f"{'Flux in r <= 3.0 px (18.45\")':<34} | {qr2_metrics['aperture_flux_3px']:<18.6f} | {qr2_eff_metrics['aperture_flux_3px']:<18.6f} | {qr3_metrics['aperture_flux_3px']:<14.6f}")
        print(f"{'Aperture Flux Fraction (r<=3.0)':<34} | {qr2_metrics['aperture_containment_fraction']*100:<17.2f}% | {qr2_eff_metrics['aperture_containment_fraction']*100:<17.2f}% | {qr3_metrics['aperture_containment_fraction']*100:<13.2f}%")
        print(f"{'Raw Pixel Peak':<34} | {qr2_metrics['raw_peak_subpixel']:<18.6f} | {qr2_eff_metrics['raw_peak_subpixel']:<18.6f} | {qr3_metrics['raw_peak_subpixel']:<14.6f}")
        print(f"{'Peak Density (flux/native px²)':<34} | {qr2_metrics['peak_surface_density']:<18.4f} | {qr2_eff_metrics['peak_surface_density']:<18.4f} | {qr3_metrics['peak_surface_density']:<14.4f}")
        print(f"{'Centroid Offset X (arcsec, r<=3)':<34} | {qr2_metrics['centroid_aperture_arcsec'][0]:<18.3f} | {qr2_eff_metrics['centroid_aperture_arcsec'][0]:<18.3f} | {qr3_metrics['centroid_aperture_arcsec'][0]:<14.3f}")
        print(f"{'Centroid Offset Y (arcsec, r<=3)':<34} | {qr2_metrics['centroid_aperture_arcsec'][1]:<18.3f} | {qr2_eff_metrics['centroid_aperture_arcsec'][1]:<18.3f} | {qr3_metrics['centroid_aperture_arcsec'][1]:<14.3f}")
        print(f"{'FWHM Gaussian Core (arcsec)':<34} | {qr2_metrics['fwhm_gaussian_arcsec']:<18.2f} | {qr2_eff_metrics['fwhm_gaussian_arcsec']:<18.2f} | {qr3_metrics['fwhm_gaussian_arcsec']:<14.2f}")
        print(f"{'FWHM Empirical (arcsec)':<34} | {qr2_metrics['fwhm_empirical_arcsec']:<18.2f} | {qr2_eff_metrics['fwhm_empirical_arcsec']:<18.2f} | {qr3_metrics['fwhm_empirical_arcsec']:<14.2f}")
        print(f"{'Central Native Pixel Fraction':<34} | {qr2_nat_5[2, 2]:<18.4f} | {qr2_eff_nat_5[2, 2]:<18.4f} | {qr3_nat_5[2, 2]:<14.4f}")
        print("-" * 92)

        # -----------------------------------------------------------------
        # PLOT 1 & 2: 4-PANEL SIDE-BY-SIDE COMPARISON (CORRECTED LABELS)
        # -----------------------------------------------------------------
        fig, axes = plt.subplots(1, 4, figsize=(19, 4.6), constrained_layout=True)
        fig.suptitle(
            f"SPHEREx {epoch} ({obs_id}) — Detector D3 Model Comparison (CWAVE = {target['cwave']:.4f} µm)\n"
            f"[Methodological Comparison: QR2 Exposure-Averaged PSF vs QR3 Empirical ePSF]",
            fontsize=12,
            fontweight="bold",
            color="#0f172a",
        )

        extent_native = [-3.3, 3.3, -3.3, 3.3]
        vmax = max(qr3_orig.max(), qr2_resampled_33.max(), qr2_eff_33.max())

        # Panel 1: QR2 Exposure-Averaged Effective PSF (Resampled 5x)
        im0 = axes[0].imshow(qr2_resampled_33, origin="lower", extent=extent_native, cmap="inferno", vmin=0.0, vmax=vmax)
        axes[0].set_title(f"QR2 Exp-Avg PSF (5x)\n[Pixel-Deconvolved]\nPeak={qr2_resampled_33.max():.4f}", fontsize=9, fontweight="bold")
        axes[0].set_xlabel("Offset Δx (native pixels)")
        axes[0].set_ylabel("Offset Δy (native pixels)")
        divider0 = make_axes_locatable(axes[0])
        cax0 = divider0.append_axes("right", size="5%", pad=0.08)
        fig.colorbar(im0, cax=cax0, label="Fractional Flux / 5x pixel")

        # Panel 2: QR3 Empirical Pixel-Convolved ePSF (5x)
        im1 = axes[1].imshow(qr3_orig, origin="lower", extent=extent_native, cmap="inferno", vmin=0.0, vmax=vmax)
        axes[1].set_title(f"QR3 Empirical ePSF (5x)\n[Official IRSA Recommended]\nPeak={qr3_orig.max():.4f}", fontsize=9, fontweight="bold")
        axes[1].set_xlabel("Offset Δx (native pixels)")
        divider1 = make_axes_locatable(axes[1])
        cax1 = divider1.append_axes("right", size="5%", pad=0.08)
        fig.colorbar(im1, cax=cax1, label="Fractional Flux / 5x pixel")

        # Panel 3: Difference (QR3 - QR2_deconvolved)
        diff_opt_lim = max(abs(diff_optical.min()), abs(diff_optical.max()))
        im2 = axes[2].imshow(diff_optical, origin="lower", extent=extent_native, cmap="coolwarm", vmin=-diff_opt_lim, vmax=diff_opt_lim)
        axes[2].set_title(f"Difference: QR3 - QR2\n[Empirical - Deconvolved]\nRMS={np.sqrt(np.mean(diff_optical**2)):.4f}", fontsize=9, fontweight="bold")
        axes[2].set_xlabel("Offset Δx (native pixels)")
        divider2 = make_axes_locatable(axes[2])
        cax2 = divider2.append_axes("right", size="5%", pad=0.08)
        fig.colorbar(im2, cax=cax2, label="Residual Difference")

        # Panel 4: Residual (QR3 - QR2 Reconstructed Pixel-Convolved)
        diff_eff_lim = max(abs(diff_effective.min()), abs(diff_effective.max()))
        im3 = axes[3].imshow(diff_effective, origin="lower", extent=extent_native, cmap="coolwarm", vmin=-diff_eff_lim, vmax=diff_eff_lim)
        axes[3].set_title(f"Residual: QR3 - QR2 Reconst\n[Empirical - Pixel Convolved]\nRMS={np.sqrt(np.mean(diff_effective**2)):.4f}", fontsize=9, fontweight="bold")
        axes[3].set_xlabel("Offset Δx (native pixels)")
        divider3 = make_axes_locatable(axes[3])
        cax3 = divider3.append_axes("right", size="5%", pad=0.08)
        fig.colorbar(im3, cax=cax3, label="Pixel-Convolved Residual")

        plot_path = OUT_DIR / f"{tag}_qr2_qr3_comparison.png"
        plt.savefig(plot_path, dpi=180)
        plt.close(fig)
        print(f"Saved: {plot_path.relative_to(PROJECT_ROOT)}")

    # -----------------------------------------------------------------
    # PLOT 3: RADIAL PROFILES & ENCLOSED ENERGY (APPROVED TERMINOLOGY)
    # -----------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=True)
    fig.suptitle(
        "SPHEREx Detector D3: Surface Brightness Density & Normalized Enclosed Energy Profiles\n"
        "[Methodological Comparison: QR2 Exposure-Averaged PSF vs QR3 Empirical ePSF]",
        fontsize=12,
        fontweight="bold",
    )

    for col, target in enumerate(TARGETS):
        tag = target["tag"]
        epoch = target["epoch"]
        data = summary_results["epochs"][tag]["radial_profiles"]

        r_arcsec = np.array(data["radii_arcsec"])

        # Top row: Surface Brightness Density
        ax_top = axes[0, col]
        ax_top.plot(r_arcsec, data["qr2_exposure_averaged_sb"], label="QR2 exposure-averaged effective PSF (10x)", color="#2563eb", linewidth=2.0)
        ax_top.plot(r_arcsec, data["qr2_reconstructed_sb"], label="QR2 reconstructed pixel-convolved model (5x)", color="#059669", linewidth=2.0, linestyle="--")
        ax_top.plot(r_arcsec, data["qr3_empirical_sb"], label="QR3 empirical pixel-convolved ePSF (5x)", color="#dc2626", linewidth=2.2)
        ax_top.set_title(
            f"{epoch}: Surface Brightness Density\nCWAVE = {target['cwave']:.4f} µm (Zone Row {target['qr3_row']})",
            fontsize=11,
            fontweight="bold",
        )
        ax_top.set_xlabel("Radial Distance r (arcseconds)")
        ax_top.set_ylabel("Surface Brightness (flux / native pixel²)")
        ax_top.grid(True, linestyle=":", alpha=0.6)
        ax_top.legend(frameon=True, fontsize=8.5)
        ax_top.set_xlim(0, 18.5)

        ax_top_px = ax_top.secondary_xaxis("top", functions=(lambda a: a / NOMINAL_PIXEL_SCALE_ARCSEC, lambda p: p * NOMINAL_PIXEL_SCALE_ARCSEC))
        ax_top_px.set_xlabel("Radial Distance r (native detector pixels)")

        # Bottom row: Normalized Enclosed Energy (normalized at r = 3.0 native px)
        ee_arcsec = np.array(data["ee_radii_arcsec"])
        ax_bot = axes[1, col]
        ax_bot.plot(ee_arcsec, data["qr2_exposure_averaged_ee"], label="QR2 exposure-averaged EE(r)", color="#2563eb", linewidth=2.0)
        ax_bot.plot(ee_arcsec, data["qr2_reconstructed_ee"], label="QR2 reconstructed pixel-convolved EE(r)", color="#059669", linewidth=2.0, linestyle="--")
        ax_bot.plot(ee_arcsec, data["qr3_empirical_ee"], label="QR3 empirical pixel-convolved EE(r)", color="#dc2626", linewidth=2.2)
        ax_bot.axhline(0.5, color="gray", linestyle=":", alpha=0.5, label="50% Normalized")
        ax_bot.axhline(0.8, color="gray", linestyle="--", alpha=0.5, label="80% Normalized")
        ax_bot.axhline(1.0, color="black", linestyle="-", alpha=0.3)
        ax_bot.set_title(
            f"{epoch}: Normalized Enclosed Energy (EE(r) / EE(18.45\"))",
            fontsize=11,
            fontweight="bold",
        )
        ax_bot.set_xlabel("Aperture Radius r (arcseconds)")
        ax_bot.set_ylabel("Normalized Enclosed Fraction")
        ax_bot.grid(True, linestyle=":", alpha=0.6)
        ax_bot.legend(frameon=True, fontsize=8.5, loc="lower right")
        ax_bot.set_xlim(0, 18.5)
        ax_bot.set_ylim(0, 1.05)

        ax_bot_px = ax_bot.secondary_xaxis("top", functions=(lambda a: a / NOMINAL_PIXEL_SCALE_ARCSEC, lambda p: p * NOMINAL_PIXEL_SCALE_ARCSEC))
        ax_bot_px.set_xlabel("Aperture Radius r (native detector pixels)")

    radial_plot_path = OUT_DIR / "radial_profile_comparison.png"
    plt.savefig(radial_plot_path, dpi=180)
    plt.close(fig)
    print(f"Saved: {radial_plot_path.relative_to(PROJECT_ROOT)}")

    # -----------------------------------------------------------------
    # PLOT 4: CENTERED NATIVE DETECTOR 5x5 PIXELATION (APPROVED LABELS)
    # -----------------------------------------------------------------
    fig, axes = plt.subplots(2, 3, figsize=(14, 9), constrained_layout=True)
    fig.suptitle(
        "SPHEREx Detector D3: Physical Native Pixelation (Centered 5×5 Science Pixels @ 6.15\"/pixel)\n"
        "[Methodological Demonstration of Native Pixel Integration]",
        fontsize=12,
        fontweight="bold",
    )

    extent_5 = [-2.5, 2.5, -2.5, 2.5]

    for row_idx, target in enumerate(TARGETS):
        tag = target["tag"]
        epoch = target["epoch"]
        qr2_file = target["qr2_path"]
        qr3_row = target["qr3_row"]

        qr2_orig = np.load(qr2_file).astype(float)
        qr3_orig = np.array(qr3_table["EPSF"][qr3_row], dtype=float)
        qr2_conv = convolve2d(qr2_orig, boxcar_kernel_11, mode="same")

        qr2_nat = rebin_centered_native(qr2_orig, oversampling=10, box_size_native=5)
        qr3_nat = rebin_centered_native(qr3_orig, oversampling=5, box_size_native=5)
        qr2_eff_nat = rebin_centered_native(qr2_conv, oversampling=10, box_size_native=5)
        diff_nat = qr3_nat - qr2_eff_nat

        vmax_nat = max(qr2_nat.max(), qr3_nat.max(), qr2_eff_nat.max())

        # Col 0: QR2 Exposure-Averaged PSF binned to native
        im0 = axes[row_idx, 0].imshow(qr2_nat, origin="lower", extent=extent_5, cmap="inferno", vmin=0, vmax=vmax_nat)
        axes[row_idx, 0].set_title(f"{epoch}: QR2 Exp-Avg PSF on Native Pixels\nPeak={qr2_nat.max():.4f}", fontsize=9, fontweight="bold")
        axes[row_idx, 0].set_xlabel("Detector X Offset (native pixels)")
        axes[row_idx, 0].set_ylabel("Detector Y Offset (native pixels)")
        divider0 = make_axes_locatable(axes[row_idx, 0])
        cax0 = divider0.append_axes("right", size="5%", pad=0.08)
        fig.colorbar(im0, cax=cax0, label="Native Pixel Fraction")

        # Col 1: QR3 Empirical ePSF binned to native
        im1 = axes[row_idx, 1].imshow(qr3_nat, origin="lower", extent=extent_5, cmap="inferno", vmin=0, vmax=vmax_nat)
        axes[row_idx, 1].set_title(f"{epoch}: QR3 Empirical ePSF on Native Pixels\nPeak={qr3_nat.max():.4f}", fontsize=9, fontweight="bold")
        axes[row_idx, 1].set_xlabel("Detector X Offset (native pixels)")
        divider1 = make_axes_locatable(axes[row_idx, 1])
        cax1 = divider1.append_axes("right", size="5%", pad=0.08)
        fig.colorbar(im1, cax=cax1, label="Native Pixel Fraction")

        # Col 2: Native difference (QR3 - QR2 reconstructed)
        diff_nat_lim = max(abs(diff_nat.min()), abs(diff_nat.max()))
        im2 = axes[row_idx, 2].imshow(diff_nat, origin="lower", extent=extent_5, cmap="coolwarm", vmin=-diff_nat_lim, vmax=diff_nat_lim)
        axes[row_idx, 2].set_title(f"{epoch}: Residual (QR3 - QR2 Reconst)\nRMS={np.sqrt(np.mean(diff_nat**2)):.4f}", fontsize=9, fontweight="bold")
        axes[row_idx, 2].set_xlabel("Detector X Offset (native pixels)")
        divider2 = make_axes_locatable(axes[row_idx, 2])
        cax2 = divider2.append_axes("right", size="5%", pad=0.08)
        fig.colorbar(im2, cax=cax2, label="Difference Fraction")

    native_plot_path = OUT_DIR / "detector_native_rebin_comparison.png"
    plt.savefig(native_plot_path, dpi=180)
    plt.close(fig)
    print(f"Saved: {native_plot_path.relative_to(PROJECT_ROOT)}")

    # -----------------------------------------------------------------
    # SAVE SUMMARY JSON
    # -----------------------------------------------------------------
    summary_path = OUT_DIR / "comparison_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_results, f, indent=2)
    print(f"Saved: {summary_path.relative_to(PROJECT_ROOT)}")

    print("\n" + "=" * 88)
    print("APPROVED SCIENTIFIC INTERPRETATION & CAVEATS:")
    print("=" * 88)
    print("1. CALIBRATION STATUS & HIERARCHY:")
    print("   - Official QR3 empirical pixel-convolved ePSF supersedes the legacy QR2 PSF.")
    print("   - IRSA officially recommends QR3 ePSF for all scientific analysis, including QR2 images.")
    print("2. NATURE OF CALIBRATION MODELS:")
    print("   - QR2 is an exposure-averaged effective PSF (optical response + pointing jitter),")
    print("     deconvolved for detector pixel response.")
    print("   - QR3 is an empirical pixel-convolved ePSF derived from on-sky stellar observations.")
    print("   - QR2 reconstructed pixel-convolved model is our methodological reconstruction,")
    print("     NOT an official calibration product.")
    print("3. EDUCATIONAL SCOPE:")
    print("   - This comparison is educational and methodological, demonstrating pixel-response broadening.")
    print("   - It does NOT imply that QR2 and QR3 models are interchangeable for science photometry.")
    print("4. COMETARY TARGET MORPHOLOGY LIMITATION:")
    print("   - Comet 3I/ATLAS is an extended body with a diffuse cometary coma.")
    print("   - Neither QR2 point-spread model nor QR3 ePSF represents the extended coma.")
    print("   - Point-source profile fitting will systematically underestimate total coma flux.")
    print("5. DETECTOR SCALE:")
    print("   - 6.15 arcsec/pixel is nominal; slight optical distortion variations exist across D3.")
    print("=" * 88)
    print("STAGE 2 COMPARISON (APPROVED SCIENTIFIC TERMINOLOGY) COMPLETED.")
    print("=" * 88)


if __name__ == "__main__":
    run_comparison()
