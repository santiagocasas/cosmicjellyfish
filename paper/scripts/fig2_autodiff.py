"""Fig. 2: autodiff versus finite-difference Fisher matrices with the jaxcosmo backend."""

import matplotlib.pyplot as plt
import numpy as np

from cosmicjellyfish.analysis.fishconsumer import make_triangle_plot
from cosmicjellyfish.fishermatrix.cosmicfish import FisherMatrix
from cosmicjellyfish.fishermatrix.jaxcosmo_derivatives import (
    JaxAutodiffProvider,
    JaxFiniteDifferenceProvider,
)

fiducial = {"10^9As": 2.1, "Omegam": 0.32, "Omegab": 0.05, "h": 0.67, "ns": 0.96, "mnu": 0.0}
cosmo = ["10^9As", "Omegam", "Omegab", "h"]
freepars = {name: 0.01 for name in cosmo}


def forecast(provider, outroot):
    options = {  # a fresh dictionary for each forecast
        "code": "jaxcosmo",
        "accuracy": 1,
        "feedback": 0,
        "nonlinear": True,
        "derivatives": "3PT",
        "results_dir": "results",
        "outroot": outroot,
        "survey_name_photo": "Euclid-Photometric-ISTF-Pessimistic",
    }
    return FisherMatrix(
        fiducialpars=fiducial,
        freepars=freepars,
        options=options,
        observables=["GCph", "WL"],
        cosmoModel="LCDM",
        surveyName="Euclid",
        derivative_provider=provider,
    ).compute()


fisher_ad = forecast(JaxAutodiffProvider(), "fig2_ad")
fisher_jfd = forecast(JaxFiniteDifferenceProvider(), "fig2_jaxfd")
fisher_fd = forecast(None, "fig2_fd")

names = fisher_ad.get_param_names()
assert names == fisher_jfd.get_param_names() == fisher_fd.get_param_names()
sig_ad = fisher_ad.get_confidence_bounds()
r_jfd = fisher_jfd.get_confidence_bounds() / sig_ad - 1
r_fd = fisher_fd.get_confidence_bounds() / sig_ad - 1


def dF(f):
    """Max relative deviation of a Fisher matrix from the autodiff one."""
    return (
        np.abs(f.fisher_matrix - fisher_ad.fisher_matrix).max()
        / np.abs(fisher_ad.fisher_matrix).max()
    )


print("max|dF|/max|F|  JAX FD:", dF(fisher_jfd), " standard FD:", dF(fisher_fd))
print("max |sigma ratio - 1|  JAX FD:", np.abs(r_jfd).max(), " standard FD:", np.abs(r_fd).max())
np.savetxt(
    "fig2_sigma_ratios.txt", np.c_[r_jfd, r_fd], header="JAXFD/AD-1 stdFD/AD-1  " + " ".join(names)
)

for ext in ("pdf", "png"):
    make_triangle_plot(
        fishers=[fisher_fd, fisher_ad],
        fisher_labels=["Finite differences (NumPy observable)", "Autodiff (JAX observable)"],
        params=cosmo,
        colors=["#3a86ff", "#fb5607"],
        ls_fisher=["-", "--"],
        truth_values={p: fiducial[p] for p in cosmo},
        param_labels={
            "10^9As": r"$10^9A_s$",
            "Omegam": r"$\Omega_m$",
            "Omegab": r"$\Omega_b$",
            "h": r"$h$",
        },
        legend_kwargs={"fontsize": 14, "loc": "upper right"},
        label_font_size=18,
        tick_font_size=10,
        figsize=(9, 9),
        savefile=f"fig2_autodiff_triangle.{ext}",
    )

tex = {
    "10^9As": r"$10^9A_s$",
    "Omegam": r"$\Omega_m$",
    "Omegab": r"$\Omega_b$",
    "h": r"$h$",
    "AIA": r"$A_{\rm IA}$",
    "betaIA": r"$\beta_{\rm IA}$",
    "etaIA": r"$\eta_{\rm IA}$",
}
labels = [tex.get(n, rf"$b_{{{n[1:]}}}$") for n in names]
x = np.arange(len(names))
fig, ax = plt.subplots(figsize=(8, 3.4))
ax.axhline(0, color="0.4", lw=0.8)
ax.plot(x, 100 * r_jfd, "o", color="#2a9d8f", label="finite differences, same JAX observable")
ax.plot(
    x, 100 * r_fd, "s", color="#3a86ff", mfc="none", label="finite differences, NumPy observable"
)
ax.set_xticks(x, labels)
ax.set_ylabel(r"$\sigma_{\rm FD}/\sigma_{\rm AD} - 1$  [%]")
ax.set_title("Marginalised errors relative to autodiff (Euclid WL+GCph, jaxcosmo)", fontsize=10)
ax.legend(frameon=False, fontsize=9)
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(f"fig2_autodiff_ratios.{ext}", dpi=200)
