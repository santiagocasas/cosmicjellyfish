"""Which spectra a spectroscopic forecast uses: galaxy auto, IM auto, cross or all three.

The user-facing observable names are

``GCsp``
    galaxy auto-spectrum :math:`P_{gg}`,
``IM``
    intensity-mapping auto-spectrum :math:`P_{II}`,
``GCspxIM``
    galaxy x intensity-mapping cross-spectrum :math:`P_{Ig}` only.

Listing all three, or listing ``GCspxIM`` with the option ``spectro_joint=True``, asks for a
*joint* analysis in which :math:`P_{gg}`, :math:`P_{Ig}` and :math:`P_{II}` are treated
together with their full Gaussian covariance, so that the shared modes are counted once.

The pre-2.1 spelling ``["GCsp", "IM"]`` selected the cross-spectrum only. It is still
accepted as a deprecated alias for ``["GCspxIM"]`` and emits a ``FutureWarning``.

Notes
-----
This module only depends on NumPy so that it can be imported by the configuration code.
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence

import numpy as np

SPECTRO_OBSERVABLES = ("GCsp", "IM", "GCspxIM")

#: spectrum modes: auto galaxy, auto IM, cross-spectrum only, and the joint analysis
MODES = ("gg", "II", "Ig", "joint")


def resolve_spectro_observables(
    observables: Sequence[str], joint: bool = False
) -> tuple[list[str], str | None]:
    """Normalise the spectroscopic part of an observables list.

    Parameters
    ----------
    observables : sequence of str
        Observables requested by the user.
    joint : bool, optional
        Ask for the joint auto + cross analysis when ``GCspxIM`` is requested.

    Returns
    -------
    observables : list of str
        The list with the spectroscopic entries canonicalised. A cross or joint analysis
        always contains ``GCsp``, ``IM`` and ``GCspxIM``, because it needs the galaxy and the
        intensity-mapping nuisance parameters.
    mode : str or None
        One of ``"gg"``, ``"II"``, ``"Ig"``, ``"joint"``; ``None`` without spectroscopic probes.

    Raises
    ------
    ValueError
        If ``GCspxIM`` is combined with only one of ``GCsp`` and ``IM``.
    """
    requested = list(observables)
    gc = "GCsp" in requested
    im = "IM" in requested
    cross = "GCspxIM" in requested
    if not (gc or im or cross):
        return requested, None

    if cross and (gc != im):
        raise ValueError(
            "'GCspxIM' is the cross-spectrum. List it alone for the cross-spectrum only, or "
            "together with both 'GCsp' and 'IM' (or with the option spectro_joint=True) for the "
            "joint auto + cross analysis."
        )
    if gc and im and not cross:
        warnings.warn(
            "observables ['GCsp', 'IM'] select the cross-spectrum only; this spelling is "
            "deprecated. Use ['GCspxIM'] for the cross-spectrum, or ['GCsp', 'GCspxIM', 'IM'] "
            "(or spectro_joint=True) for the joint auto + cross analysis.",
            FutureWarning,
            stacklevel=3,
        )
        mode = "Ig"
    elif cross:
        mode = "joint" if (joint or (gc and im)) else "Ig"
    elif im:
        mode = "II"
    else:
        mode = "gg"

    others = [name for name in requested if name not in SPECTRO_OBSERVABLES]
    if mode in ("Ig", "joint"):
        spectro = ["GCsp", "IM", "GCspxIM"]
    elif mode == "II":
        spectro = ["IM"]
    else:
        spectro = ["GCsp"]
    return others + spectro, mode


def spectro_mode(observables: Sequence[str], settings: Mapping | None = None) -> str | None:
    """Return the spectrum mode of an already resolved forecast.

    The mode stored by the configuration in ``settings["spectro_mode"]`` wins. Without it,
    the mode is read from the observables list, with the legacy ``["GCsp", "IM"]`` pair
    meaning the cross-spectrum.
    """
    if settings is not None and settings.get("spectro_mode"):
        return settings["spectro_mode"]
    gc = "GCsp" in observables
    im = "IM" in observables
    if gc and im:
        return "Ig"
    if im:
        return "II"
    if gc:
        return "gg"
    return None


def replay_observables(observables: Sequence[str], mode: str | None) -> list[str]:
    """Return an observables request that resolves again to the recorded ``mode``.

    A forecast records its *resolved* observables. For a cross-only run that is the same
    three-name list a user passes to ask for the joint analysis, so resolving it again would
    turn ``"Ig"`` into ``"joint"``. A recorded ``"Ig"`` is therefore mapped back to the
    unambiguous request ``GCspxIM``; every other mode, and any list that is not a resolved
    cross/joint triplet, is returned unchanged. Explicit user requests are never altered:
    only snapshot replay calls this.
    """
    names = list(observables)
    if mode == "Ig" and set(SPECTRO_OBSERVABLES) <= set(names):
        return [name for name in names if name not in SPECTRO_OBSERVABLES] + ["GCspxIM"]
    return names


def output_tag(mode: str | None) -> str:
    """Return the file-name suffix that keeps cross-only and joint forecasts apart.

    A cross-only (``"Ig"``) and a joint forecast both resolve to the observables
    ``["GCsp", "IM", "GCspxIM"]``, so the observables alone cannot tell their output files
    apart. Those two modes get ``"_Ig"`` and ``"_joint"``. The auto-spectrum modes (``"gg"``,
    ``"II"``) are already unique through their observables and, like forecasts without
    spectroscopic probes (``None``), get no suffix, so their file names do not change.
    """
    return f"_{mode}" if mode in ("Ig", "joint") else ""


def spectrum_pair(mode: str | None) -> list[str] | None:
    """Return the ``[si, sj]`` pair that labels the (first) spectrum of a mode."""
    return {"gg": ["g", "g"], "II": ["I", "I"], "Ig": ["I", "g"], "joint": ["I", "g"]}.get(mode)


def joint_gaussian_trace(
    cov_II: np.ndarray,
    cov_Ig: np.ndarray,
    cov_gg: np.ndarray,
    d_II: Sequence[np.ndarray],
    d_Ig: Sequence[np.ndarray],
    d_gg: Sequence[np.ndarray],
) -> np.ndarray:
    r"""Gaussian Fisher kernel :math:`\mathrm{Tr}[C^{-1}\partial_p C\, C^{-1}\partial_q C]`.

    At every :math:`(k, \mu)` the data are the two fields :math:`(I, g)` with the
    :math:`2\times 2` covariance

    .. math::
        C = \begin{pmatrix} P_{II} + N_I & P_{Ig} \\ P_{Ig} & P_{gg} + N_g \end{pmatrix},

    and the Fisher matrix of one mode is :math:`\tfrac{V}{2}\int \mathrm{d}^3k/(2\pi)^3`
    times this trace. With a single tracer it reduces to
    :math:`(\partial_p P\,\partial_q P)/(P+N)^2`.

    Parameters
    ----------
    cov_II, cov_Ig, cov_gg : numpy.ndarray
        Entries of :math:`C`, including noise on the diagonal, all on the same grid.
    d_II, d_Ig, d_gg : sequence of numpy.ndarray
        Derivatives of the three *spectra* (not of their logarithms), one array per parameter.

    Returns
    -------
    numpy.ndarray
        Array of shape ``(n_par, n_par) + grid.shape``.
    """
    det = cov_II * cov_gg - cov_Ig**2
    if np.any(det <= 0):
        raise ValueError("The (I, g) covariance is not positive definite on the k-mu grid.")
    inverse = np.stack([np.stack([cov_gg, -cov_Ig]), np.stack([-cov_Ig, cov_II])]) / det
    # derivative has shape (n_par, 2, 2, *grid); M_p = C^-1 dC_p
    derivative = np.stack(
        [np.stack([np.stack([a, b]), np.stack([b, c])]) for a, b, c in zip(d_II, d_Ig, d_gg)]
    )
    matrix = np.einsum("ab...,pbc...->pac...", inverse, derivative)
    return np.einsum("pab...,qba...->pq...", matrix, matrix)
