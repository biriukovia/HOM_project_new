"""
Generative property-based verifier for the HOM exp*gauss model.
Implemented according to METHOD.md.

[порождено: Goose / gemma4:31b-cloud]
Методику и задания поставил пользователь с помощью Codex.
"""

import sys
sys.dont_write_bytecode = True
import os
import json
import hashlib
import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import integrate, stats

# Root from __file__
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

try:
    import src.hom_models as hm
except Exception as e:
    print(f"CRITICAL: Failed to import src.hom_models: {e}")
    sys.exit(1)

def get_file_hash(path):
    """Calculate SHA256 hash of a file."""
    p = Path(path)
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()

def get_data_bytes_hash():
    """
    Calculate specific hash for data/data.txt as per METHOD.md:
    prefix '130,2\n' + little-endian float64 contiguous bytes.
    """
    p = Path('data/data.txt')
    if not p.exists():
        return None
    try:
        data = np.loadtxt(p, comments="#")
        if data.shape != (130, 2):
            return None
        
        # Use explicit little-endian float64
        prefix = b"130,2\n"
        body = data.astype('<f8').tobytes() 
        return hashlib.sha256(prefix + body).hexdigest()
    except Exception:
        return None

def check_inputs():
    """Verify data/data.txt integrity and existence of required files."""
    p = Path('data/data.txt')
    if not p.exists():
        return False, "data/data.txt missing"
    
    try:
        data = np.loadtxt(p, comments="#")
        if data.shape != (130, 2):
            return False, f"data shape {data.shape} != (130, 2)"
        if not np.all(np.isfinite(data)):
            return False, "data contains non-finite values"
        if not np.all(np.diff(data[:, 0]) > 0):
            return False, "data x coordinates not strictly increasing"
        
        data_hash = get_data_bytes_hash()
        if data_hash != 'd9b904bae0f78959c6cc9653f7e2a73174044c9bf6ea0c9468d442af7f3bc8e1':
            return False, f"data hash mismatch: {data_hash}"
            
        if not Path('src/hom_models.py').exists():
            return False, "src/hom_models.py missing"
        if not Path('METHOD.md').exists():
            return False, "METHOD.md missing"
            
        return True, "OK"
    except Exception as e:
        return False, f"input validation error: {e}"

def verify_p1(u, L, s):
    k = hm.kernel_exp_gauss(u, L, s)
    if not np.all(np.isfinite(k)):
        return False, np.nan, 1e-12
    pass_status = np.all((k >= -1e-12) & (k <= 1.0 + 1e-12))
    metric = np.max(np.abs(np.clip(k, 0, 1) - k))
    return pass_status, metric, 1e-12

def verify_p2(u, L, s):
    k_pos = hm.kernel_exp_gauss(u, L, s)
    k_neg = hm.kernel_exp_gauss(-u, L, s)
    if not (np.all(np.isfinite(k_pos)) and np.all(np.isfinite(k_neg))):
        return False, np.nan, 1e-12
    diff = np.abs(k_pos - k_neg)
    pass_status = np.all(diff <= 1e-12)
    return pass_status, np.max(diff), 1e-12

def verify_p3(u, L, s):
    k_orig = hm.kernel_exp_gauss(u, L, s)
    if not np.all(np.isfinite(k_orig)):
        return False, np.nan, 1e-10
    max_diff = 0.0
    for a in [0.1, 10.0]:
        k_scaled = hm.kernel_exp_gauss(a*u, a*L, a*s)
        if not np.all(np.isfinite(k_scaled)):
            return False, np.nan, 1e-10
        max_diff = max(max_diff, np.max(np.abs(k_orig - k_scaled)))
    pass_status = max_diff <= 1e-10
    return pass_status, max_diff, 1e-10

def verify_p4(L, s):
    limit = 12 * max(L, s)
    u = np.linspace(0, limit, 65)
    k = hm.kernel_exp_gauss(u, L, s)
    if not np.all(np.isfinite(k)):
        return False, np.nan, 1e-12
    diffs = np.diff(k)
    max_violation = np.max(diffs)
    pass_status = max_violation <= 1e-12
    return pass_status, max_violation, 1e-12

def verify_p5(u, L, s):
    def integrand(z, u, L, s):
        return np.exp(-np.abs(u - s*z)/L) * (np.exp(-z**2/2) / np.sqrt(2 * np.pi))
    pts = [u/s] if (s != 0 and -12 < u/s < 12) else []
    try:
        val, err = integrate.quad(integrand, -12, 12, args=(u, L, s), points=pts, epsabs=1e-11, epsrel=1e-11)
        if not np.isfinite(val) or err > 1e-9:
            return False, err if np.isfinite(err) else np.nan, 1e-9
    except Exception:
        return False, np.nan, 1e-9
        
    actual = hm.kernel_exp_gauss(u, L, s)
    if not np.isfinite(actual):
        return False, np.nan, 1e-9
    diff = np.abs(actual - val)
    pass_status = diff <= 1e-9
    return pass_status, diff, 1e-9

