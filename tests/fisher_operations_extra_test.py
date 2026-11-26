import numpy as np
import pytest

from cosmicjellyfish.analysis import fisher_matrix as fm
from cosmicjellyfish.analysis import fisher_operations as fo


@pytest.fixture()
def simple_fisher():
    F = np.array([[4.0, 1.0, 0.5], [1.0, 3.0, 0.2], [0.5, 0.2, 2.0]])
    return fm.fisher_matrix(
        fisher_matrix=F,
        param_names=["a", "b", "c"],
        param_names_latex=["a", "b", "c"],
        fiducial=[1.0, 2.0, 3.0],
        name="Fbase",
    )


def test_eliminate_columns_rows_invalid_input():
    with pytest.raises(ValueError):
        fo.eliminate_columns_rows(np.eye(2), [0])  # not a fisher_matrix instance


def test_eliminate_parameters_missing(simple_fisher):
    with pytest.raises(ValueError):
        fo.eliminate_parameters(simple_fisher, ["d"])  # parameter does not exist


def test_reshuffle_missing_param(simple_fisher):
    with pytest.raises(ValueError):
        fo.reshuffle(simple_fisher, ["a", "d"])  # d missing


def test_reshuffle_update_names_false(simple_fisher):
    resh = fo.reshuffle(simple_fisher, ["c", "a"], update_names=False)
    assert resh.get_param_names() == ["c", "a"]
    # name unchanged because update_names=False
    assert resh.name == simple_fisher.name


def test_marginalise_missing_param(simple_fisher):
    with pytest.raises(ValueError):
        fo.marginalise(simple_fisher, ["a", "d"])  # d missing


def test_marginalise_update_names_false(simple_fisher):
    # keep only two parameters without appending suffix
    marg = fo.marginalise(simple_fisher, ["b", "a"], update_names=False)
    assert marg.get_param_names() == ["b", "a"]
    assert marg.name == simple_fisher.name  # unchanged


def test_marginalise_over_invalid_name(simple_fisher):
    with pytest.raises(ValueError):
        fo.marginalise_over(simple_fisher, ["d"])  # d missing


def test_information_gain_stat_paths(simple_fisher):
    """Exercise information_gain for both stat=False and stat=True branches."""
    F1 = simple_fisher
    # Slightly perturb F2 so determinants differ and trace terms non-trivial
    F2 = fm.fisher_matrix(
        fisher_matrix=F1.get_fisher_matrix() + np.diag([1e-3, -5e-4, 2e-3]),
        param_names=F1.get_param_names(),
        param_names_latex=F1.get_param_names_latex(),
        fiducial=F1.get_param_fiducial(),
        name="F2",
    )
    prior_matrix = fm.fisher_matrix(
        fisher_matrix=0.05 * np.eye(3),
        param_names=F1.get_param_names(),
        param_names_latex=F1.get_param_names_latex(),
        fiducial=F1.get_param_fiducial(),
        name="prior",
    )
    ig_no_stat = fo.information_gain(F1, F2, prior_matrix, stat=False)
    ig_with_stat = fo.information_gain(F1, F2, prior_matrix, stat=True)
    # Basic sanity: both are finite floats and stat=True adds extra positive contribution
    assert isinstance(ig_no_stat, float)
    assert isinstance(ig_with_stat, float)
    assert np.isfinite(ig_no_stat) and np.isfinite(ig_with_stat)
    assert ig_with_stat >= ig_no_stat


def test_information_gain_prior_is_optional(simple_fisher):
    """The prior can be omitted; identical Fishers gain nothing and different ones do."""
    F1 = simple_fisher
    assert fo.information_gain(F1, F1, None, stat=False) == pytest.approx(0.0, abs=1e-12)

    F2 = fm.fisher_matrix(
        fisher_matrix=0.5 * F1.get_fisher_matrix(),
        param_names=F1.get_param_names(),
        param_names_latex=F1.get_param_names_latex(),
        fiducial=F1.get_param_fiducial(),
        name="F2",
    )
    # Kullback-Leibler divergence between the two posteriors: positive in both directions
    assert fo.information_gain(F1, F2, stat=False) > 0.0
    assert fo.information_gain(F2, F1, stat=False) > 0.0
    # the same call with an explicit, negligible prior agrees
    prior = fm.fisher_matrix(
        fisher_matrix=1e-12 * np.eye(len(F1.get_param_names())),
        param_names=F1.get_param_names(),
        param_names_latex=F1.get_param_names_latex(),
        fiducial=F1.get_param_fiducial(),
        name="prior",
    )
    assert fo.information_gain(F1, F2, prior, stat=False) == pytest.approx(
        fo.information_gain(F1, F2, stat=False), rel=1e-6
    )


def test_information_gain_prior_may_add_a_parameter(simple_fisher):
    """A prior can supply a parameter that is absent from the second Fisher matrix.

    The prior-added matrices share it, so the statistical term must zero-pad it rather
    than ask ``reshuffle`` to extract it from ``fisher_2``.
    """
    F1 = simple_fisher
    names = F1.get_param_names()
    F2 = fm.fisher_matrix(
        fisher_matrix=F1.get_fisher_matrix()[:2, :2],
        param_names=names[:2],
        param_names_latex=names[:2],
        fiducial=F1.get_param_fiducial()[:2],
        name="F2_subset",
    )
    prior = fm.fisher_matrix(
        fisher_matrix=0.1 * np.eye(3),
        param_names=names,
        param_names_latex=F1.get_param_names_latex(),
        fiducial=F1.get_param_fiducial(),
        name="prior",
    )
    # ``c`` reaches the common set only through the prior.
    ig_no_stat = fo.information_gain(F1, F2, prior, stat=False)
    ig_with_stat = fo.information_gain(F1, F2, prior, stat=True)
    assert np.isfinite(ig_no_stat)
    assert np.isfinite(ig_with_stat)
    assert ig_with_stat >= ig_no_stat
