"""Consistency tests for the survey specification files.

These tests do not build a cosmology; they only check that the packaged files
exist, parse, and are internally consistent (bin edges, densities, bias keys and
shot-noise keys all agree). The observable-level checks live in the dedicated
observable test modules.
"""

from __future__ import annotations

import importlib.util
import sys
from importlib import resources
from pathlib import Path

import numpy as np
import pytest
import yaml

SPECTRO_FILES = [
    "DESI-BGS-SKAOPaper",
    "DESI-ELG-SKAOPaper",
    "SKAO-Spectroscopic-SKAOPaper",
    "SKAO-Spectroscopic-Redbook",
    "DESI-BGS-Validation2023",
    "DESI-LRG-Validation2023",
    "DESI-ELG-Validation2023",
    "DESI-QSO-Validation2023",
]

PHOTO_FILES = [
    "Rubin-Photometric-SKAOPaper",
    "SKAO-Photometric-SKAOPaper",
]

IM_FILES = [
    "SKAO-IM-Redbook-DESI-ELG",
    "SKAO-IM-Redbook",
]


def _specs_dir():
    return resources.files("cosmicjellyfish") / "configs" / "other_survey_specifications"


def _load(name):
    path = _specs_dir() / f"{name}.yaml"
    assert path.is_file(), f"missing packaged survey file: {path}"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["specifications"]


@pytest.mark.parametrize("name", SPECTRO_FILES)
def test_spectroscopic_specs_are_consistent(name):
    specs = _load(name)
    bins = specs["z_bins_sp"]
    nbins = len(bins)

    assert nbins >= 1
    assert len(specs["dndOmegadz"]) == nbins, f"{name}: dndOmegadz length != bins"
    assert set(specs["dndOmegadz"]) == set(bins), f"{name}: dndOmegadz keys != bin keys"

    model = specs["sp_bias_model"]
    bias_table = specs["sp_bias_parametrization"][model]
    prefix = specs["sp_bias_root"] + specs["sp_bias_sample"] + "_"
    for ibin in bins:
        assert prefix + str(ibin) in bias_table, f"{name}: missing bias key {prefix}{ibin}"

    shot_keys = specs["shot_noise_parametrization"][specs["shot_noise_model"]]
    for ibin in bins:
        assert f"Ps_{ibin}" in shot_keys, f"{name}: missing shot-noise key Ps_{ibin}"

    for edge_pair in bins.values():
        assert len(edge_pair) == 2
        assert edge_pair[0] < edge_pair[1]


@pytest.mark.parametrize("name", PHOTO_FILES)
def test_photometric_specs_are_consistent(name):
    specs = _load(name)
    bins = specs.get("z_bins_ph", specs.get("z_bins_GCph"))
    assert bins is not None and len(bins) >= 2
    assert all(b0 < b1 for b0, b1 in zip(bins[:-1], bins[1:]))

    assert specs["zm"] > 0
    assert specs["ngamma"] > 0
    assert specs["ngal_sqarmin"] > 0
    assert specs["fsky_GCph"] > 0
    assert specs["fsky_WL"] > 0
    assert specs["lmax_GCph"] > 0
    assert specs["lmax_WL"] > 0

    bias_model = specs["ph_bias_model"]
    assert bias_model in specs["ph_bias_parametrization"]
    assert specs["IA_params"]["IA_model"] == "eNLA"


@pytest.mark.parametrize("name", IM_FILES)
def test_im_specs_are_consistent(name):
    specs = _load(name)
    bins = specs["z_bins_IM"]
    assert len(bins) >= 1
    for edge_pair in bins.values():
        assert len(edge_pair) == 2
        assert edge_pair[0] < edge_pair[1]
    assert specs["fsky_IM"] > 0
    assert specs["area_survey_IM"] > 0


def test_desi_elg_and_im_cross_bins_align():
    elg = _load("DESI-ELG-SKAOPaper")["z_bins_sp"]
    im = _load("SKAO-IM-Redbook-DESI-ELG")["z_bins_IM"]
    assert list(elg.values()) == list(im.values())


