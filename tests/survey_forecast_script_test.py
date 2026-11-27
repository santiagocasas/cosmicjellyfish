"""Unit tests for the Phase 3 survey-forecast harness.

These tests exercise the bookkeeping (parameter sets, combination of independent blocks
and table rendering) without running a Fisher matrix. The full runs are recorded in
``docs/SURVEY_VALIDATION_ROADMAP.md``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validation" / "run_survey_forecasts.py"


def _load_module():
    sys.path.insert(0, str(REPO_ROOT))
    spec = importlib.util.spec_from_file_location("run_survey_forecasts", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


module = _load_module()


def test_free_parameters_follow_the_model():
    lcdm = module._free_parameters("LCDM")
    w0wa = module._free_parameters("w0waCDM")
    assert list(lcdm) == ["Omegam", "Omegab", "h", "ns", "sigma8"]
    assert list(w0wa) == ["Omegam", "Omegab", "h", "ns", "sigma8", "w0", "wa"]
    with pytest.raises(ValueError):
        module._free_parameters("nuoCDM")


def test_combination_matches_inverse_variance_addition():
    names = list(module._free_parameters("LCDM"))
    sigmas = {
        "first": {name: 0.01 for name in names},
        "second": {name: 0.02 for name in names},
    }
    results = {
        name: {
            "label": name,
            "observables": ["GCsp"],
            "note": "",
            "elapsed_s": 1.0,
            "sigma": sigma,
            "fisher_matrix": np.diag([1.0 / sigma[n] ** 2 for n in names]).tolist(),
        }
        for name, sigma in sigmas.items()
    }
    combined = module.combine(results, ("first", "second"), "LCDM")
    expected = 1.0 / np.sqrt(1.0 / 0.01**2 + 1.0 / 0.02**2)
    for name in names:
        assert combined["sigma"][name] == pytest.approx(expected, rel=1e-12)
    assert combined["elapsed_s"] == pytest.approx(2.0)
    assert np.shape(combined["fisher_matrix"]) == (len(names), len(names))


def test_combination_requires_a_stored_block():
    results = {
        "first": {
            "label": "first",
            "observables": ["GCsp"],
            "note": "",
            "elapsed_s": 1.0,
            "sigma": {name: 0.1 for name in module._free_parameters("LCDM")},
        }
    }
    with pytest.raises(ValueError, match="no stored Fisher block"):
        module.combine(results, ("first",), "LCDM")


def test_combination_rejects_a_block_with_the_wrong_shape():
    results = {
        "first": {
            "label": "first",
            "observables": ["GCsp"],
            "note": "",
            "elapsed_s": 1.0,
            "sigma": {name: 0.1 for name in module._free_parameters("LCDM")},
            "fisher_matrix": np.eye(3).tolist(),
        }
    }
    with pytest.raises(ValueError, match="Fisher block of shape"):
        module.combine(results, ("first",), "LCDM")


def test_combination_keeps_parameter_correlations():
    names = list(module._free_parameters("LCDM"))
    first = np.array(
        [
            [4.0, 1.0, 0.5, 0.0, 0.0],
            [1.0, 3.0, 0.4, 0.0, 0.0],
            [0.5, 0.4, 2.0, 0.1, 0.0],
            [0.0, 0.0, 0.1, 2.5, 0.3],
            [0.0, 0.0, 0.0, 0.3, 1.5],
        ]
    )
    second = np.array(
        [
            [2.0, 0.6, 0.0, 0.0, 0.0],
            [0.6, 2.2, 0.3, 0.0, 0.0],
            [0.0, 0.3, 1.8, 0.2, 0.0],
            [0.0, 0.0, 0.2, 3.0, 0.5],
            [0.0, 0.0, 0.0, 0.5, 2.4],
        ]
    )
    results = {
        "first": {
            "label": "first",
            "observables": ["GCsp"],
            "note": "",
            "elapsed_s": 1.0,
            "sigma": {n: float(np.sqrt(np.linalg.inv(first)[i, i])) for i, n in enumerate(names)},
            "fisher_matrix": first.tolist(),
        },
        "second": {
            "label": "second",
            "observables": ["GCsp"],
            "note": "",
            "elapsed_s": 1.0,
            "sigma": {n: float(np.sqrt(np.linalg.inv(second)[i, i])) for i, n in enumerate(names)},
            "fisher_matrix": second.tolist(),
        },
    }
    combined = module.combine(results, ("first", "second"), "LCDM")
    expected = np.sqrt(np.diag(np.linalg.inv(first + second)))
    naive = np.sqrt(np.diag(np.linalg.inv(np.diag(np.diag(first) + np.diag(second)))))
    for index, name in enumerate(names):
        assert combined["sigma"][name] == pytest.approx(expected[index], rel=1e-12)
    # Dropping the off-diagonal blocks would move at least one error noticeably.
    assert np.max(np.abs(np.array(list(combined["sigma"].values())) / naive - 1.0)) > 1e-3


def test_format_table_has_one_row_per_case():
    results = [
        {
            "label": "Euclid",
            "elapsed_s": 1.5,
            "sigma": {name: 0.1 for name in module._free_parameters("LCDM")},
        },
        {
            "label": "Rubin",
            "elapsed_s": 2.5,
            "sigma": {name: 0.2 for name in module._free_parameters("LCDM")},
        },
    ]
    table = module.format_table(results, "LCDM")
    lines = [line for line in table.splitlines() if line.startswith("|")]
    assert len(lines) == 4  # header, separator, two cases
    assert "Euclid" in table and "Rubin" in table
