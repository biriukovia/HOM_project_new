"""[порождено: Codex] Independent repair of Goose draft, authorized 2026-11-05.
Frozen specification: METHOD.md. Original drafts are retained in logs/hw2-build-*.
"""
import sys
sys.dont_write_bytecode = True
import argparse
from datetime import datetime
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import platform
import time
import warnings
import numpy as np
import scipy
from scipy.integrate import IntegrationWarning, quad
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[2]
DIGEST = 'd9b904bae0f78959c6cc9653f7e2a73174044c9bf6ea0c9468d442af7f3bc8e1'
IDS = tuple(f'P{i}' for i in range(1, 9))


def now():
    return datetime.now().astimezone().isoformat()


def inputs():
    names = ('data/data.txt', 'src/hom_models.py', 'METHOD.md', 'checks/hw2/verify.py', 'checks/hw2/engine.py')
    hashes = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}
    data = np.loadtxt(ROOT/'data/data.txt', comments='#', ndmin=2)
    if data.shape != (130, 2) or not np.isfinite(data).all():
        raise ValueError('Expected 130 finite coordinate/coincidence pairs')
    if not np.all(np.diff(data[:, 0]) > 0):
        raise ValueError('Coordinates must strictly increase')
    digest = hashlib.sha256(b'130,2\n'+np.asarray(data, dtype='<f8', order='C').tobytes()).hexdigest()
    if digest != DIGEST:
        raise ValueError(f'Numeric data digest mismatch: {digest}')
    return {'rows': 130, 'numeric_sha256': digest, 'sha256': hashes}


def finite(value):
    arr = np.asarray(value, dtype=float)
    if not np.isfinite(arr).all():
        raise ValueError('Nonfinite result; no samples may be discarded')
    return arr


def record(metric, tolerance, **details):
    metric = float(finite(metric))
    return {'pass': metric <= tolerance, 'metric': metric, 'tolerance': float(tolerance), **details}


def reference(u, length, width):
    """Independent convolution, not a second call to the tested model."""
    def integrand(z):
        return np.exp(-abs(u-width*z)/length-z*z/2)/np.sqrt(2*np.pi)
    point = u/width
    with warnings.catch_warnings():
        warnings.simplefilter('error', IntegrationWarning)
        value, error = quad(integrand, -12, 12, epsabs=1e-11, epsrel=1e-11,
                            points=[point] if -12 < point < 12 else None)
    finite([value, error])
    if error > 1e-9:
        raise ValueError(f'Quadrature uncertainty {error} exceeds 1e-9')
    return value, error


def property_case(pid, hm, case):
    u, length, width = case['u'], case['L'], case['s']
    kernel = lambda x, l=length, s=width: finite(hm.kernel_exp_gauss(x, l, s))
    if pid == 'P1':
        k = kernel(np.array([u, 0.0, -u]))
        return record(max(0.0, float(np.max(-k)), float(np.max(k-1))), 1e-12)
    if pid == 'P2':
        return record(abs(kernel(u)-kernel(-u)), 1e-12)
    if pid == 'P3':
        return record(max(abs(kernel(a*u, a*length, a*width)-kernel(u)) for a in (0.1, 10.0)), 1e-10)
    if pid == 'P4':
        k = kernel(np.linspace(0, 12*max(length, width), 65))
        return record(max(0.0, float(np.max(np.diff(k)))), 1e-12)
    if pid == 'P5':
        value, error = reference(u, length, width)
        return record(abs(kernel(u)-value), 1e-9, quadrature_error=error)
    if pid == 'P6':
        grid = np.array([0.0, 0.5*length, case['small_width_u']])
        delta = abs(kernel(grid, length, 1e-6*length)-np.exp(-abs(grid)/length))
        return record(np.max(delta), np.sqrt(2/np.pi)*1e-6+1e-10)
    if pid == 'P7':
        a, v, x0 = case['A'], case['V'], case['x0']
        c = float(finite(hm.m_exp_gauss(x0+u, a, v, x0, length, width)))
        zero = float(finite(hm.m_exp_gauss(x0+u, a, 0.0, x0, length, width)))
        return record(max(0.0, a*(1-v)-c, c-a, abs(zero-a)), 1e-10, zero_visibility_error=abs(zero-a))
    if pid == 'P8':
        dx = np.array([0.0, 1.0, -1.0, 0.123, -0.456, case['dx']])
        expected = dx*1.00028/0.0299792458
        actual = finite(hm.cm_to_ps(dx))
        if actual.shape != dx.shape:
            raise ValueError('cm_to_ps must preserve input shape')
        back = finite(actual*0.0299792458/1.00028)
        forward, reverse = abs(actual-expected), abs(back-dx)
        ratio = max(float(np.max(forward/(1e-10+1e-12*abs(expected)))),
                    float(np.max(reverse/(1e-10+1e-12*abs(dx)))))
        return record(ratio, 1.0, rtol=1e-12, atol=1e-10,
                      forward_error_ps=float(np.max(forward)), reverse_error_cm=float(np.max(reverse)))
    raise ValueError(pid)


