"""Import-error guidance for the optional ``symbolic_pofk`` dependency."""

from __future__ import annotations

import builtins
import sys
from types import SimpleNamespace

import pytest

from cosmicjellyfish.cosmology.cosmology import boltzmann_code
from cosmicjellyfish.cosmology.symbolic_new import (
    SYMBOLIC_POFK_INSTALL_HINT,
    import_symbolic_pofk,
)


def _legacy_symbolic_configuration():
    """Minimal explicit configuration selecting the legacy symbolic provider."""
    return SimpleNamespace(
        settings={
            "feedback": 0,
            "SUPPRESS_WARNINGS": True,
            "colossus_persistence": "",
            "cosmo_model": "LCDM",
        },
        input_type="symbolic",
        backend_parameters={
            "ACCURACY": {"provider": "legacy"},
            "COSMO_SETTINGS": {"halofit_version": "takahashi"},
            "NUMERICS": {"extrapolate": False},
        },
    )


def _block_imports(monkeypatch, blocked_prefix):
    """Make ``import <blocked_prefix>...`` raise ImportError."""
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == blocked_prefix or name.startswith(blocked_prefix + "."):
            raise ImportError(f"blocked {name}")
        return real_import(name, *args, **kwargs)

    for module in [m for m in sys.modules if m.split(".")[0] == blocked_prefix]:
        monkeypatch.delitem(sys.modules, module)
    monkeypatch.setattr(builtins, "__import__", fake_import)


def test_import_symbolic_pofk_missing_module_gives_install_hint():
    with pytest.raises(ImportError) as excinfo:
        import_symbolic_pofk("this_module_does_not_exist")
    assert str(excinfo.value) == SYMBOLIC_POFK_INSTALL_HINT
    assert "pip install git+https://github.com/DeaglanBartlett/symbolic_pofk.git" in str(
        excinfo.value
    )
    assert isinstance(excinfo.value.__cause__, ImportError)


def test_legacy_symbolic_without_symbolic_pofk_gives_install_hint(monkeypatch):
    pytest.importorskip("colossus")
    _block_imports(monkeypatch, "symbolic_pofk")
    with pytest.raises(ImportError) as excinfo:
        boltzmann_code(
            {"Omegam": 0.32, "Omegab": 0.05, "h": 0.67, "ns": 0.96, "sigma8": 0.8},
            code="symbolic",
            configuration=_legacy_symbolic_configuration(),
        )
    assert str(excinfo.value) == SYMBOLIC_POFK_INSTALL_HINT


def test_legacy_symbolic_without_colossus_does_not_blame_symbolic_pofk(monkeypatch):
    _block_imports(monkeypatch, "colossus")
    with pytest.raises(ImportError) as excinfo:
        boltzmann_code(
            {"Omegam": 0.32, "Omegab": 0.05, "h": 0.67, "ns": 0.96, "sigma8": 0.8},
            code="symbolic",
            configuration=_legacy_symbolic_configuration(),
        )
    assert "colossus" in str(excinfo.value)
    assert "symbolic_pofk" not in str(excinfo.value)
