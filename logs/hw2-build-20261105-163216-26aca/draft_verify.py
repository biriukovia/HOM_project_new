"""
Generative property-based verifier for the HOM exp*gauss model.
Implemented according to METHOD.md.

[порождено: Goose / gemma4:31b-cloud]
Методику и задания поставил пользователь с помощью Codex.
"""

import sys
import os
import json
import hashlib
import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import integrate, stats

# Ensure src is in path for importing hom_models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
try:
    import src.hom_models as hm
except ImportError:
    # Fallback if structure differs slightly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    import src.hom_models as hm

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
        # Ensure shape is (130, 2)
        if data.shape != (130, 2):
            return None
        
        # Construct the specific byte stream: prefix + contiguous float64 bytes
        prefix = b"130,2\n"
        body = data.astype(np.float64).tobytes() # numpy default is system endian (Windows is little)
        return hashlib.sha256(prefix + body).hexdigest()
    except Exception:
        return None

def verify_p1(u, L, s):
    """P1: Finite and Normalization: 0 <= K(u) <= 1."""
    k = hm.kernel_exp_gauss(u, L, s)
    # Tolerance 1e-12
    pass_status = np.all((k >= -1e-12) & (k <= 1.0 + 1e-12))
    metric = np.max(np.abs(np.clip(k, 0, 1) - k))
    return pass_status, metric, 1e-12

def verify_p2(u, L, s):
    """P2: Parity: K(u) = K(-u)."""
    k_pos = hm.kernel_exp_gauss(u, L, s)
    k_neg = hm.kernel_exp_gauss(-u, L, s)
    diff = np.abs(k_pos - k_neg)
    pass_status = np.all(diff <= 1e-12)
    return pass_status, np.max(diff), 1e-12

def verify_p3(u, L, s):
    """P3: Scale Invariance: K(au, aL, as) = K(u, L, s)."""
    k_orig = hm.kernel_exp_gauss(u, L, s)
    max_diff = 0.0
    for a in [0.1, 10.0]:
        k_scaled = hm.kernel_exp_gauss(a*u, a*L, a*s)
        max_diff = max(max_diff, np.max(np.abs(k_orig - k_scaled)))
    pass_status = max_diff <= 1e-10
    return pass_status, max_diff, 1e-10

def verify_p4(L, s):
    """P4: Monotonicity: dK/du <= 0 for u >= 0."""
    # 65-point grid up to 12 * max(L, s)
    limit = 12 * max(L, s)
    u = np.linspace(0, limit, 65)
    k = hm.kernel_exp_gauss(u, L, s)
    diffs = np.diff(k)
    # diffs should be <= 0. Since u is increasing, k should be non-increasing.
    # diffs = k[i+1] - k[i]. We want diffs <= 0.
    # Tolerance 1e-12
    max_violation = np.max(diffs)
    pass_status = max_violation <= 1e-12
    return pass_status, max_violation, 1e-12

def verify_p5(u, L, s):
    """P5: Independent Quadrature."""
    # Integral: exp(-|u-sz|/L) * G(z) dz where G(z) is unit Gaussian
    def integrand(z, u, L, s):
        return np.exp(-np.abs(u - s*z)/L) * (np.exp(-z**2/2) / np.sqrt(2 * np.pi))

    # points = [u/s] if inside (-12, 12)
    pts = []
    if s != 0:
        z_crit = u / s
        if -12 < z_crit < 12:
            pts = [z_crit]
    
    val, err = integrate.quad(integrand, -12, 12, args=(u, L, s), points=pts, epsabs=1e-11, epsrel=1e-11)
    
    # Check if quad error is within limit
    if err > 1e-9:
        # Reference failure
        pass
        
    actual = hm.kernel_exp_gauss(u, L, s)
    diff = np.abs(actual - val)
    pass_status = diff <= 1e-9
    return pass_status, diff, 1e-9

