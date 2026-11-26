"""Fig. 1: Euclid photometric, spectroscopic and combined Fisher forecasts (symbolic backend)."""

from cosmicjellyfish.analysis.fishconsumer import make_triangle_plot
from cosmicjellyfish.analysis.fisher_operations import marginalise
from cosmicjellyfish.fishermatrix import cosmicfish as cff

fiducial = {"Omegam": 0.32, "Omegab": 0.05, "h": 0.67, "ns": 0.96, "sigma8": 0.815584}
freepars = {"Omegam": 0.01, "h": 0.01, "sigma8": 0.01}  # relative steps
params = ["Omegam", "h", "sigma8"]


def options(photo, spectro):
    return {
        "code": "symbolic",
        "accuracy": 1,
        "feedback": 0,
        "nonlinear": True,
        "derivatives": "3PT",
        "results_dir": "results",
        "outroot": "fig1",
        "survey_name": "Euclid",
        "survey_name_photo": photo,
        "survey_name_spectro": spectro,
    }


photo = cff.FisherMatrix(
    fiducialpars=fiducial,
    freepars=freepars,
    options=options("Euclid-Photometric-ISTF-Pessimistic", False),
    observables=["WL", "GCph"],
    cosmoModel="LCDM",
    surveyName="Euclid",
).compute()
spectro = cff.FisherMatrix(
    fiducialpars=fiducial,
    freepars=freepars,
    options=options(False, "Euclid-Spectroscopic-ISTF-Pessimistic"),
    observables=["GCsp"],
    cosmoModel="LCDM",
    surveyName="Euclid",
).compute()
combined = photo + spectro

for name, fisher in (("WL+GCph", photo), ("GCsp", spectro), ("combined", combined)):
    print(name, dict(zip(params, marginalise(fisher, params).get_confidence_bounds())))

for ext in ("pdf", "png"):
    make_triangle_plot(
        fishers=[spectro, photo, combined],
        fisher_labels=["GCsp", "WL+GCph", "WL+GCph+GCsp"],
        params=params,
        colors=["#2a9d8f", "#3a86ff", "#fb5607"],
        truth_values={p: fiducial[p] for p in params},
        legend_kwargs={"fontsize": 16, "loc": "upper right"},
        label_font_size=18,
        tick_font_size=11,
        figsize=(8, 8),
        savefile=f"fig1_euclid_probes.{ext}",
    )
