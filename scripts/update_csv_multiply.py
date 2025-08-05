#!/usr/bin/env python3
"""
Parse cuSPARSE results and update CSV with multiplication metrics
"""
import sys
import pandas as pd
import os

def parse_cusparse_results(results_file):
    """Parse cuSPARSE results file and return metrics dict"""
    metrics = {}
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            for line in f:
                if ',' in line:
                    key, value = line.strip().split(',', 1)
                    try:
                        metrics[key] = float(value)
                    except ValueError:
                        metrics[key] = value
    return metrics

def main():
    if len(sys.argv) < 7:
        print(f"Usage: {sys.argv[0]} <csv> <impl> <param_set> <time_ms> <status> <timestamp> [results_file]")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    impl = sys.argv[2]
    param_set = sys.argv[3]
    time_ms = float(sys.argv[4])
    status = int(sys.argv[5])
    timestamp = sys.argv[6]
    results_file = sys.argv[7] if len(sys.argv) > 7 else None
    
    # Load existing CSV
    df = pd.read_csv(csv_file)
    
    # Update basic multiplication info
    df['mult_type'] = impl
    df['mult_param_set'] = param_set
    df['exit_code'] = status
    df['timestamp'] = timestamp
    
    # For cuSPARSE, use timing from results file if available
    if impl == 'cucsrspmm' and results_file and os.path.exists(results_file):
        metrics = parse_cusparse_results(results_file)
        if 'avg_time_ms' in metrics:
            df['mult_time_ms'] = metrics['avg_time_ms']
        else:
            df['mult_time_ms'] = time_ms
        
        # Add GFLOPS if available
        if 'gflops' in metrics:
            df['gflops'] = metrics['gflops']
        else:
            # Calculate GFLOPS if we have the metrics
            if 'avg_time_ms' in metrics and 'nnz' in metrics:
                nnz = metrics.get('nnz', 0)
                num_cols_B = metrics.get('num_cols_B', 64)
                gflops = (2.0 * nnz * num_cols_B) / (metrics['avg_time_ms'] * 1e6)
                df['gflops'] = gflops
        
        # Store additional metrics as JSON-like string
        mult_metrics = []
        for key in ['nnz', 'num_rows', 'num_cols', 'num_cols_B']:
            if key in metrics:
                mult_metrics.append(f"{key}:{metrics[key]}")
        if mult_metrics:
            df['mult_metrics'] = ';'.join(mult_metrics)
    else:
        # Default behavior for other implementations
        df['mult_time_ms'] = time_ms
    
    # Save updated CSV
    df.to_csv(csv_file, index=False)

if __name__ == '__main__':
    main()