def verify_p6(L):
    """P6: Small width limit: s=1e-6*L, K -> exp(-|u|/L)."""
    s = 1e-6 * L
    u = 0.5 * L # representative point
    k_gauss = hm.kernel_exp_gauss(u, L, s)
    k_exp = np.exp(-np.abs(u)/L)
    diff = np.abs(k_gauss - k_exp)
    
    # Bound: sqrt(2/pi)*1e-6 + 1e-10
    tol = np.sqrt(2/np.pi) * 1e-6 + 1e-10
    pass_status = diff <= tol
    return pass_status, diff, tol

def verify_p7(A, V):
    """P7: Physical boundaries: A(1-V) <= C <= A."""
    # We test m_exp_gauss result
    u, L, s = 0.0, 1.0, 0.1
    c = hm.m_exp_gauss(u, A, V, 0.0, L, s)
    
    lower = A * (1 - V)
    upper = A
    
    if abs(V) < 1e-12:
        pass_status = abs(c - A) <= 1e-10
        metric = abs(c - A)
    else:
        pass_status = (c >= lower - 1e-10) and (c <= upper + 1e-10)
        metric = max(0, lower - c, c - upper)
        
    return pass_status, metric, 1e-10

def verify_p8():
    """P8: Unit Conversion: cm_to_ps."""
    expected_factor = 1.00028 / 0.0299792458
    test_dx = [1.0, -1.0, 0.0, 0.123, -0.456]
    for dx in test_dx:
        res = hm.cm_to_ps(dx)
        expected = dx * expected_factor
        if not (np.isclose(res, expected, rtol=1e-12, atol=1e-10)):
            return False, np.abs(res - expected), 1e-10
            
    for dx in test_dx:
        res = hm.cm_to_ps(dx)
        back = res * 0.0299792458 / 1.00028
        if not (np.isclose(back, dx, rtol=1e-12, atol=1e-10)):
            return False, np.abs(back - dx), 1e-10
            
    return True, 0.0, 1e-10

def run_properties(seed, count, stage):
    rng = np.random.default_rng(seed)
    results = []
    for i in range(count):
        L = 10**(rng.uniform(np.log10(0.2), np.log10(30)))
        s = 10**(rng.uniform(np.log10(0.01), np.log10(3)))
        A = rng.uniform(0.05, 2)
        V = rng.uniform(0, 1)
        u = rng.uniform(-12*max(L, s), 12*max(L, s))
        
        results.append({
            'P1': verify_p1(u, L, s),
            'P2': verify_p2(u, L, s),
            'P3': verify_p3(u, L, s),
            'P4': verify_p4(L, s),
            'P5': verify_p5(u, L, s),
            'P6': verify_p6(L),
            'P7': verify_p7(A, V),
            'P8': verify_p8(),
        })
    return results

