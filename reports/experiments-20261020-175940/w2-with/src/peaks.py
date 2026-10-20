import numpy as np
import pandas as pd
from scipy.signal import find_peaks
import os
from pathlib import Path

def process_spectrum(file_path):
    # Load data
    data = pd.read_csv(file_path, sep='\t')
    x = data['wavelength_nm'].values
    y = data['intensity'].values
    
    # Linear background subtraction
    # Fit a line to the ends of the spectrum to estimate background
    # Using first 50 and last 50 points
    z = np.polyfit(np.concatenate([x[:50], x[-50:]]), np.concatenate([y[:50], y[-50:]]), 1)
    p = np.poly1d(z)
    y_detrended = y - p(x)
    
    # Noise level estimation
    # Use the standard deviation of the detrended baseline (first 50 points)
    noise_level = np.std(y_detrended[:50])
    threshold = 5 * noise_level
    
    # Peak finding
    # height=threshold ensures peak is 5 times noise level
    # Add distance to avoid picking multiple points of the same peak
    peaks, properties = find_peaks(y_detrended, height=threshold, distance=30)
    
    results = []
    for peak in peaks:
        center = x[peak]
        height = y_detrended[peak]
        
        # FWHM calculation
        # Find where the intensity drops to half the peak height above background
        half_max = height / 2
        
        # Search for half-max on the left
        left_idx = peak
        while left_idx > 0 and y_detrended[left_idx] > half_max:
            left_idx -= 1
            
        # Search for half-max on the right
        right_idx = peak
        while right_idx < len(y_detrended) - 1 and y_detrended[right_idx] > half_max:
            right_idx += 1
            
        # Linear interpolation for more precise FWHM
        if left_idx > 0:
            x_left = x[left_idx] + (x[left_idx+1] - x[left_idx]) * \
                     (half_max - y_detrended[left_idx]) / (y_detrended[left_idx+1] - y_detrended[left_idx])
        else:
            x_left = x[0]
            
        if right_idx < len(y_detrended) - 1:
            x_right = x[right_idx] + (x[right_idx+1] - x[right_idx]) * \
                      (half_max - y_detrended[right_idx]) / (y_detrended[right_idx+1] - y_detrended[right_idx])
        else:
            x_right = x[-1]
            
        fwhm = x_right - x_left
        results.append([Path(file_path).name, center, fwhm])
        
    return results

def main():
    data_dir = Path('data')
    all_results = []
    
    # Process all .txt files in data/
    for file_path in sorted(data_dir.glob('*.txt')):
        all_results.extend(process_spectrum(file_path))
        
    # Save to results/peaks.csv
    df = pd.DataFrame(all_results, columns=['file', 'center_nm', 'fwhm_nm'])
    os.makedirs('results', exist_ok=True)
    df.to_csv('results/peaks.csv', index=False)
    print("Processing complete. Results saved to results/peaks.csv")

if __name__ == '__main__':
    main()
