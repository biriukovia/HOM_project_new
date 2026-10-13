"""Independent checks of the fit and of the model selection.

1. Global optimiser (differential evolution) vs local Levenberg-Marquardt.
2. Injection-recovery: synthetic data from the best fit + noise -> refit;
   bias, scatter and coverage of the covariance-based 1-sigma intervals.
3. Discrimination power: data simulated from the Laplace-jitter model,
   how often does AICc still prefer the Gaussian-jitter model?
4. 10-fold cross-validation (random and contiguous folds) for all models.
5. Stability of the parameters on data subsets.
6. Model-light estimate of the zero-delay visibility.
Writes results/verify_fit.txt
"""
import os
import sys

import numpy as np
from scipy.optimize import curve_fit, differential_evolution

sys.path.insert(0, os.path.dirname(__file__))
import hom_models as hm  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(ROOT, "results")
RNG = np.random.default_rng(12345)
LINES = []


def log(s=""):
    print(s)
    LINES.append(s)


def aicc(rss, n, k):
    return n * np.log(rss / n) + 2 * k + 2 * k * (k + 1) / (n - k - 1)


def lfit(name, x, y, p0=None):
    f, _, g, _ = hm.MODELS[name]
    p, c = curve_fit(f, x, y, p0=g if p0 is None else p0, maxfev=100000)
    return p, c, float(np.sum((y - f(x, *p)) ** 2))


