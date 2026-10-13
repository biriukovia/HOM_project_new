"""Independent numerical check of the analytic HOM kernels.

The HOM coincidence probability for a 50:50 beam splitter is
    P_c(tau) = 1/2 [1 - J(tau)],   J = int int G_a(t,t') G_b(t',t) dt dt',
with G the (normalised) two-time first-order coherence of each photon
(Brańczyk 2017, Sec. 4.3; Kiraz et al. 2004).  Here G is built directly on a
time grid for a two-level emitter with lifetime T1, pure dephasing time T2*
and random emission start t0 (Gaussian jitter), WITHOUT using the analytic
convolution formula.  J(tau) is compared with
    V_th * K_EG(tau; T1, sqrt2*sigma1),  V_th = T2/(2 T1).
The pure-state (coherent) model is checked in the same way.
Usage: python src/verify_model.py [DT_ps]   (run with 1 and 0.5 to see convergence)
Writes results/verify_model_dt<DT>.txt
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import hom_models as hm  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(ROOT, "results")

T1, TSTAR, SIG1 = 130.0, 3000.0, 12.0    # ps (values close to the fit)
DT = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
t = np.arange(-120.0, 1800.0, DT)
G1 = 1 / T1
gstar = 1 / TSTAR


def coherence_matrix(t0_samples, weights):
    """Mixture of G_t0(t,t') = G1 exp(-G1(t+t'-2t0)/2) exp(-g*|t-t'|) theta."""
    tt, tp = np.meshgrid(t, t, indexing="ij")
    deph = np.exp(-gstar * np.abs(tt - tp))
    G = np.zeros_like(tt)
    for t0, w in zip(t0_samples, weights):
        a = np.where(t >= t0, np.exp(-G1 * (t - t0) / 2), 0.0)
        G += w * np.outer(a, a)
    return G1 * G * deph


def J_of_tau(G, shifts):
    out = []
    for k in shifts:           # photon b delayed by k grid steps
        Gb = np.zeros_like(G)
        if k >= 0:
            Gb[k:, k:] = G[:G.shape[0] - k, :G.shape[1] - k]
        else:
            Gb[:k, :k] = G[-k:, -k:]
        out.append(np.sum(G * Gb.T) * DT * DT)
    return np.array(out)


def main():
    # Gaussian quadrature over the jitter distribution of t0
    nodes, w = np.polynomial.hermite_e.hermegauss(41)
    w = w / w.sum()
    G = coherence_matrix(SIG1 * nodes, w)
    norm = np.trace(G) * DT                     # should be ~1 (photon number)
    shifts = np.round(np.array([0, 5, 10, 20, 40, 80, 130, 200, 300, 450, -40]) / DT).astype(int)
    J = J_of_tau(G, shifts) / norm ** 2          # normalise photon number
    T2 = 1 / (1 / (2 * T1) + gstar)
    Vth = T2 / (2 * T1)
    K = hm.kernel_exp_gauss(shifts * DT, T1, np.sqrt(2) * SIG1)
    lines = [f"grid step DT = {DT} ps; trace(G) = {norm:.5f} (1 up to discretisation; J is divided by trace^2)",
             f"T1={T1} ps, T2*={TSTAR} ps, sigma1={SIG1} ps -> T2={T2:.2f} ps, "
             f"V_th=T2/2T1={Vth:.5f}",
             "tau_ps   J_numeric   V_th*K_EG   rel.diff"]
    maxrel = 0
    for s_, j_, k_ in zip(shifts, J, Vth * K):
        rel = (j_ - k_) / k_
        maxrel = max(maxrel, abs(rel))
        lines.append(f"{s_*DT:7.1f}  {j_:.6f}   {k_:.6f}   {rel:+.2e}")
    lines.append(f"max |rel.diff| (incoherent jitter model) = {maxrel:.2e}")

    # coherent (pure-state) wave packet: psi = gaussian pulse (*) exp decay
    sp = SIG1                                   # rms of the pulse intensity |g|^2
    pulse = np.exp(-t ** 2 / (4 * sp ** 2))     # amplitude with intensity rms sp
    dec = np.where(t >= 0, np.exp(-G1 * t / 2), 0.0)
    i0 = np.argmin(np.abs(t))
    psi = np.convolve(pulse, dec, mode="full")[i0:i0 + len(t)] * DT
    psi /= np.sqrt(np.sum(np.abs(psi) ** 2) * DT)
    ov = np.array([np.sum(psi[k:] * psi[:len(t) - k]) * DT if k >= 0 else
                   np.sum(psi[:k] * psi[-k:]) * DT for k in shifts]) ** 2
    # analytic: [K_EG(u; 2T1, s_c) / K_EG(0)]^2 with s_c = rms of the pulse-
    # amplitude autocorrelation = sqrt(2)*(amplitude rms) = sqrt(2)*sqrt(2)*sp
    sc = 2 * sp
    Ka = (hm.kernel_exp_gauss(shifts * DT, 2 * T1, sc) /
          hm.kernel_exp_gauss(0.0, 2 * T1, sc)) ** 2
    lines.append("coherent model: tau_ps  |<psi|psi_tau>|^2  analytic  rel.diff")
    maxrel2 = 0
    for s_, o_, k_ in zip(shifts, ov, Ka):
        rel = (o_ - k_) / k_
        maxrel2 = max(maxrel2, abs(rel))
        lines.append(f"{s_*DT:7.1f}  {o_:.6f}   {k_:.6f}   {rel:+.2e}")
    lines.append(f"max |rel.diff| (coherent model) = {maxrel2:.2e}")
    # closed form (eq. K_EG) vs direct quadrature of the convolution
    from scipy.integrate import quad
    Lc, sc2 = 3.92, 0.506
    worst = 0.0
    for u in (0.0, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0):
        num = quad(lambda w: np.exp(-abs(u - w) / Lc) * np.exp(-w * w / (2 * sc2 ** 2))
                   / np.sqrt(2 * np.pi) / sc2, -14 * sc2, 14 * sc2, points=[u],
                   limit=400, epsabs=0, epsrel=1e-13)[0]
        worst = max(worst, abs(hm.kernel_exp_gauss(u, Lc, sc2) / num - 1))
    lines.append(f"closed-form K_EG vs quadrature (L=3.92, s=0.506 cm): max rel.diff = {worst:.1e}")
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(RES, f"verify_model_dt{DT:g}.txt"), "w") as fh:
        fh.write(txt + "\n")


if __name__ == "__main__":
    main()
