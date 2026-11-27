"""Nonlinear boosts B(k, z) = P_NL^{f(R)} / P_NL^{LCDM} for Hu-Sawicki f(R) (n = 1), used by
cosmicjellyfish/cosmology/modified_gravity.py.

``MGfit_Winther.py`` is a verbatim copy (unmodified, sha256
7d7d09ac01009df4b03be4e029ffaa4475264b2539728b8d036aec8e39a34629) of
https://github.com/Sefa76/photometric_fofR/blob/main/codes/MGfit_Winther.py (commit bb63de1,
2023-07-07), the file imported by the MontePython likelihood ``euclid_photometric_z_fofr`` of that
repository. It is the fitting formula of Winther, Casas, Baldi, Koyama, Li, Lombriser, Zhao (2019),
arXiv:1903.08798 (original code: https://github.com/HAWinther/FofrFittingFunction), as used in
Euclid Collaboration: Casas et al. (2023), arXiv:2306.11053, and Euclid Collaboration: Koyama et
al. (2024), arXiv:2409.03524. Its ``kazuya_correktion`` (sigma8 of f(R) from the linear fit,
matched to MGCAMB) is not used here: the f(R) sigma8 comes directly from the f(R) Boltzmann code.

e-MANTIS is the pip package ``emantis`` (Saez-Casares, Rasera, Li 2023, arXiv:2303.08899), class
``FofrBoost``.
"""
