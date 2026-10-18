#!/usr/bin/env python3
"""Один быстрый fit exp*gauss, без bootstrap и перезаписи научных результатов.

Данные: data/data.txt; src/hom_models.py:m_exp_gauss.
Проверка: checks/check.py — отдельная формула, квадратура и оптимизация.
Используется в: учебном опыте недели 2; results/course_fit.json.
Подготовлено ассистентом; запуск скрипта сам по себе не является сессией Goose.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import curve_fit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--data", type=Path, help="По умолчанию: <root>/data/data.txt")
    parser.add_argument("--result", type=Path, help="По умолчанию: <root>/results/course_fit.json")
    args = parser.parse_args()
    root = args.root.resolve()
    data_path = args.data or root / "data/data.txt"
    result_path = args.result or root / "results/course_fit.json"
    # Не создаём __pycache__ в исходном проекте при проверке из другой папки.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(root / "src"))
    import hom_models as hm

    data = np.loadtxt(data_path, comments="#", ndmin=2)
    if data.shape != (130, 2) or not np.isfinite(data).all():
        raise ValueError("Ожидаются ровно 130 конечных пар (x, C).")
    x, y = data.T
    if not np.all(np.diff(x) > 0):
        raise ValueError("Позиции должны строго возрастать.")
    f, names, initial, _ = hm.MODELS["exp*gauss"]
    bounds = ([0.05, 0, x.min(), 0.2, 0.01], [2, 1, x.max(), 30, 3])
    params, _ = curve_fit(f, x, y, p0=initial, bounds=bounds, maxfev=2000)
    rss = float(np.sum((y - f(x, *params)) ** 2))
    canonical = np.asarray(data, dtype="<f8", order="C").tobytes()
    digest = hashlib.sha256(f"{len(x)},2\n".encode("ascii") + canonical).hexdigest()
    output = {
        "schema_version": 1,
        "model": "exp*gauss",
        "data": {"rows": len(x), "sha256_numeric": digest},
        "parameters": dict(zip(names, map(float, params))),
        "rss": rss,
        "residual_sigma": float(np.sqrt(rss / (len(x) - len(params)))),
        "derived": {
            "V0": float(params[1] * hm.kernel_exp_gauss(0, params[3], params[4])),
            "T1_ps": float(hm.cm_to_ps(params[3])),
        },
        "interpretation": "V0: глубина относительно fitted A; T1: exp*gauss, однопроходная схема. Это условная модельная интерпретация, не независимое измерение T1.",
        "producer": "src/quick_fit.py; один МНК-fit, без bootstrap",
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"WROTE {result_path}; n={len(x)}; RSS={rss:.12g}; V0={output['derived']['V0']:.9f}")


if __name__ == "__main__":
    main()
