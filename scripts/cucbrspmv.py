#!/usr/bin/env python3
"""
BSR SpMV implementation using unified cuSPARSE operations.
"""

import sys
import os

# Add the scripts directory to path to import cusparse_operations
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cusparse_operations import main, load_matrix, detect_gpu_environment, perform_bsr_spmv
import argparse


def main_bsr_spmv():
    parser = argparse.ArgumentParser(description='BSR SpMV implementation using cuSPARSE')
    parser.add_argument('matrix_path', help='Path to Matrix Market file')
    parser.add_argument('--alpha', type=float, default=1.0, help='Alpha parameter')
    parser.add_argument('--beta', type=float, default=0.0, help='Beta parameter')
    parser.add_argument('--block-size', type=int, default=4, help='Block size for BSR operations')
    parser.add_argument('--n-iterations', type=int, default=10, help='Number of iterations for SpMV operations')
    
    args = parser.parse_args()
    
    # Load matrix
    matrix = load_matrix(args.matrix_path)
    if matrix is None:
        print("TIMING_MS:0")
        return 1
    
    # Detect GPU environment - fail fast if not available
    gpu_info = detect_gpu_environment()
    print(f"GPU Environment: {gpu_info}", file=sys.stderr)
    
    if not gpu_info['cusparse_available']:
        print("Error: cuSPARSE/GPU environment not available", file=sys.stderr)
        print("TIMING_MS:0")
        return 1
    
    # Perform BSR SpMV
    print(f"Performing BSR SpMV...", file=sys.stderr)
    timing_ms, success = perform_bsr_spmv(matrix, args.alpha, args.beta, args.block_size, args.n_iterations)
    
    if success and timing_ms is not None:
        print(f"TIMING_MS:{timing_ms:.3f}")
        return 0
    else:
        print("TIMING_MS:0")
        return 1


if __name__ == '__main__':
    sys.exit(main_bsr_spmv())