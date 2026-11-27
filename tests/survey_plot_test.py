"""Unit tests for the survey-validation figure helpers.

The plotting script is not imported by the library, but the marginalised covariance it
extracts decides what the published ellipses mean, so it is worth pinning.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validation" / "plot_survey_validation.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("plot_survey_validation", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


module = _load_module()


def _report(block: np.ndarray) -> dict:
    names = ["Omegam", "h", "w0", "wa"]
    return {
        "freepars": {name: 0.01 for name in names},
        "results": [
            {
                "name": "probe",
                "label": "probe",
                "observables": ["GCsp"],
                "note": "",
                "elapsed_s": 1.0,
                "sigma": {name: 0.1 for name in names},
                "fisher_matrix": block.tolist(),
            }
        ],
    }


def test_w0wa_covariance_is_marginalised_not_conditional():
    # Correlate w0/wa with the shape parameters so the two answers differ.
    block = np.array(
        [
            [4.0, 0.5, -2.0, 0.3],
            [0.5, 3.0, 0.4, 0.2],
            [-2.0, 0.4, 2.0, -1.2],
            [0.3, 0.2, -1.2, 1.5],
        ]
    )
    covariance = module._w0wa_covariance(_report(block), ("probe",))
    indices = [2, 3]
    marginalised = np.linalg.inv(block)[np.ix_(indices, indices)]
    conditional = np.linalg.inv(block[np.ix_(indices, indices)])
    assert np.allclose(covariance, marginalised)
    assert not np.allclose(covariance, conditional)


def test_w0wa_covariance_sums_the_requested_blocks():
    first = np.diag([1.0, 1.0, 100.0, 100.0])
    second = np.diag([1.0, 1.0, 300.0, 300.0])
    report = _report(first)
    report["results"].append(
        {**report["results"][0], "name": "other", "fisher_matrix": second.tolist()}
    )
    combined = module._w0wa_covariance(report, ("probe", "other"))
    expected = np.linalg.inv(first + second)[2:, 2:]
    assert np.allclose(combined, expected)


def test_w0wa_covariance_rejects_a_missing_case():
    with pytest.raises(KeyError, match="missing"):
        module._w0wa_covariance(_report(np.eye(4)), ("absent",))


def test_w0wa_covariance_rejects_a_report_without_blocks():
    report = _report(np.eye(4))
    report["results"][0].pop("fisher_matrix")
    with pytest.raises(ValueError, match="no stored Fisher block"):
        module._w0wa_covariance(report, ("probe",))