def run_properties(hm, seeds, count):
    rows = {pid: {'pass': True, 'cases': 0, 'failures': 0, 'max_metric': 0.0,
                  'tolerance': None, 'first_failure': None} for pid in IDS}
    quad_error = 0.0
    for seed in seeds:
        rng = np.random.default_rng(seed)
        for index in range(count):
            length = float(np.exp(rng.uniform(np.log(.2), np.log(30))))
            width = float(np.exp(rng.uniform(np.log(.01), np.log(3))))
            case = {'L': length, 's': width, 'A': float(rng.uniform(.05, 2)),
                    'V': float(rng.uniform(0, 1)), 'u': float(rng.uniform(-12, 12)*max(length, width)),
                    'x0': float(rng.uniform(-5, 5)), 'small_width_u': float(rng.uniform(-2, 2)*length),
                    'dx': float(rng.uniform(-10, 10))}
            for pid in IDS:
                try:
                    item = property_case(pid, hm, case)
                except Exception as exc:
                    item = {'pass': False, 'metric': None, 'error': f'{type(exc).__name__}: {exc}'}
                row = rows[pid]
                row['cases'] += 1
                row['pass'] = row['pass'] and item['pass']
                if item.get('metric') is not None:
                    row['max_metric'] = max(row['max_metric'], item['metric'])
                if 'tolerance' in item:
                    row['tolerance'] = item['tolerance']
                if not item['pass']:
                    row['failures'] += 1
                    if row['first_failure'] is None:
                        row['first_failure'] = {'seed': seed, 'index': index, 'inputs': case, **item}
                quad_error = max(quad_error, item.get('quadrature_error', 0.0))
    return rows, quad_error


def descriptive(values, inference):
    values = finite(values)
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if len(values) > 1 else None
    ci = None
    if inference:
        half = float(t.ppf(.975, len(values)-1)*std/np.sqrt(len(values)))
        ci = [mean-half, mean+half]
    return {'mean': mean, 'std': std, 'ci95': ci}