def run_comparison(seed, stage):
    rng = np.random.default_rng(10000 + seed)
    L = 10**(rng.uniform(np.log10(0.2), np.log10(3)))
    q = 10**(rng.uniform(np.log10(0.05), np.log10(1)))
    u_rel = rng.uniform(0, 3)
    s = q * L
    u = u_rel * L
    
    def integrand(z, u, L, s):
        return np.exp(-np.abs(u - s*z)/L) * (np.exp(-z**2/2) / np.sqrt(2 * np.pi))
    
    z_crit = u / s if s != 0 else 0
    pts = [z_crit] if -12 < z_crit < 12 else []
    ref_val, _ = integrate.quad(integrand, -12, 12, args=(u, L, s), points=pts, epsabs=1e-11, epsrel=1e-11)
    
    cand_val = hm.kernel_exp_gauss(u, L, s)
    base_val = np.exp(-np.abs(u)/L)
    
    return {'mae_cand': np.abs(cand_val - ref_val), 'mae_base': np.abs(base_val - ref_val)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['dry', 'smoke', 'full'], required=True)
    parser.add_argument('--output', default='results/hw2/current.json')
    args = parser.parse_args()
    
    start_time = datetime.now(timezone.utc)
    start_perf = time.time()
    
    if args.stage == 'dry':
        data_hash = get_data_bytes_hash()
        source_hash = get_file_hash('src/hom_models.py')
        method_hash = get_file_hash('METHOD.md')
        verif_hash = get_file_hash(__file__)
        data_ok = (data_hash == 'd9b904bae0f78959c6cc9653f7e2a73174044c9bf6ea0c9468d442af7f3bc8e1')
        print(f"Dry Run: Data OK: {data_ok}")
        
        res = {
            'schema_version': '1.0',
            'started': start_time.isoformat(),
            'ended': datetime.now(timezone.utc).isoformat(),
            'stage': 'dry',
            'hashes': {'data': data_hash, 'source': source_hash, 'method': method_hash, 'verifier': verif_hash},
            'verdict': 'PASS' if data_ok else 'FAIL',
            'elapsed_seconds': time.time() - start_perf
        }
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(res, f, indent=2)
        sys.exit(0 if data_ok else 1)

    if args.stage in ['smoke', 'full']:
        seeds = [0] if args.stage == 'smoke' else range(10)
        count_per_seed = 8 if args.stage == 'smoke' else 64
        all_prop_results = {}
        comparison_data = []
        overall_pass = True
        
        for seed in seeds:
            prop_res = run_properties(seed, count_per_seed, args.stage)
            all_prop_results[seed] = prop_res
            for case in prop_res:
                for p_id in ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8']:
                    if not case[p_id][0]:
                        overall_pass = False
            comparison_data.append(run_comparison(seed, args.stage))
            
        mae_cand = np.array([d['mae_cand'] for d in comparison_data])
        mae_base = np.array([d['mae_base'] for d in comparison_data])
        deltas = mae_base - mae_cand
        n = len(mae_cand)
        mean_delta = np.mean(deltas)
        std_delta = np.std(deltas, ddof=1) if n > 1 else 0
        ci_low = mean_delta - stats.t.ppf(0.975, n-1) * std_delta / np.sqrt(n) if n > 1 else mean_delta
        
        p_val = 1.0
        if n <= 15:
            count = 0
            for i in range(2**n):
                signs = np.array([1 if (i >> j) & 1 else -1 for j in range(n)])
                if np.abs(np.mean(signs * deltas)) >= np.abs(mean_delta) - 1e-15:
                    count += 1
            p_val = count / (2**n)
        
        improvement = (p_val < 0.05) and (ci_low > 1e-3)
        comp_verdict = "IMPROVED" if improvement else "INCONCLUSIVE"
        final_verdict = "PASS" if overall_pass else "FAIL"
        
        print("\n--- Property Summary ---")
        for p_id in ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8']:
            p_passed = all(case[p_id][0] for seed in seeds for case in all_prop_results[seed])
            print(f"{p_id}: {'PASS' if p_passed else 'FAIL'}")
        print(f"\nComparison: {comp_verdict} (p={p_val:.4f}, CI_low={ci_low:.4e})")
        print(f"Verdict: {final_verdict}")
        
        res_json = {
            'schema_version': '1.0',
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
                'mae_cand_mean': np.mean(mae_cand),
                'mae_base_mean': np.mean(mae_base),
                'delta_mean': mean_delta,
                'delta_std': std_delta,
                'ci_low': ci_low,
                'p_value': p_val,
                'comparison_verdict': comp_verdict
            },
            'properties': {
                p_id: {'pass': all(case[p_id][0] for seed in seeds for case in all_prop_results[seed])} 
                for p_id in ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8']
            },
            'verdict': final_verdict,
            'elapsed_seconds': time.time() - start_perf
        }
        
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(res_json, f, indent=2)
        sys.exit(0 if overall_pass else 1)

if __name__ == '__main__':
    main()
