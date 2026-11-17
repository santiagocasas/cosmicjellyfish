"""Consistency tests for the survey specification files.

These tests do not build a cosmology; they only check that the packaged files
exist, parse, and are internally consistent (bin edges, densities, bias keys and
shot-noise keys all agree). The observable-level checks live in the dedicated
observable test modules.
"""

from __future__ import annotations

from importlib import resources

import pytest
import yaml

SPECTRO_FILES = [
    "DESI-BGS-SKAOPaper",
    "DESI-ELG-SKAOPaper",
    "SKAO-Spectroscopic-SKAOPaper",
    "SKAO-Spectroscopic-Redbook",
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
