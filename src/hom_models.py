"""Model functions for the Hong-Ou-Mandel (HOM) dip of quantum-dot photons.

All models have the common form

    C(x) = A * [1 - V * K(x - x0)],       K(0) <= 1,

where x is the stage position (cm), A is the coincidence level for fully
distinguishable photons (arbitrary normalisation), V is the interference
amplitude and K is the normalised overlap kernel.

Physics (see paper/ for derivation):
  * A two-level emitter with radiative lifetime T1 and pure dephasing
    rate gamma* emits photons whose HOM overlap, integrated over detection
    times, is  (T2 / 2 T1) * exp(-|tau| / T1)  (Kiraz et al., PRA 69, 032305).
    -> kernel K_exp(u) = exp(-|u| / L), L = c T1 (single pass).
  * A random emission (excitation) time t0 of each photon makes the photon
    state mixed; Tr(rho_a rho_b) is then the exponential kernel convolved with
    the distribution of t0a - t0b.  For Gaussian timing jitter of rms s_1 per
    photon, the difference is Gaussian with s = sqrt(2) s_1:
        K_EG(u) = [exp(-|.|/L) (*) N(0, s^2)](u)       (exponentially modified
                                                         Gaussian, two-sided)
    For exponential feeding (non-resonant relaxation, time constant l_r),
    the difference is Laplace distributed:
        K_EL(u) = [b/(b^2-a^2)] (b e^{-a|u|} - a e^{-b|u|}),  a=1/L, b=1/l_r.
  * Reference (non-physical for a QD) shapes: Gaussian and Lorentzian dips.
"""
import numpy as np
from scipy.special import erfc, erfcx

C_LIGHT_CM_PER_PS = 2.99792458e-2   # speed of light, cm / ps
N_GROUP_AIR = 1.00028               # group index of air near 900-950 nm


def kernel_exp(u, L):
    return np.exp(-np.abs(u) / L)


def kernel_exp_gauss(u, L, s):
    """exp(-|u|/L) convolved with a unit-area Gaussian of rms s.

    Numerically stable form using the scaled complementary error function
    erfcx(z) = exp(z^2) erfc(z)  (u >= 0 by symmetry):
      K = 0.5 e^{s^2/2L^2 - u/L} erfc((s/L - u/s)/sqrt2)
        + 0.5 e^{-u^2/2s^2} erfcx((s/L + u/s)/sqrt2)
    """
    u = np.abs(np.asarray(u, dtype=float))      # kernel is even
    r2 = np.sqrt(2.0)
    # first term written with erfc (bounded), second with erfcx (no underflow)
    t1 = 0.5 * np.exp(s * s / (2 * L * L) - u / L) * erfc((s / L - u / s) / r2)
    t2 = 0.5 * np.exp(-u * u / (2 * s * s)) * erfcx((s / L + u / s) / r2)
    return t1 + t2


def kernel_exp_laplace(u, L, lr):
    a, b = 1.0 / L, 1.0 / lr
    u = np.abs(u)
    return b / (b * b - a * a) * (b * np.exp(-a * u) - a * np.exp(-b * u))


def kernel_gauss(u, s):
    return np.exp(-u * u / (2 * s * s))


def kernel_lorentz(u, g):
    return 1.0 / (1.0 + (u / g) ** 2)


# ---- full models:  C(x) = A (1 - V K(x - x0)) --------------------------------
def m_exp(x, A, V, x0, L):
    return A * (1 - V * kernel_exp(x - x0, L))


def m_exp_gauss(x, A, V, x0, L, s):
    return A * (1 - V * kernel_exp_gauss(x - x0, L, s))


def m_exp_laplace(x, A, V, x0, L, lr):
    return A * (1 - V * kernel_exp_laplace(x - x0, L, lr))


def m_gauss(x, A, V, x0, s):
    return A * (1 - V * kernel_gauss(x - x0, s))


def m_lorentz(x, A, V, x0, g):
    return A * (1 - V * kernel_lorentz(x - x0, g))


def m_exp_gauss_asym(x, A, V, x0, L1, L2, s):
    """Different decay lengths on the two sides (symmetry test only)."""
    u = x - x0
    return np.where(u < 0,
                    A * (1 - V * kernel_exp_gauss(u, L1, s)),
                    A * (1 - V * kernel_exp_gauss(u, L2, s)))


def m_exp_gauss_coherent(x, A, V, x0, L, s):
    """Pure-state (coherently shaped) wave packet psi = g (*) exp(-t/2T1):
    |<psi|psi_tau>|^2 = [G (*) exp(-|u|/2L)]^2 / [same at 0]^2 ; V is then the
    zero-delay visibility itself."""
    k = kernel_exp_gauss(x - x0, 2 * L, s)
    k0 = kernel_exp_gauss(np.array([0.0]), 2 * L, s)[0]
    return A * (1 - V * (k / k0) ** 2)


MODELS = {
    # name: (function, parameter names, initial guess, description)
    "exp":         (m_exp, ["A", "V", "x0", "L"], [0.52, 0.9, 1.4, 4.0],
                    "two-level emitter, no timing jitter"),
    "exp*gauss":   (m_exp_gauss, ["A", "V", "x0", "L", "s"], [0.52, 0.9, 1.4, 4.0, 0.5],
                    "emitter + Gaussian emission-time jitter (main model)"),
    "exp*laplace": (m_exp_laplace, ["A", "V", "x0", "L", "lr"], [0.52, 0.9, 1.4, 4.0, 0.4],
                    "emitter + exponential feeding jitter"),
    "coherent":    (m_exp_gauss_coherent, ["A", "V", "x0", "L", "s"], [0.52, 0.85, 1.4, 4.0, 0.5],
                    "pure wave packet shaped by Gaussian excitation"),
    "gauss":       (m_gauss, ["A", "V", "x0", "s"], [0.5, 0.8, 1.4, 4.0],
                    "Gaussian spectrum (reference)"),
    "lorentz":     (m_lorentz, ["A", "V", "x0", "g"], [0.52, 0.8, 1.4, 3.0],
                    "Lorentzian dip (reference)"),
    "asym":        (m_exp_gauss_asym, ["A", "V", "x0", "L1", "L2", "s"],
                    [0.52, 0.9, 1.4, 4.0, 4.0, 0.5], "symmetry test"),
}


def load_data(path):
    """Данные: data/data.txt.

    Проверка: checks/check.py::check — размер, конечность и числовой отпечаток.
    Используется в: src/fit_hom.py::main; src/verify_fit.py::main.
    """
    d = np.loadtxt(path, comments="#")
    return d[:, 0], d[:, 1]


def cm_to_ps(dx_cm):
    """Stage displacement -> optical delay (single pass: path change = dx).

    Данные: смещение в см; однопроходность подтверждена в diary.md (13.10).
    Проверка: checks/check.py::check — отдельный пересчёт T1 без импорта функции.
    Используется в: src/quick_fit.py::main; src/fit_hom.py::derived.
    """
    return N_GROUP_AIR * np.asarray(dx_cm) / C_LIGHT_CM_PER_PS
