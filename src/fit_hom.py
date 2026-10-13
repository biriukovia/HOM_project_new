"""Fit the HOM dip with several physical models, select the best one,
estimate uncertainties (bootstrap) and derive physical parameters.

Usage (from the project root):  python src/fit_hom.py
Outputs: results/model_comparison.csv, results/fit_results.json,
         results/physical_parameters.csv, results/fig_*.pdf/png
"""
import json
import os
import sys

import numpy as np
from scipy.optimize import curve_fit
from scipy import stats

sys.path.insert(0, os.path.dirname(__file__))
import hom_models as hm  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(ROOT, "results")
os.makedirs(RES, exist_ok=True)
RNG = np.random.default_rng(20260930)
H_UEV_PER_GHZ = 4.135667696   # Planck constant, micro-eV per GHz
MAIN = "exp*gauss"


# ----------------------------------------------------------------------------
def fit(model, x, y, p0=None, sigma=None):
    f, names, guess, _ = hm.MODELS[model]
    p, cov = curve_fit(f, x, y, p0=guess if p0 is None else p0, sigma=sigma,
                       maxfev=200000)
    return p, cov


def stats_block(model, x, y, p):
    f = hm.MODELS[model][0]
    r = y - f(x, *p)
    n, k = len(x), len(p)
    rss = float(np.sum(r ** 2))
    aic = n * np.log(rss / n) + 2 * k
    aicc = aic + 2 * k * (k + 1) / (n - k - 1)
    bic = n * np.log(rss / n) + k * np.log(n)
    # Wald-Wolfowitz runs test on residual signs
    s = r > 0
    n1, n2 = s.sum(), (~s).sum()
    runs = 1 + int(np.sum(s[1:] != s[:-1]))
    mu = 2 * n1 * n2 / (n1 + n2) + 1
    var = (mu - 1) * (mu - 2) / (n1 + n2 - 1)
    z = (runs - mu) / np.sqrt(var)
    dw = float(np.sum(np.diff(r) ** 2) / rss)   # Durbin-Watson
    return dict(n=n, k=k, rss=rss, sigma=float(np.sqrt(rss / (n - k))),
                AIC=float(aic), AICc=float(aicc), BIC=float(bic), runs=runs,
                runs_expected=float(mu), runs_z=float(z),
                runs_p=float(2 * stats.norm.sf(abs(z))), DW=dw,
                shapiro_p=float(stats.shapiro(r).pvalue))


def noise_second_difference(y):
    """Model-free white-noise estimate: Var(y[i+1]-2y[i]+y[i-1]) = 6 sigma^2."""
    d2 = y[2:] - 2 * y[1:-1] + y[:-2]
    return float(np.sqrt(np.mean(d2 ** 2) / 6.0))


# ----------------------------------------------------------------------------
def derived(p):
    """Physical quantities from the main-model parameters (single pass)."""
    A, V, x0, L, s = p
    k0 = float(hm.kernel_exp_gauss(np.array([0.0]), L, s)[0])
    V0 = V * k0                                   # visibility at zero delay
    T1 = float(hm.cm_to_ps(L))                    # radiative lifetime, ps
    sd = float(hm.cm_to_ps(s))                    # rms of t0a - t0b, ps
    # FWHM of the dip (level A(1 - V0/2))
    u = np.linspace(0, 10 * L, 200001)
    K = hm.kernel_exp_gauss(u, L, s)
    half = u[np.argmin(np.abs(K - k0 / 2))]
    out = dict(A=A, V_int=V, V0=V0, K0=k0, x0_cm=x0, L_cm=L, s_cm=s,
               T1_ps=T1, sigma_diff_ps=sd, sigma_single_ps=sd / np.sqrt(2),
               FWHM_cm=2 * half, FWHM_ps=float(hm.cm_to_ps(2 * half)))
    # two limiting interpretations of indistinguishability M
    for tag, M in (("int", V), ("0", V0)):
        T2 = 2 * M * T1
        gstar = 1 / T2 - 1 / (2 * T1)             # pure dephasing rate, 1/ps
        dnu = 1e3 / (np.pi * T2)                  # FWHM (GHz), Lorentzian
        out.update({f"T2_{tag}_ps": T2,
                    f"Tstar_{tag}_ps": (1 / gstar if gstar > 0 else np.inf),
                    f"dnu_{tag}_GHz": dnu,
                    f"dE_{tag}_ueV": dnu * H_UEV_PER_GHZ,
                    f"lcoh_{tag}_cm": T2 * hm.C_LIGHT_CM_PER_PS})
    out["dnu_FL_GHz"] = 1e3 / (2 * np.pi * T1)
    out["dE_FL_ueV"] = out["dnu_FL_GHz"] * H_UEV_PER_GHZ
    out["lpacket_cm"] = T1 * hm.C_LIGHT_CM_PER_PS
    return out