def test_historical_desi_bins_match_the_reference_tables():
    bgs = _load("DESI-BGS-SKAOPaper")
    assert list(bgs["z_bins_sp"].values()) == [
        [0.00, 0.10],
        [0.10, 0.20],
        [0.20, 0.30],
        [0.30, 0.40],
        [0.40, 0.50],
    ]
    assert [bgs["dndOmegadz"][i] for i in range(1, 6)] == [
        1165.0,
        3074.0,
        1909.0,
        732.0,
        120.0,
    ]

    elg = _load("DESI-ELG-SKAOPaper")
    assert len(elg["z_bins_sp"]) == 11
    assert elg["z_bins_sp"][1] == [0.60, 0.70]
    assert elg["z_bins_sp"][11] == [1.60, 1.70]
    assert elg["dndOmegadz"][2] == 2269.0


# --- DESI 2023 validation-paper specifications (arXiv:2306.06307, Table 7) -----------------
# Transcribed a second time here, independently of the generator, so that a typo in either
# copy is caught. Densities are deg^-2 per bin of width 0.1; amplitudes A in b(z) = A / D(z).
DESI2023 = {
    "BGS": (0.0, 1.34, [101.1, 231.3, 216.9, 97.3]),
    "LRG": (0.4, 1.7, [47.5, 65.6, 80.0, 93.2, 99.3, 63.7, 28.3]),
    "ELG": (1.1, 0.84, [108.0, 103.6, 97.1, 87.7, 55.4]),
    "QSO": (1.6, 1.2, [12.1, 11.8, 11.1, 10.6, 9.5]),
}


def _generator():
    path = Path(__file__).resolve().parents[1] / "scripts" / "validation"
    path = path / "generate_desi_validation_specs.py"
    spec = importlib.util.spec_from_file_location("generate_desi_validation_specs", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("tracer", sorted(DESI2023))
def test_desi2023_bins_and_densities_match_table7(tracer):
    zmin, _, densities = DESI2023[tracer]
    specs = _load(f"DESI-{tracer}-Validation2023")
    nbins = len(densities)

    assert len(specs["z_bins_sp"]) == nbins
    for i, (lo, hi) in specs["z_bins_sp"].items():
        assert lo == pytest.approx(zmin + 0.1 * (i - 1))
        assert hi == pytest.approx(zmin + 0.1 * i)
    # the YAML stores deg^-2 per unit redshift
    got = [specs["dndOmegadz"][i] for i in range(1, nbins + 1)]
    assert got == pytest.approx([d / 0.1 for d in densities])
    assert specs["area_survey_spectro"] == 14000


def test_desi2023_tracers_tile_the_redshift_range_without_overlap():
    edges = []
    for tracer in ("BGS", "LRG", "ELG", "QSO"):
        bins = _load(f"DESI-{tracer}-Validation2023")["z_bins_sp"]
        edges.extend(bins[i] for i in sorted(bins))
    assert edges[0][0] == pytest.approx(0.0)
    assert edges[-1][1] == pytest.approx(2.1)
    for (_, hi), (lo, _) in zip(edges[:-1], edges[1:]):
        assert hi == pytest.approx(lo)


@pytest.mark.parametrize("tracer", sorted(DESI2023))
def test_desi2023_bias_is_amplitude_over_growth(tracer):
    zmin, amplitude, densities = DESI2023[tracer]
    specs = _load(f"DESI-{tracer}-Validation2023")
    growth = _generator().growth_factor
    table = specs["sp_bias_parametrization"]["linear"]
    log_table = specs["sp_bias_parametrization"]["linear_log"]
    for i in range(1, len(densities) + 1):
        zmid = zmin + 0.1 * (i - 0.5)
        expected = amplitude / growth(zmid)
        assert table[f"bg_{i}"] == pytest.approx(expected, abs=5e-4)
        assert log_table[f"lnbg_{i}"] == pytest.approx(np.log(expected), abs=5e-4)


def test_desi2023_growth_factor_sanity():
    growth = _generator().growth_factor
    assert growth(0.0) == pytest.approx(1.0)
    assert growth(0.55) == pytest.approx(0.7485, abs=2e-3)  # symbolic backend: 0.74849


def test_desi2023_generator_output_is_up_to_date():
    generator = _generator()
    assert generator.main(["--check"]) == 0


def test_legacy_desi_specs_are_untouched_by_the_2023_set():
    bgs = _load("DESI-BGS-SKAOPaper")
    elg = _load("DESI-ELG-SKAOPaper")
    assert len(bgs["z_bins_sp"]) == 5 and len(elg["z_bins_sp"]) == 11
    assert bgs["sp_bias_parametrization"]["linear"]["bg_1"] == pytest.approx(1.364, abs=1e-3)
    assert elg["sp_bias_parametrization"]["linear"]["bg_1"] == pytest.approx(1.019, abs=1e-3)