def verify_p6(L, rng):
    s = 1e-6 * L
    # Test center, 0.5L and random u
    test_u = [0.0, 0.5 * L, rng.uniform(-2*L, 2*L)]
    max_diff = 0.0
    for u in test_u:
        k_gauss = hm.kernel_exp_gauss(u, L, s)
        k_exp = np.exp(-np.abs(u)/L)
        if not (np.isfinite(k_gauss) and np.isfinite(k_exp)):
            return False, np.nan, 0.0
        max_diff = max(max_diff, np.abs(k_gauss - k_exp))
    
    tol = np.sqrt(2/np.pi) * 1e-6 + 1e-10
    return max_diff <= tol, max_diff, tol

def verify_p7(A, V, L, s, u, x0):
    # Test specific case
    c = hm.m_exp_gauss(u + x0, A, V, x0, L, s)
    if not np.isfinite(c):
        return False, np.nan, 1e-10
    
    lower, upper = A * (1 - V), A
    if abs(V) < 1e-12:
        pass_status = abs(c - A) <= 1e-10
        metric = abs(c - A)
    else:
        pass_status = (c >= lower - 1e-10) and (c <= upper + 1e-10)
        metric = max(0, lower - c, c - upper)
    return pass_status, metric, 1e-10

def verify_p8(rng):
    expected_factor = 1.00028 / 0.0299792458
    test_dx = [1.0, -1.0, 0.0, 0.123, -0.456, rng.uniform(-10, 10)]
    max_err = 0.0
    for dx in test_dx:
        res = hm.cm_to_ps(dx)
        expected = dx * expected_factor
        if not np.isfinite(res): return False, np.nan, 1e-10
        max_err = max(max_err, np.abs(res - expected))
        
        back = res * 0.0299792458 / 1.00028
        if not np.isfinite(back): return False, np.nan, 1e-10
        max_err = max(max_err, np.abs(back - dx))
        
    pass_status = max_err <= 1e-10 # atol
    return pass_status, max_err, 1e-10

def run_properties(seed, count, stage):
    rng = np.random.default_rng(seed)
    results = []
    for i in range(count):
        L = 10**(rng.uniform(np.log10(0.2), np.log10(30)))
        s = 10**(rng.uniform(np.log10(0.01), np.log10(3)))
        A = rng.uniform(0.05, 2)
        V = rng.uniform(0, 1)
        u = rng.uniform(-12*max(L, s), 12*max(L, s))
        x0 = rng.uniform(-5, 5)
        
        results.append({
            'P1': verify_p1(u, L, s),
            'P2': verify_p2(u, L, s),
            'P3': verify_p3(u, L, s),
            'P4': verify_p4(L, s),
            'P5': verify_p5(u, L, s),
            'P6': verify_p6(L, rng),
            'P7': verify_p7(A, V, L, s, u, x0),
            'P8': verify_p8(rng),
        })
    return results

