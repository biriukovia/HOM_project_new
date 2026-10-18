#!/usr/bin/env python3
"""Конечная проверка учебного результата: exit 0 = PASS, иначе FAIL.

Данные: data/data.txt и results/course_fit.json (или явные --data/--result).
Проверка: числовой отпечаток, независимое ядро через log_ndtr, прямая
квадратура свёртки и least_squares; исходные hom_models/fit_hom не импортируются.
Используется в: src/quick_fit.py; checks/check_selftest.py; опыт недели 2.
Проверяет согласованность чисел в заданной модели, не её физическую истинность.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.integrate import quad
from scipy.optimize import least_squares
from scipy.special import log_ndtr

NAMES = ("A", "V", "x0", "L", "s")
EXPECTED_DATA_DIGEST = 'd9b904bae0f78959c6cc9653f7e2a73174044c9bf6ea0c9468d442af7f3bc8e1'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def kernel(u, length, width):
    """Своя формула exp(-|.|/L) * N(0,s²), без импорта модели проекта."""
    u = np.abs(np.asarray(u, dtype=float))
    q = width / length
    return (np.exp(q*q/2 - u/length + log_ndtr(u/width - q))
            + np.exp(q*q/2 + u/length + log_ndtr(-u/width - q)))


def prediction(x, p):
    a, v, x0, length, width = p
    return a * (1 - v * kernel(x-x0, length, width))


def finite_number(value):
    return type(value) in (int, float) and np.isfinite(value)


def check(data_path, result_path):
    data = np.loadtxt(data_path, comments="#", ndmin=2)
    require(data.shape == (130, 2), "Ожидаются 130 пар (x,C)")
    require(np.isfinite(data).all(), "В данных есть NaN/Inf")
    x, y = data.T
    require(np.all(np.diff(x) > 0), "Позиции не строго возрастают")
    saved = json.loads(result_path.read_text(encoding="utf-8"))
    require(saved.get("schema_version") == 1, "Неизвестная версия схемы")
    require(saved.get("model") == "exp*gauss", "Не та модель")
    canonical = np.asarray(data, dtype="<f8", order="C").tobytes()
    digest = hashlib.sha256(f"{len(x)},2\n".encode("ascii") + canonical).hexdigest()
    require(digest == EXPECTED_DATA_DIGEST, "Исходные числовые данные изменены относительно архива 19.10.2026")
    require(saved["data"]["rows"] == len(x), "Не совпало число точек")
    require(saved["data"]["sha256_numeric"] == digest, "Не совпал числовой отпечаток данных")
    require(set(saved["parameters"]) == set(NAMES), "Не совпала схема параметров")
    p = [saved["parameters"][key] for key in NAMES]
    require(all(finite_number(v) for v in p), "Параметры должны быть конечными числами")
    p = np.asarray(p, dtype=float)
    lower = np.array([0.05, 0, x.min(), 0.2, 0.01])
    upper = np.array([2, 1, x.max(), 30, 3])
    require(np.all(p >= lower) and np.all(p <= upper), "Параметры вне заданной области")
    for v in [saved["rss"], saved["residual_sigma"], saved["derived"]["V0"], saved["derived"]["T1_ps"]]:
        require(finite_number(v), "Производные величины должны быть конечными числами")

    # Пять независимых интегралов, включая центр и крылья провала.
    max_kernel_error = 0.0
    for u in (0.0, 0.3, 1.0, 3.0, 10.0):
        length, width = p[3:]
        integrand = lambda z: np.exp(-abs(u-width*z)/length-z*z/2) / np.sqrt(2*np.pi)
        points = [u/width] if abs(u/width) < 12 else None
        numeric, _ = quad(integrand, -12, 12, epsabs=1e-11, epsrel=1e-11, points=points)
        max_kernel_error = max(max_kernel_error, abs(numeric-float(kernel(u, length, width))))
    require(max_kernel_error < 1e-9, "Ядро не согласуется с прямой квадратурой")
    residual = y-prediction(x, p)
    rss = float(residual @ residual)
    sigma = np.sqrt(rss/(len(x)-len(p)))
    require(np.isclose(saved["rss"], rss, rtol=1e-7, atol=1e-12), "Сохранённый RSS неверен")
    require(np.isclose(saved["residual_sigma"], sigma, rtol=1e-7, atol=1e-12), "Сохранённая sigma неверна")
    require(sigma <= 0.0025, "Качество fit ниже принятого порога sigma <= 0.0025")
    v0 = float(p[1]*kernel(0, p[3], p[4]))
    t1 = float(1.00028*p[3]/0.0299792458)
    require(np.isclose(saved["derived"]["V0"], v0, rtol=1e-7, atol=1e-10), "Неверный V0")
    require(np.isclose(saved["derived"]["T1_ps"], t1, rtol=1e-7, atol=1e-8), "Неверный T1 для однопроходной схемы")
    # Начальная точка независима от представленного результата. Это проверка
    # против конкретного численного optimum, не доказательство глобальности.
    reference = least_squares(lambda q: y-prediction(x, q),
                              [0.52, 0.9, float(x[np.argmin(y)]), 4, 0.5],
                              bounds=(lower, upper), max_nfev=2000,
                              ftol=1e-12, xtol=1e-12, gtol=1e-12)
    require(reference.success, "Независимый least_squares не сошёлся")
    reference_rss = float(reference.fun @ reference.fun)
    require(abs(rss-reference_rss) <= max(1e-9, 1e-4*reference_rss), "RSS отличается от независимого fit")
    return f"PASS n={len(x)} RSS={rss:.12g} sigma={sigma:.9f} V0={v0:.9f} T1_ps={t1:.6f} quad_error={max_kernel_error:.2g}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--data", type=Path)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        print(check(args.data or root/"data/data.txt", args.result or root/"results/course_fit.json"))
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