def main():
    x, y = hm.load_data(os.path.join(ROOT, "data", "data.txt"))
    n = len(x)
    f = hm.MODELS["exp*gauss"][0]
    p, cov, rss = lfit("exp*gauss", x, y)
    sig = np.sqrt(rss / (n - 5))
    names = hm.MODELS["exp*gauss"][1]

    # 1 ---------------------------------------------------------------------
    obj = lambda q: np.sum((y - f(x, *q)) ** 2)   # noqa: E731
    de = differential_evolution(obj, [(0.3, 0.8), (0.3, 1.5), (0.0, 3.0),
                                      (0.5, 15.0), (0.01, 3.0)],
                                seed=7, tol=1e-12, maxiter=4000, polish=True)
    log("1. Global optimiser (differential evolution) vs Levenberg-Marquardt")
    for nm, a, b in zip(names, p, de.x):
        log(f"   {nm:3s}  LM={a:.6f}  DE={b:.6f}  diff={b - a:+.1e}")
    log(f"   RSS LM={rss:.8e}  DE={de.fun:.8e}")

    # 2 ---------------------------------------------------------------------
    nsim = 400
    yfit = f(x, *p)
    est, cover = [], np.zeros(5)
    for _ in range(nsim):
        ys = yfit + RNG.normal(0, sig, n)
        ps, cs = curve_fit(f, x, ys, p0=p, maxfev=20000)
        est.append(ps)
        cover += np.abs(ps - p) < np.sqrt(np.diag(cs))
    est = np.array(est)
    log(f"\n2. Injection-recovery ({nsim} synthetic sets, white noise sigma={sig:.5f})")
    for j, nm in enumerate(names):
        log(f"   {nm:3s} true={p[j]:.5f}  mean={est[:, j].mean():.5f}  "
            f"bias/sd={(est[:, j].mean() - p[j]) / est[:, j].std():+.2f}  "
            f"sd={est[:, j].std():.2e}  cov.err={np.sqrt(cov[j, j]):.2e}  "
            f"coverage(1sig)={cover[j] / nsim:.2f}")

    # 3 ---------------------------------------------------------------------
    pl, _, rl = lfit("exp*laplace", x, y)
    fl = hm.MODELS["exp*laplace"][0]
    wins_g, wins_l = 0, 0
    d_sim = []
    for _ in range(300):
        ys = fl(x, *pl) + RNG.normal(0, sig, n)
        _, _, r_g = lfit("exp*gauss", x, ys, p0=p)
        _, _, r_l = lfit("exp*laplace", x, ys, p0=pl)
        d = aicc(r_g, n, 5) - aicc(r_l, n, 5)
        d_sim.append(d)
        wins_g += d < 0
    d_obs = aicc(rss, n, 5) - aicc(rl, n, 5)
    log("\n3. Discrimination power Gaussian vs Laplace jitter")
    log(f"   observed AICc(gauss) - AICc(laplace) = {d_obs:.2f}")
    log(f"   data simulated from Laplace model: Gaussian preferred in "
        f"{wins_g}/300 cases; P(dAICc <= {d_obs:.1f}) = "
        f"{np.mean(np.array(d_sim) <= d_obs):.3f}")
    wins = 0
    d_sim2 = []
    for _ in range(300):
        ys = yfit + RNG.normal(0, sig, n)
        _, _, r_g = lfit("exp*gauss", x, ys, p0=p)
        _, _, r_l = lfit("exp*laplace", x, ys, p0=pl)
        d_sim2.append(aicc(r_g, n, 5) - aicc(r_l, n, 5))
    d_sim2 = np.array(d_sim2)
    log(f"   data simulated from Gaussian model: Gaussian preferred in "
        f"{np.sum(d_sim2 < 0)}/300 cases; median dAICc = {np.median(d_sim2):.1f}")

    # 4 ---------------------------------------------------------------------
    log("\n4. 10-fold cross-validation, RMS prediction error (1e-3)")
    log("   model         random   contiguous")
    perm = RNG.permutation(n)
    for name in ("exp*gauss", "exp*laplace", "coherent", "exp", "lorentz", "gauss"):
        fn = hm.MODELS[name][0]
        out = []
        for kind in ("random", "contig"):
            err = []
            idx = perm if kind == "random" else np.arange(n)
            for k in range(10):
                test = idx[k::10] if kind == "random" else idx[k * n // 10:(k + 1) * n // 10]
                train = np.setdiff1d(np.arange(n), test)
                try:
                    pk, _, _ = lfit(name, x[train], y[train])
                    err.append(y[test] - fn(x[test], *pk))
                except RuntimeError:
                    err.append(np.full(len(test), np.nan))
            out.append(1e3 * np.sqrt(np.nanmean(np.concatenate(err) ** 2)))
        log(f"   {name:12s}  {out[0]:6.2f}   {out[1]:8.2f}")

    # 5 ---------------------------------------------------------------------
    log("\n5. Parameter stability on subsets (exp*gauss)")
    subsets = {"all": np.ones(n, bool),
               "x <= 9 cm": x <= 9,
               "x >= 0.5 cm": x >= 0.5,
               "drop |x-x0|<0.3": np.abs(x - p[2]) >= 0.3,
               "even points": np.arange(n) % 2 == 0,
               "odd points": np.arange(n) % 2 == 1}
    for lab, m in subsets.items():
        ps, cs, _ = lfit("exp*gauss", x[m], y[m], p0=p)
        e = np.sqrt(np.diag(cs))
        log(f"   {lab:16s} " + "  ".join(f"{nm}={v:.4f}({ee:.4f})"
                                         for nm, v, ee in zip(names, ps, e)))

    # 6 ---------------------------------------------------------------------
    m = np.abs(x - x[np.argmin(y)]) <= 0.35
    c2 = np.polyfit(x[m], y[m], 2)
    xm = -c2[1] / (2 * c2[0])
    ymin = np.polyval(c2, xm)
    # asymptote from the tail alone: y = A - B exp(-x/L) on x > 7 cm
    mt = x > 7
    pt, ct = curve_fit(lambda xx, A, B, L: A - B * np.exp(-xx / L),
                       x[mt], y[mt], p0=[0.52, 0.5, 4])
    log("\n6. Model-light zero-delay visibility")
    log(f"   parabola through {m.sum()} lowest points: x_min={xm:.4f} cm, "
        f"y_min={ymin:.5f}")
    log(f"   tail-only asymptote (x>7 cm, single exponential): A={pt[0]:.4f} "
        f"+- {np.sqrt(ct[0, 0]):.4f}, L_tail={pt[2]:.3f} cm")
    log(f"   V0 = 1 - y_min/A = {1 - ymin / pt[0]:.4f} (tail A),  "
        f"{1 - ymin / p[0]:.4f} (global-fit A)")
    log(f"   main model: V0 = {p[1] * hm.kernel_exp_gauss(0.0, p[3], p[4]):.4f}")

    # 7 ---------------------------------------------------------------------
    # can a fixed asymptote A = 1/2 be rescued by a second (slow) exponential?
    def m_bi(q):
        V, x0, L1, s, w, L2 = q
        u = x - x0
        return 0.5 * (1 - V * ((1 - w) * hm.kernel_exp_gauss(u, L1, s)
                               + w * hm.kernel_exp_gauss(u, L2, s)))
    de2 = differential_evolution(lambda q: np.sum((y - m_bi(q)) ** 2),
                                 [(0.5, 1.2), (1, 2), (0.5, 10), (0.05, 2), (0, 1), (1, 100)],
                                 seed=1, tol=1e-12, maxiter=3000, polish=True)
    log("\n7. Fixed asymptote A=1/2 with bi-exponential kernel (global fit)")
    log(f"   sigma = {np.sqrt(de2.fun / (n - 6)):.5f} (free-A model: {sig:.5f}); "
        f"points above 0.5: {np.sum(y > 0.5)}")

    with open(os.path.join(RES, "verify_fit.txt"), "w") as fh:
        fh.write("\n".join(LINES) + "\n")


if __name__ == "__main__":
    main()