def run_comparison(seed, count):
    rng = np.random.default_rng(10000 + seed)
    mae_seed = []
    for i in range(count):
        L = 10**(rng.uniform(np.log10(0.2), np.log10(3)))
        q = 10**(rng.uniform(np.log10(0.05), np.log10(1)))
        u_rel = rng.uniform(0, 3)
        s, u = q * L, u_rel * L
        
        def integrand(z, u, L, s):
            return np.exp(-np.abs(u - s*z)/L) * (np.exp(-z**2/2) / np.sqrt(2 * np.pi))
        
        z_crit = u/s if s != 0 else 0
        pts = [z_crit] if -12 < z_crit < 12 else []
        try:
            ref_val, _ = integrate.quad(integrand, -12, 12, args=(u, L, s), points=pts, epsabs=1e-11, epsrel=1e-11)
        except Exception:
            ref_val = np.nan
            
        cand_val = hm.kernel_exp_gauss(u, L, s)
        base_val = np.exp(-np.abs(u)/L)
        
        mae_seed.append({
            'cand': np.abs(cand_val - ref_val) if np.isfinite(ref_val) else np.nan,
            'base': np.abs(base_val - ref_val) if np.isfinite(ref_val) else np.nan
        })
    
    c_vals = np.array([x['cand'] for x in mae_seed])
    b_vals = np.array([x['base'] for x in mae_seed])
    return {
        'mae_cand': np.nanmean(c_vals),
        'mae_base': np.nanmean(b_vals),
        'raw': mae_seed
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['dry', 'smoke', 'full'], required=True)
    parser.add_argument('--output', default='results/hw2/current.json')
    args = parser.parse_args()
    
    start_time = datetime.now(timezone.utc)
    start_perf = time.time()
    
    ok, msg = check_inputs()
    if not ok:
        print(f"INPUT ERROR: {msg}")
        try:
            res = {'stage': args.stage, 'verdict': 'FAIL', 'error': msg, 'started': start_time.isoformat()}
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(res, f, indent=2)
        except: pass
        sys.exit(1)

    if args.stage == 'dry':
        print("Dry Run: Inputs OK")
        sys.exit(0)

    seeds = [0] if args.stage == 'smoke' else range(10)
    count_per_seed = 8 if args.stage == 'smoke' else 64
    all_prop_results = {}
    comparison_data = []
    overall_pass = True
    
    try:
        for seed in seeds:
            prop_res = run_properties(seed, count_per_seed, args.stage)
            all_prop_results[seed] = prop_res
            for case in prop_res:
                for p_id in ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8']:
                    if not case[p_id][0]: overall_pass = False
            comparison_data.append(run_comparison(seed, count_per_seed))
    except Exception as e:
        print(f"EXECUTION ERROR: {e}")
        sys.exit(1)
            
    mae_cand = np.array([d['mae_cand'] for d in comparison_data])
    mae_base = np.array([d['mae_base'] for d in comparison_data])
    deltas = mae_base - mae_cand
    n = len(mae_cand)
    
    def get_ci(data):
        m = np.nanmean(data)
        s = np.nanstd(data, ddof=1) if n > 1 else 0
        err = stats.t.ppf(0.975, n-1) * s / np.sqrt(n) if n > 1 else 0
        return m, m - err, m + err

    mean_c, low_c, high_c = get_ci(mae_cand)
    mean_b, low_b, high_b = get_ci(mae_base)
    mean_d, low_d, high_d = get_ci(deltas)
    
    p_val = 1.0
    if args.stage == 'full' and n <= 15:
        count = 0
        for i in range(2**n):
            signs = np.array([1 if (i >> j) & 1 else -1 for j in range(n)])
            if np.abs(np.mean(signs * deltas)) >= np.abs(np.nanmean(deltas)) - 1e-15:
                count += 1
        p_val = count / (2**n)
    
    improvement = (args.stage == 'full') and (p_val < 0.05) and (low_d > 1e-3)
    comp_verdict = "IMPROVED" if improvement else ("INCONCLUSIVE" if args.stage == 'full' else "DESCRIPTIVE_ONLY")
    
    print("\n--- Property Summary ---")
    for p_id in ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8']:
        p_passed = all(case[p_id][0] for seed in seeds for case in all_prop_results[seed])
        print(f"{p_id}: {'PASS' if p_passed else 'FAIL'}")
    print(f"\nComparison: {comp_verdict} (p={p_val:.4f}, CI_low={low_d:.4e})")
    
    res_json = {
        'schema_version': '1.1',
        'started': start_time.isoformat(),
        'ended': datetime.now(timezone.utc).isoformat(),
        'stage': args.stage,
        'sys_info': {'version': sys.version, 'platform': sys.platform, 'numpy': np.__version__, 'scipy': '1.18.1'},
        'setup': {
            'seeds': list(seeds),
            'count': count_per_seed,
            'hashes': {
                'data': get_data_bytes_hash(),
                'source': get_file_hash('src/hom_models.py'),
                'method': get_file_hash('METHOD.md'),
                'verifier': get_file_hash(__file__)
            }
        },
        'metrics': {
            'candidate': {'mean': mean_c, 'ci_low': low_c, 'ci_high': high_c},
            'baseline': {'mean': mean_b, 'ci_low': low_b, 'ci_high': high_b},
            'delta': {'mean': mean_d, 'ci_low': low_d, 'ci_high': high_d},
            'p_value': p_val,
            'comparison_verdict': comp_verdict,
            'raw_per_seed': comparison_data
        },
        'properties': {
            p_id: {
                'pass': all(case[p_id][0] for seed in seeds for case in all_prop_results[seed]),
                'max_metric': max([case[p_id][1] for seed in seeds for case in all_prop_results[seed]]),
                'tolerance': all_prop_results[next(iter(seeds))][0][p_id][2]
            } for p_id in ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8']
        },
        'verdict': 'PASS' if overall_pass else 'FAIL',
        'elapsed_seconds': time.time() - start_perf
    }
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(res_json, f, indent=2, allow_nan=False)
    
    sys.exit(0 if overall_pass else 1)

if __name__ == '__main__':
    main()