def bootstrap(x, y, p, nboot=3000, block=None):
    """Residual bootstrap (block=None) or moving-block bootstrap."""
    f = hm.MODELS[MAIN][0]
    yfit = f(x, *p)
    r = y - yfit
    r = r - r.mean()
    n = len(r)
    out = []
    for _ in range(nboot):
        if block is None:
            rb = RNG.choice(r, n, replace=True)
        else:
            starts = RNG.integers(0, n - block + 1, int(np.ceil(n / block)))
            rb = np.concatenate([r[s0:s0 + block] for s0 in starts])[:n]
        try:
            pb, _ = curve_fit(f, x, yfit + rb, p0=p, maxfev=20000)
            out.append(pb)
        except RuntimeError:
            pass
    return np.array(out)


def summarize(samples):
    lo, med, hi = np.percentile(samples, [15.865, 50, 84.135])
    return dict(median=float(med), lo=float(lo), hi=float(hi),
                std=float(np.std(samples)))


# ----------------------------------------------------------------------------
def main():
    x, y = hm.load_data(os.path.join(ROOT, "data", "data.txt"))
    fits, rows = {}, []
    for name in hm.MODELS:
        p, cov = fit(name, x, y)
        st = stats_block(name, x, y, p)
        fits[name] = dict(params=dict(zip(hm.MODELS[name][1], map(float, p))),
                          errors=dict(zip(hm.MODELS[name][1],
                                          map(float, np.sqrt(np.diag(cov))))),
                          stats=st, description=hm.MODELS[name][3])
        rows.append((name, st))
    best_aic = min(st["AICc"] for n_, st in rows if n_ != "asym")
    with open(os.path.join(RES, "model_comparison.csv"), "w") as fh:
        fh.write("model,k,sigma,AICc,dAICc,BIC,runs,runs_expected,runs_p,DW,shapiro_p\n")
        for name, st in rows:
            fh.write(f"{name},{st['k']},{st['sigma']:.5f},{st['AICc']:.2f},"
                     f"{st['AICc'] - best_aic:.2f},{st['BIC']:.2f},{st['runs']},"
                     f"{st['runs_expected']:.1f},{st['runs_p']:.3g},{st['DW']:.3f},"
                     f"{st['shapiro_p']:.3g}\n")

    # ---- main model: bootstrap -------------------------------------------
    p_main, cov_main = fit(MAIN, x, y)
    boot = bootstrap(x, y, p_main, nboot=3000)
    boot_blk = bootstrap(x, y, p_main, nboot=1000, block=8)
    # weighted fit (Poisson-like noise sigma ~ sqrt(y)) as robustness check
    p_w, _ = fit(MAIN, x, y, p0=p_main, sigma=np.sqrt(y))

    res = dict(noise_second_difference=noise_second_difference(y),
               fits=fits, main_model=MAIN,
               weighted_fit=dict(zip(hm.MODELS[MAIN][1], map(float, p_w))))
    d0 = derived(p_main)
    dist = [derived(pb) for pb in boot]
    dist_b = [derived(pb) for pb in boot_blk]
    res["derived_1pass"] = {
        key: dict(value=float(d0[key]),
                  boot=summarize([d[key] for d in dist]),
                  block_boot=summarize([d[key] for d in dist_b]))
        for key in d0}
    # BS-imbalance consistency: if A were an absolute probability, A=R^2+T^2
    A = p_main[0]
    RT2 = 1 - A                                   # 2RT
    R_abs = (1 - np.sqrt(max(2 * A - 1, 0))) / 2      # R from A = R^2 + T^2
    V0_main = derived(p_main)["V0"]
    res["bs_check"] = dict(A=float(A), Vmax_if_absolute=float(RT2 / A),
                           R_if_absolute=float(R_abs),
                           M0_BScorrected_if_absolute=float(V0_main / (RT2 / A)),
                           V_int=float(p_main[1]),
                           g2_upper_bound_if_Vint_is_M=float((1 - p_main[1]) / 2),
                           z=float((p_main[1] - RT2 / A) /
                                   np.std(boot[:, 1] - (1 - boot[:, 0]) / boot[:, 0])))
    # g2 correction table (Ollivier et al., PRL 126, 063602): M=(V+g2)/(1-g2)
    V0 = res["derived_1pass"]["V0"]["value"]
    Vi = res["derived_1pass"]["V_int"]["value"]
    res["g2_table"] = [dict(g2=g, M_from_V0=(V0 + g) / (1 - g),
                            M_from_Vint=(Vi + g) / (1 - g))
                       for g in (0.0, 0.01, 0.02, 0.05)]
    # parameter correlation matrix of the main fit
    sd = np.sqrt(np.diag(cov_main))
    res["corr_main"] = (cov_main / np.outer(sd, sd)).round(3).tolist()
    np.save(os.path.join(RES, "bootstrap_main.npy"), boot)

    with open(os.path.join(RES, "fit_results.json"), "w") as fh:
        json.dump(res, fh, indent=2, default=float)

    # human-readable table
    with open(os.path.join(RES, "physical_parameters.csv"), "w") as fh:
        fh.write("quantity,value,err\n")
        for key in res["derived_1pass"]:
            a = res["derived_1pass"][key]
            fh.write(f"{key},{a['value']:.6g},{a['boot']['std']:.3g}\n")
    make_figures(x, y, fits, p_main, boot)
    print_summary(res)


