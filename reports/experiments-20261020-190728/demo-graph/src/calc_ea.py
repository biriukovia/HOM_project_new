import numpy as np
import pandas as pd
import os

# Constants
R = 8.314462618  # J/(mol*K)

def main():
    # 1. Load data
    df = pd.read_csv('data/raw/rates.csv')
    
    # Filter 25-70 C (Column is T_C)
    df_filtered = df[(df['T_C'] >= 25) & (df['T_C'] <= 70)].copy()
    df_filtered['T_K'] = df_filtered['T_C'] + 273.15
    df_filtered['invT'] = 1.0 / df_filtered['T_K']
    df_filtered['ln_k'] = np.log(df_filtered['k_s'])
    
    # 2. Exclude Series 2024-03 (faulty thermostat)
    if 'series' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['series'] != '2024-03']
    
    x = df_filtered['invT'].values
    y = df_filtered['ln_k'].values
    
    # Linearity check (Linear Regression)
    coeffs = np.polyfit(x, y, 1)
    slope, intercept = coeffs
    correlation_matrix = np.corrcoef(x, y)
    r_squared = correlation_matrix[0, 1]**2
    
    # Save linearity check
    os.makedirs('results', exist_ok=True)
    pd.DataFrame({'R2': [r_squared]}).to_csv('results/linearity_check.csv', index=False)
    
    # 3. Calculate Ea (Main method: slope)
    ea_j_mol = -slope * R
    ea_kj_mol = ea_j_mol / 1000.0
    
    pd.DataFrame({'Ea_kJ_mol': [ea_kj_mol]}).to_csv('results/ea_result.csv', index=False)
    
    # 4. Independent verification (Two-point method)
    # Using the extremes of the filtered data
    x_first, y_first = x[0], y[0]
    x_last, y_last = x[-1], y[-1]
    
    slope_2p = (y_last - y_first) / (x_last - x_first)
    ea_2p_kj_mol = (-slope_2p * R) / 1000.0
    
    pd.DataFrame({'Ea_2p_kJ_mol': [ea_2p_kj_mol]}).to_csv('results/verification.csv', index=False)
    
    # 5. Comparison
    diff_percent = abs(ea_kj_mol - ea_2p_kj_mol) / ea_kj_mol * 100
    
    print(f"R2: {r_squared:.4f}")
    print(f"Ea (Linear): {ea_kj_mol:.4f} kJ/mol")
    print(f"Ea (2-point): {ea_2p_kj_mol:.4f} kJ/mol")
    print(f"Diff: {diff_percent:.4f}%")

if __name__ == '__main__':
    main()
