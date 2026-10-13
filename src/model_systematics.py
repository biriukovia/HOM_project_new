"""Model-dependence (systematic spread) of the key observables among the
three statistically acceptable models: exp*gauss, coherent, exp*laplace.
Writes results/model_systematics.csv
"""
import os
import sys

import numpy as np
from scipy.optimize import curve_fit

sys.path.insert(0, os.path.dirname(__file__))
import hom_models as hm  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
x, y = hm.load_data(os.path.join(ROOT, "data", "data.txt"))
rows = []
for name in ("exp*gauss", "coherent", "exp*laplace"):
    f, _, g, _ = hm.MODELS[name]
    p, _ = curve_fit(f, x, y, p0=g, maxfev=100000)
    A, V, x0, L, w = p
    if name == "exp*gauss":
        V0 = V * hm.kernel_exp_gauss(0.0, L, w)
        jit = hm.cm_to_ps(w / np.sqrt(2))        # per-photon rms jitter
    elif name == "coherent":
        V0 = V                                   # pure state: K(0)=1
        jit = hm.cm_to_ps(w / 2)                 # rms of pulse intensity
    else:
        V0 = V * (1 / w) / (1 / L + 1 / w)       # K(0) = b/(a+b)
        jit = hm.cm_to_ps(w)                     # feeding time constant
    Vmin = float(f(np.array([x0]), *p)[0])
    rows.append((name, A, V, V0, x0, L, float(hm.cm_to_ps(L)), float(jit), Vmin))
out = os.path.join(ROOT, "results", "model_systematics.csv")
with open(out, "w") as fh:
    fh.write("model,A,V,V0,x0_cm,L_cm,T1_ps_1pass,jitter_ps_1pass,C_min\n")
    for r in rows:
        fh.write(r[0] + "," + ",".join(f"{v:.5f}" for v in r[1:]) + "\n")
arr = np.array([r[1:] for r in rows])
fh = open(out, "a")
fh.write("spread(max-min)," + ",".join(f"{v:.5f}" for v in arr.max(0) - arr.min(0)) + "\n")
fh.close()
print(open(out).read())