def make_figures(x, y, fits, p_main, boot):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "font.family": "serif"})
    xx = np.linspace(x.min(), x.max(), 2000)
    colors = {"exp*gauss": "#1f4e9c", "exp": "#d1495b", "gauss": "#8a8a8a",
              "lorentz": "#edae49", "exp*laplace": "#00798c"}

    # Fig 1: data + main fit + residuals
    f = hm.MODELS[MAIN][0]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(3.3, 3.6), sharex=True,
                                 gridspec_kw=dict(height_ratios=[3, 1], hspace=0.05))
    a1.plot(x, y, "o", ms=2.3, color="k", label="data")
    a1.plot(xx, f(xx, *p_main), "-", color=colors[MAIN], lw=1.2,
            label=r"exp$\ast$Gauss fit")
    a1.axhline(p_main[0], ls=":", color="gray", lw=0.8)
    a1.axvline(p_main[2], ls=":", color="gray", lw=0.8)
    a1.set_ylabel("coincidence level")
    top = a1.secondary_xaxis("top", functions=(
        lambda v: hm.cm_to_ps(v - p_main[2]), lambda t: t * hm.C_LIGHT_CM_PER_PS /
        hm.N_GROUP_AIR + p_main[2]))
    top.set_xlabel(r"delay $\tau$ (ps), single pass")
    a1.legend(frameon=False, loc="lower right")
    r = y - f(x, *p_main)
    a2.plot(x, 1e3 * r, "o", ms=2, color=colors[MAIN])
    a2.axhline(0, color="k", lw=0.6)
    a2.set_ylabel(r"res. ($10^{-3}$)")
    a2.set_xlabel("position (cm)")
    fig.savefig(os.path.join(RES, "fig_fit_main.pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(RES, "fig_fit_main.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)

    # Fig 2: residuals of competing models
    names = ["exp*gauss", "exp*laplace", "exp", "lorentz", "gauss"]
    fig, axs = plt.subplots(len(names), 1, figsize=(3.3, 4.2), sharex=True,
                            gridspec_kw=dict(hspace=0.08))
    for ax, nm in zip(axs, names):
        fn = hm.MODELS[nm][0]
        p = list(fits[nm]["params"].values())
        rr = y - fn(x, *p)
        ax.plot(x, 1e3 * rr, "o", ms=1.6, color=colors[nm])
        ax.axhline(0, color="k", lw=0.5)
        lim = max(4, 1.15e3 * np.abs(rr).max())
        ax.set_ylim(-lim, lim)
        ax.text(0.99, 0.93, f"{nm}  ($\\sigma$={1e3*fits[nm]['stats']['sigma']:.1f}e-3)",
                transform=ax.transAxes, ha="right", va="top", fontsize=7,
                bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.85))
    axs[len(names) // 2].set_ylabel(r"residual ($10^{-3}$)")
    axs[-1].set_xlabel("position (cm)")
    fig.savefig(os.path.join(RES, "fig_residuals_models.pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(RES, "fig_residuals_models.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)

    # Fig 3: zoom around the minimum, exp vs exp*gauss (cusp rounding)
    fig, ax = plt.subplots(figsize=(3.3, 2.4))
    m = np.abs(x - p_main[2]) < 1.6
    ax.plot(x[m], y[m], "o", ms=3, color="k", label="data")
    x2 = np.linspace(x[m].min(), x[m].max(), 1000)
    for nm in ("exp*gauss", "exp", "lorentz"):
        fn = hm.MODELS[nm][0]
        ax.plot(x2, fn(x2, *fits[nm]["params"].values()), color=colors[nm],
                lw=1.1, label=nm)
    ax.set_xlabel("position (cm)")
    ax.set_ylabel("coincidence level")
    ax.legend(frameon=False, fontsize=7)
    fig.savefig(os.path.join(RES, "fig_zoom.pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(RES, "fig_zoom.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)

    # Fig 4: bootstrap distributions of V, L, s
    fig, axs = plt.subplots(1, 3, figsize=(6.8, 1.9))
    for ax, j, lab in zip(axs, (1, 3, 4), ("$V$", "$L$ (cm)", "$s$ (cm)")):
        ax.hist(boot[:, j], bins=50, color=colors[MAIN], alpha=0.8)
        ax.axvline(p_main[j], color="k", lw=0.8)
        ax.set_xlabel(lab)
        ax.set_yticks([])
    fig.savefig(os.path.join(RES, "fig_bootstrap.pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(RES, "fig_bootstrap.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def print_summary(res):
    print("model-free noise (2nd differences):", round(res["noise_second_difference"], 5))
    for nm, fr in res["fits"].items():
        st = fr["stats"]
        print(f"{nm:12s} sigma={st['sigma']:.5f} AICc={st['AICc']:.1f} "
              f"runs={st['runs']}/{st['runs_expected']:.0f} p={st['runs_p']:.2g} "
              f"DW={st['DW']:.2f}  ", {k: round(v, 4) for k, v in fr["params"].items()})
    for key, v in res["derived_1pass"].items():
        print(f"  {key:16s} {v['value']:.5g} ± {v['boot']['std']:.2g} "
              f"(block ± {v['block_boot']['std']:.2g})")
    print("BS check:", res["bs_check"])
    print("weighted fit:", res["weighted_fit"])
    print("g2 table:", res["g2_table"])
    print("corr:", res["corr_main"])


if __name__ == "__main__":
    main()