def run_comparison(hm, seeds, count, inference):
    rows, max_quad, max_error = [], 0.0, 0.0
    for seed in seeds:
        rng = np.random.default_rng(10000+seed)
        candidate, baseline = [], []
        for _ in range(count):
            length = float(np.exp(rng.uniform(np.log(.2), np.log(3))))
            q = float(np.exp(rng.uniform(np.log(.05), np.log(1))))
            u = float(rng.uniform(0, 3)*length)
            ref, err = reference(u, length, q*length)
            actual = float(finite(hm.kernel_exp_gauss(u, length, q*length)))
            candidate.append(abs(actual-ref))
            baseline.append(abs(np.exp(-abs(u)/length)-ref))
            max_quad, max_error = max(max_quad, err), max(max_error, candidate[-1])
        rows.append({'seed': seed, 'rng_seed': 10000+seed, 'count': count,
                     'candidate_mae': float(np.mean(candidate)), 'baseline_mae': float(np.mean(baseline)),
                     'candidate_errors': candidate, 'baseline_errors': baseline})
    c = np.array([row['candidate_mae'] for row in rows])
    b = np.array([row['baseline_mae'] for row in rows])
    d = b-c
    summary = {'candidate': descriptive(c, inference), 'baseline': descriptive(b, inference),
               'paired_difference': descriptive(d, inference), 'raw_per_seed': rows,
               'alpha': .05, 'practical_threshold': 1e-3, 'p_value': None,
               'sign_patterns': None, 'verdict': 'DESCRIPTIVE_ONLY',
               'max_quadrature_error': max_quad, 'max_candidate_error': max_error}
    if inference:
        outcomes = [abs(float(np.mean(np.asarray(s)*d))) for s in itertools.product((-1, 1), repeat=len(d))]
        p = sum(v >= abs(float(np.mean(d)))-1e-15 for v in outcomes)/len(outcomes)
        summary.update(p_value=p, sign_patterns=len(outcomes),
                       verdict='IMPROVED' if p < .05 and summary['paired_difference']['ci95'][0] > 1e-3 else 'INCONCLUSIVE')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('dry', 'smoke', 'full'), default='full')
    parser.add_argument('--output', type=Path, default=Path('results/hw2/current.json'))
    args = parser.parse_args()
    start = time.perf_counter()
    seeds = list(range(10)) if args.stage == 'full' else [0] if args.stage == 'smoke' else []
    count = 64 if args.stage == 'full' else 8 if args.stage == 'smoke' else 0
    result = {'schema_version': 2, 'started': now(), 'stage': args.stage,
              'environment': {'python': platform.python_version(), 'platform': platform.platform(),
                              'numpy': np.__version__, 'scipy': scipy.__version__},
              'seeds': seeds, 'cases_per_seed': count, 'properties': {}, 'comparison': None, 'verdict': 'FAIL'}
    try:
        result['inputs'] = inputs()
        if args.stage != 'dry':
            spec = importlib.util.spec_from_file_location('hw2_subject', ROOT/'src/hom_models.py')
            hm = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(hm)
            result['properties'], result['max_property_quadrature_error'] = run_properties(hm, seeds, count)
            result['comparison'] = run_comparison(hm, seeds, count, args.stage == 'full')
        result['verdict'] = 'PASS' if all(row['pass'] for row in result['properties'].values()) else 'FAIL'
    except Exception as exc:
        result['error'] = f'{type(exc).__name__}: {exc}'
    result.update(ended=now(), elapsed_seconds=time.perf_counter()-start)
    output = args.output if args.output.is_absolute() else ROOT/args.output
    try:
        text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding='utf-8')
    except Exception as exc:
        print(f'FAIL: cannot save valid result: {exc}', file=sys.stderr)
        return 1
    for pid, row in result['properties'].items():
        print(f"{pid}: {'PASS' if row['pass'] else 'FAIL'} cases={row['cases']} failures={row['failures']} max_metric={row['max_metric']:.12g}")
        if row['first_failure']:
            print(json.dumps(row['first_failure'], ensure_ascii=False, allow_nan=False))
    if result['comparison']:
        c = result['comparison']
        print(f"Comparison: {c['verdict']}; baseline={c['baseline']['mean']:.12g}; candidate={c['candidate']['mean']:.12g}; p={c['p_value']}")
    if result.get('error'):
        print(result['error'])
    print(f"{result['verdict']} stage={args.stage} output={output} elapsed={result['elapsed_seconds']:.3f}s")
    return 0 if result['verdict'] == 'PASS' else 1
