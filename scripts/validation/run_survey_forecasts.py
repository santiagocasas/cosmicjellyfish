#!/usr/bin/env python
"""Run GR forecast comparisons for DESI, Rubin, SKAO and Planck.

This is the Phase 3 harness of ``docs/SURVEY_VALIDATION_ROADMAP.md``. Every configuration
is run at the same fiducial cosmology, with the same free parameters, derivative settings
and k/mu sampling, so the marginalised errors are directly comparable.

The output is a JSON file with the per-parameter errors plus a Markdown table, both written
to ``--output-dir`` (default ``results/survey_validation``). Combinations are built by
marginalising each probe over its own nuisance parameters and adding the resulting
cosmological blocks; this assumes the probes are statistically independent, which is stated
explicitly in the tables.

Usage
-----
::

    uv run python scripts/validation/run_survey_forecasts.py --list
    uv run python scripts/validation/run_survey_forecasts.py --case euclid-photo
    uv run python scripts/validation/run_survey_forecasts.py --model w0waCDM
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from cosmicjellyfish.analysis.fisher_operations import marginalise  # noqa: E402
from cosmicjellyfish.fishermatrix.cosmicfish import FisherMatrix  # noqa: E402

COMMON_FIDUCIAL = {
    "Omegam": 0.32,
    "Omegab": 0.05,
    "h": 0.67,
    "ns": 0.96,
    "sigma8": 0.822,
    # Fixed, not varied. Spelled out because the symbolic backend falls back to
    # 0.06 eV when the key is absent; do not describe these runs as massless.
    "mnu": 0.06,
}
# Relative finite-difference steps. The spectroscopic derivatives need a smaller step
# than the photometric ones: at 1% the GCsp Fisher matrix is not converged (sigma8 moves
# by ~25% between 1% and 0.2%), while 0.2% agrees with 0.05% to better than 0.1%. The
# photometric probes are stable at the 0.03% level between the two steps.
DERIVATIVE_STEP = 0.002
LCDM_FREE = dict.fromkeys(("Omegam", "Omegab", "h", "ns", "sigma8"), DERIVATIVE_STEP)
W0WA_FREE = {**LCDM_FREE, "w0": 0.02, "wa": 0.02}
BASE_OPTIONS = {
    "code": "symbolic",
    "nonlinear": True,
    "feedback": 0,
    "derivatives": "3PT",
}


@dataclass(frozen=True)
class ForecastCase:
    """One survey/probe combination to run."""

    name: str
    label: str
    survey: str
    observables: tuple[str, ...]
    options: dict = field(default_factory=dict)
    note: str = ""


CASES: dict[str, ForecastCase] = {
    "euclid-photo": ForecastCase(
        name="euclid-photo",
        label="Euclid photometric (GCph+WL)",
        survey="Euclid",
        observables=("GCph", "WL"),
        note="shipped Euclid-Photometric-ISTF-Pessimistic",
    ),
    "rubin-photo": ForecastCase(
        name="rubin-photo",
        label="Rubin/LSST photometric (GCph+WL)",
        survey="Rubin",
        observables=("GCph", "WL"),
        options={"survey_name_photo": "Rubin-Photometric-SKAOPaper"},
        note="historical Rubin-Optimistic transcription",
    ),
    "euclid-spectro": ForecastCase(
        name="euclid-spectro",
        label="Euclid spectroscopic (GCsp)",
        survey="Euclid",
        observables=("GCsp",),
        note="shipped Euclid-Spectroscopic-ISTF-Pessimistic",
    ),
    "desi-bgs": ForecastCase(
        name="desi-bgs",
        label="DESI BGS (GCsp)",
        survey="DESI",
        observables=("GCsp",),
        options={"survey_name_spectro": "DESI-BGS-SKAOPaper"},
        note="bright-galaxy sample, 0 < z < 0.5",
    ),
    "desi-elg": ForecastCase(
        name="desi-elg",
        label="DESI ELG (GCsp)",
        survey="DESI",
        observables=("GCsp",),
        options={"survey_name_spectro": "DESI-ELG-SKAOPaper"},
        note="emission-line galaxies, 0.6 < z < 1.7",
    ),
    "desi2023-bgs": ForecastCase(
        name="desi2023-bgs",
        label="DESI 2023 BGS (GCsp)",
        survey="DESI",
        observables=("GCsp",),
        options={"survey_name_spectro": "DESI-BGS-Validation2023"},
        note="arXiv:2306.06307 Table 7, BGS Bright, 0 < z < 0.4",
    ),
    "desi2023-lrg": ForecastCase(
        name="desi2023-lrg",
        label="DESI 2023 LRG (GCsp)",
        survey="DESI",
        observables=("GCsp",),
        options={"survey_name_spectro": "DESI-LRG-Validation2023"},
        note="arXiv:2306.06307 Table 7, luminous red galaxies, 0.4 < z < 1.1",
    ),
    "desi2023-elg": ForecastCase(
        name="desi2023-elg",
        label="DESI 2023 ELG (GCsp)",
        survey="DESI",
        observables=("GCsp",),
        options={"survey_name_spectro": "DESI-ELG-Validation2023"},
        note="arXiv:2306.06307 Table 7, ELG_LOP, 1.1 < z < 1.6",
    ),
    "desi2023-qso": ForecastCase(
        name="desi2023-qso",
        label="DESI 2023 QSO (GCsp)",
        survey="DESI",
        observables=("GCsp",),
        options={"survey_name_spectro": "DESI-QSO-Validation2023"},
        note="arXiv:2306.06307 Table 7, clustering quasars, 1.6 < z < 2.1",
    ),
    "skao-photo": ForecastCase(
        name="skao-photo",
        label="SKAO continuum photometric (GCph+WL)",
        survey="SKAO",
        observables=("GCph", "WL"),
        options={"survey_name_photo": "SKAO-Photometric-SKAOPaper"},
        note="paper-era scale cuts (lmax 1500/5000)",
    ),
    "skao-hi": ForecastCase(
        name="skao-hi",
        label="SKAO HI galaxies (GCsp)",
        survey="SKAO",
        observables=("GCsp",),
        options={"survey_name_spectro": "SKAO-Spectroscopic-SKAOPaper"},
        note="HI galaxy clustering, 0 < z < 0.5",
    ),
    "skao-im": ForecastCase(
        name="skao-im",
        label="SKAO intensity mapping (IM)",
        survey="SKAO",
        observables=("IM",),
        note="10 redshift bins, 0.5 < z < 2.6",
    ),
    "skao-im-desi": ForecastCase(
        name="skao-im-desi",
        label="SKAO IM x DESI ELG cross",
        survey="SKAO",
        observables=("GCspxIM",),
        options={
            "survey_name_spectro": "DESI-ELG-SKAOPaper",
            "survey_name_radio_IM": "SKAO-IM-Redbook-DESI-ELG",
        },
        note="cross-spectrum only, aligned bins, no auto-spectra",
    ),
    "skao-im-desi-joint": ForecastCase(
        name="skao-im-desi-joint",
        label="SKAO IM x DESI ELG (auto + cross)",
        survey="SKAO",
        observables=("GCsp", "GCspxIM", "IM"),
        options={
            "survey_name_spectro": "DESI-ELG-SKAOPaper",
            "survey_name_radio_IM": "SKAO-IM-Redbook-DESI-ELG",
        },
        note="DESI ELG auto + IM auto + cross with the full 2x2 covariance, aligned bins",
    ),
    "planck": ForecastCase(
        name="planck",
        label="Planck-like CMB (TT+TE+EE)",
        survey="Planck",
        observables=("CMB_T", "CMB_E"),
        options={"code": "camb"},
        note="shipped Planck.yaml, no lensing; CAMB is required for CMB spectra",
    ),
}

COMBINATIONS: dict[str, tuple[str, ...]] = {
    "desi-combined": ("desi-bgs", "desi-elg"),
    "desi2023-combined": ("desi2023-bgs", "desi2023-lrg", "desi2023-elg", "desi2023-qso"),
    "euclid-combined": ("euclid-photo", "euclid-spectro"),
}


def _camb_cmb_yaml(output_dir: Path) -> Path:
    """Copy the default CAMB configuration and enable the CMB spectra."""
    base = (
        REPO_ROOT
        / "cosmicjellyfish"
        / "configs"
        / "default_boltzmann_yaml_files"
        / "camb"
        / "default.yaml"
    )
    config = yaml.safe_load(base.read_text(encoding="utf-8"))
    config.setdefault("COSMO_SETTINGS", {})
    config["COSMO_SETTINGS"]["WantCls"] = True
    config["COSMO_SETTINGS"]["Want_CMB"] = True
    config["COSMO_SETTINGS"]["Want_CMB_lensing"] = False
    config["COSMO_SETTINGS"]["Want_cl_2D_array"] = False
    path = output_dir / "camb_cmb_enabled.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return path


def _free_parameters(model: str) -> dict[str, float]:
    if model == "LCDM":
        return dict(LCDM_FREE)
    if model == "w0waCDM":
        return dict(W0WA_FREE)
    raise ValueError(f"Unsupported model {model!r}")


def _effective_settings(fisher: FisherMatrix, case: ForecastCase, model: str) -> dict:
    """Record the settings that actually entered the run, not just the requested ones."""
    settings = fisher.settings
    specs = fisher.specs
    names = list(_free_parameters(model))

    def finite_or_none(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None
        return value if np.isfinite(value) else None

    return {
        "code": settings.get("code"),
        "cosmo_model": model,
        "nonlinear": bool(settings.get("nonlinear", False)),
        "derivatives": settings.get("derivatives"),
        "derivative_step": float(_free_parameters(model)[names[0]]),
        "spectro_Pk_k_samples": settings.get("spectro_Pk_k_samples"),
        "spectro_Pk_mu_samples": settings.get("spectro_Pk_mu_samples"),
        "kmin_fish": finite_or_none(getattr(fisher, "kmin_fish", None)),
        "kmax_fish": finite_or_none(getattr(fisher, "kmax_fish", None)),
        "fsky_spectro": specs.get("fsky_spectro"),
        "fsky_IM": specs.get("fsky_IM"),
        "spec_sigma_dz": specs.get("spec_sigma_dz"),
        "mnu": fisher.fiducialcosmopars.get("mnu"),
        "observables": list(case.observables),
    }


def _environment() -> dict:
    """Versions of the interpreter and the packages that can change the numbers."""
    from importlib import metadata
    from platform import python_version

    def version(package: str):
        try:
            return metadata.version(package)
        except metadata.PackageNotFoundError:
            return None

    return {
        "python": python_version(),
        "cosmicjellyfish": version("cosmicjellyfish"),
        "symbolic-pofk": version("symbolic-pofk"),
        "camb": version("camb"),
        "classy": version("classy"),
    }


def run_case(case: ForecastCase, model: str, output_dir: Path) -> dict:
    """Run one forecast and return the marginalised errors."""
    options = dict(BASE_OPTIONS)
    options["cosmo_model"] = model
    options["results_dir"] = str(output_dir / "fishers")
    options["outroot"] = f"survey_forecast_{model.lower()}_{case.name.replace('-', '_')}"
    options.update(case.options)
    if case.survey == "Planck":
        options["camb_config_yaml"] = str(_camb_cmb_yaml(output_dir))
        options["survey_name_photo"] = False
        options["survey_name_spectro"] = False

    fiducial = dict(COMMON_FIDUCIAL)
    if model == "w0waCDM":
        fiducial.update({"w0": -1.0, "wa": 0.0})
    freepars = _free_parameters(model)
    start = time.perf_counter()
    fisher = FisherMatrix(
        options=options,
        observables=list(case.observables),
        freepars=freepars,
        fiducialpars=fiducial,
        surveyName=case.survey,
        cosmoModel=model,
    )
    matrix = fisher.compute()
    elapsed = time.perf_counter() - start

    names = list(freepars)
    reduced = marginalise(matrix, names)
    fisher_block = np.asarray(reduced.fisher_matrix, dtype=float)
    covariance = np.linalg.inv(fisher_block)
    sigma = {name: float(np.sqrt(covariance[i, i])) for i, name in enumerate(names)}

    result = {
        "name": case.name,
        "label": case.label,
        "observables": list(case.observables),
        "note": case.note,
        "elapsed_s": elapsed,
        "sigma": sigma,
        # Keep the full nuisance-marginalised Fisher block so combinations sum matrices
        # rather than discarding the parameter correlations.
        "fisher_matrix": fisher_block.tolist(),
        "settings": _effective_settings(fisher, case, model),
    }
    if model == "w0waCDM":
        block = covariance[-2:, -2:]
        result["fom_w0wa"] = float(1.0 / np.sqrt(np.linalg.det(block)))
    return result


def combine(results: dict[str, dict], members: tuple[str, ...], model: str) -> dict:
    """Add independent nuisance-marginalised Fisher blocks.

    Each probe is first marginalised over its own nuisances, which leaves a
    cosmological block that still carries the correlations between parameters. Those
    blocks are added as matrices; the marginalised errors are then read from the
    inverse of the sum. Rebuilding each block from its diagonal errors would assume the
    cosmological parameters are uncorrelated and is not a Fisher combination.

    Every member must provide its full block in the parameter order of ``model``. A
    missing block raises instead of silently falling back to a diagonal matrix, because
    that fallback would reintroduce exactly the approximation this function avoids.
    """
    names = list(_free_parameters(model))
    total = np.zeros((len(names), len(names)))
    for member in members:
        block = results[member].get("fisher_matrix")
        if block is None:
            raise ValueError(
                f"{member!r} has no stored Fisher block; rerun the forecasts with the "
                "current script before combining them"
            )
        block = np.asarray(block, dtype=float)
        if block.shape != (len(names), len(names)):
            raise ValueError(
                f"{member!r} has a Fisher block of shape {block.shape}, expected "
                f"{(len(names), len(names))} for {model}"
            )
        total = total + block
    covariance = np.linalg.inv(total)
    sigma = {name: float(np.sqrt(covariance[i, i])) for i, name in enumerate(names)}
    result = {
        "name": "+".join(members),
        "label": " + ".join(results[member]["label"] for member in members),
        "observables": sorted(
            {obs for member in members for obs in results[member]["observables"]}
        ),
        "note": "sum of independent, nuisance-marginalised blocks",
        "elapsed_s": float(sum(results[member]["elapsed_s"] for member in members)),
        "sigma": sigma,
        # Store the summed block so a combination can itself enter a further
        # combination or a Fisher-space figure without being rebuilt from diagonals.
        "fisher_matrix": total.tolist(),
    }
    if model == "w0waCDM":
        block = covariance[-2:, -2:]
        result["fom_w0wa"] = float(1.0 / np.sqrt(np.linalg.det(block)))
    return result


def format_table(results: list[dict], model: str) -> str:
    """Render the marginalised errors as a Markdown table."""
    names = list(_free_parameters(model))
    header = "| Case | " + " | ".join(names) + " | Time (s) |"
    separator = "| --- |" + " --- |" * len(names) + " --- |"
    lines = [header, separator]
    for result in results:
        cells = " | ".join(f"{result['sigma'][name]:.4g}" for name in names)
        lines.append(f"| {result['label']} | {cells} | {result['elapsed_s']:.1f} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", choices=sorted(CASES), help="Case (repeatable).")
    parser.add_argument("--model", choices=("LCDM", "w0waCDM"), default="LCDM")
    parser.add_argument("--list", action="store_true", help="List the available cases and exit.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "results" / "survey_validation",
        help="Directory for the JSON and Markdown reports.",
    )
    args = parser.parse_args(argv)

    if args.list:
        for name, case in CASES.items():
            print(f"{name:<16} {case.label}  [{', '.join(case.observables)}]")
        return 0

    selected = args.case or list(CASES)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, dict] = {}
    for name in selected:
        case = CASES[name]
        print(f"Running {case.label} ...", flush=True)
        try:
            results[name] = run_case(case, args.model, args.output_dir)
        except Exception as error:  # noqa: BLE001 - report and keep going
            print(f"  failed: {error}")
            results[name] = {"name": name, "label": case.label, "error": repr(error)}

    completed = {name: value for name, value in results.items() if "sigma" in value}
    for name, members in COMBINATIONS.items():
        if all(member in completed for member in members):
            results[name] = combine(completed, members, args.model)

    ordered = [value for value in results.values() if "sigma" in value]
    table = format_table(ordered, args.model)
    print()
    print(table)

    fiducial = dict(COMMON_FIDUCIAL)
    if args.model == "w0waCDM":
        fiducial.update({"w0": -1.0, "wa": 0.0})
    report = {
        "model": args.model,
        "fiducial": fiducial,
        "freepars": _free_parameters(args.model),
        "options": BASE_OPTIONS,
        "environment": _environment(),
        "results": ordered,
        "errors": [
            {"name": value["name"], "label": value["label"], "error": value["error"]}
            for value in results.values()
            if "error" in value
        ],
    }
    json_path = args.output_dir / f"survey_forecasts_{args.model}.json"
    json_path.write_text(json.dumps(report, indent=2))

    markdown_path = args.output_dir / f"survey_forecasts_{args.model}.md"
    notes = "\n".join(
        f"- **{result['label']}**: {result['note']}" for result in ordered if result["note"]
    )
    markdown_path.write_text(f"{table}\n\nNotes\n\n{notes}\n")

    print(f"\nWrote {json_path}")
    print(f"Wrote {markdown_path}")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
