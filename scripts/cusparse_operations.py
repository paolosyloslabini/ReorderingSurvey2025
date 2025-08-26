#!/usr/bin/env python3
"""
Unified cuSPARSE operations implementation.
Provides CSR and BSR sparse matrix operations (SpMV and SpMM) using cuSPARSE.
Fails fast when GPU environment is not available - no CPU fallback.
"""

import sys
import time
import argparse
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from scipy.io import mmread


def detect_gpu_environment():
    """Detect if GPU environment is properly configured for cuSPARSE operations."""
    gpu_info = {
        'cuda_available': False,
        'cusparse_available': False,
        'nvidia_smi': False,
        'cupy_available': False
    }
    
    # Check for nvidia-smi
    import subprocess
    try:
        result = subprocess.run(['nvidia-smi', '-L'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and 'GPU' in result.stdout:
            gpu_info['nvidia_smi'] = True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check for CUDA runtime
    try:
        result = subprocess.run(['nvcc', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            gpu_info['cuda_available'] = True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check for CuPy/cuSPARSE
    try:
        import cupy as cp
        import cupyx.scipy.sparse
        # Try to initialize CuPy
        cp.cuda.Device(0).use()
        cp.array([1, 2, 3])  # Simple test
        gpu_info['cupy_available'] = True
        gpu_info['cusparse_available'] = True
    except ImportError:
        pass
    except Exception:
        # CuPy available but GPU not accessible
        pass
    
    return gpu_info


def perform_csr_spmv(matrix, alpha=1.0, beta=0.0, n_iterations=10):
    """Perform CSR sparse matrix-vector multiplication using cuSPARSE."""
    try:
        import cupy as cp
        import cupyx.scipy.sparse as cusp
        
        # Ensure matrix is in CSR format
        if not sp.isspmatrix_csr(matrix):
            matrix = matrix.tocsr()
        
        # Convert to GPU CSR matrix
        gpu_matrix = cusp.csr_matrix(matrix)
        
        # Create test vector
        vector_size = matrix.shape[1]
        test_vector = cp.random.rand(vector_size, dtype=cp.float32)
        
        # Warm up
        _ = gpu_matrix.dot(test_vector)
        cp.cuda.Device().synchronize()
        
        # Timed operation - perform multiple SpMV operations for better timing
        start_time = time.perf_counter()
        
        for _ in range(n_iterations):
            result = alpha * gpu_matrix.dot(test_vector)
            if beta != 0.0:
                # Add beta * previous result (for axpy-like operation)
                result = result + beta * result
        
        # Ensure all operations are complete
        cp.cuda.Device().synchronize()
        
        end_time = time.perf_counter()
        timing_ms = (end_time - start_time) * 1000 / n_iterations  # Average per operation
        
        return timing_ms, True
        
    except Exception as e:
        print(f"CSR SpMV failed: {e}", file=sys.stderr)
        return None, False


def perform_csr_spmm(matrix, alpha=1.0, beta=0.0, n_cols=32):
    """Perform CSR sparse matrix-matrix multiplication using cuSPARSE."""
    try:
        import cupy as cp
        import cupyx.scipy.sparse as cusp
        
        # Ensure matrix is in CSR format
        if not sp.isspmatrix_csr(matrix):
            matrix = matrix.tocsr()
        
        # Convert to GPU CSR matrix
        gpu_matrix = cusp.csr_matrix(matrix)
        
        # Create dense matrix for SpMM
        dense_matrix = cp.random.rand(matrix.shape[1], n_cols, dtype=cp.float32)
        
        # Warm up
        _ = gpu_matrix.dot(dense_matrix)
        cp.cuda.Device().synchronize()
        
        # Timed operation
        start_time = time.perf_counter()
        
        result = alpha * gpu_matrix.dot(dense_matrix)
        if beta != 0.0:
            # For complete SpMM: C = alpha * A * B + beta * C
            # Here we simulate with C as zero matrix for simplicity
            pass
        
        # Ensure computation is complete
        cp.cuda.Device().synchronize()
        
        end_time = time.perf_counter()
        timing_ms = (end_time - start_time) * 1000
        
        return timing_ms, True
        
    except Exception as e:
        print(f"CSR SpMM failed: {e}", file=sys.stderr)
        return None, False


def perform_bsr_spmv(matrix, alpha=1.0, beta=0.0, block_size=4, n_iterations=10):
    """Perform BSR sparse matrix-vector multiplication using cuSPARSE."""
    try:
        import cupy as cp
        import cupyx.scipy.sparse as cusp
        
        # Convert to BSR format
        if not sp.isspmatrix_bsr(matrix):
            # Convert to BSR with specified block size
            if sp.isspmatrix_csr(matrix):
                bsr_matrix = matrix.tobsr(blocksize=(block_size, block_size))
            else:
                bsr_matrix = matrix.tocsr().tobsr(blocksize=(block_size, block_size))
        else:
            bsr_matrix = matrix
        
        # Convert to GPU BSR matrix
        gpu_matrix = cusp.bsr_matrix(bsr_matrix)
        
        # Create test vector
        vector_size = bsr_matrix.shape[1]
        test_vector = cp.random.rand(vector_size, dtype=cp.float32)
        
        # Warm up
        _ = gpu_matrix.dot(test_vector)
        cp.cuda.Device().synchronize()
        
        # Timed operation
        start_time = time.perf_counter()
        
        for _ in range(n_iterations):
            result = alpha * gpu_matrix.dot(test_vector)
            if beta != 0.0:
                result = result + beta * result
        
        cp.cuda.Device().synchronize()
        
        end_time = time.perf_counter()
        timing_ms = (end_time - start_time) * 1000 / n_iterations
        
        return timing_ms, True
        
    except Exception as e:
        print(f"BSR SpMV failed: {e}", file=sys.stderr)
        return None, False


def perform_bsr_spmm(matrix, alpha=1.0, beta=0.0, block_size=4, n_cols=32):
    """Perform BSR sparse matrix-matrix multiplication using cuSPARSE."""
    try:
        import cupy as cp
        import cupyx.scipy.sparse as cusp
        
        # Convert to BSR format
        if not sp.isspmatrix_bsr(matrix):
            if sp.isspmatrix_csr(matrix):
                bsr_matrix = matrix.tobsr(blocksize=(block_size, block_size))
            else:
                bsr_matrix = matrix.tocsr().tobsr(blocksize=(block_size, block_size))
        else:
            bsr_matrix = matrix
        
        # Convert to GPU BSR matrix
        gpu_matrix = cusp.bsr_matrix(bsr_matrix)
        
        # Create dense matrix for SpMM
        dense_matrix = cp.random.rand(bsr_matrix.shape[1], n_cols, dtype=cp.float32)
        
        # Warm up
        _ = gpu_matrix.dot(dense_matrix)
        cp.cuda.Device().synchronize()
        
        # Timed operation
        start_time = time.perf_counter()
        
        result = alpha * gpu_matrix.dot(dense_matrix)
        if beta != 0.0:
            pass  # Simplified for benchmarking
        
        cp.cuda.Device().synchronize()
        
        end_time = time.perf_counter()
        timing_ms = (end_time - start_time) * 1000
        
        return timing_ms, True
        
    except Exception as e:
        print(f"BSR SpMM failed: {e}", file=sys.stderr)
        return None, False


def load_matrix(matrix_path):
    """Load matrix from Matrix Market file."""
    try:
        matrix = mmread(matrix_path)
        # Convert to CSR for consistency
        if hasattr(matrix, 'tocsr'):
            matrix = matrix.tocsr()
        return matrix
    except Exception as e:
        print(f"Error loading matrix from {matrix_path}: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description='Unified cuSPARSE operations implementation')
    parser.add_argument('matrix_path', help='Path to Matrix Market file')
    parser.add_argument('operation', choices=['csr_spmv', 'csr_spmm', 'bsr_spmv', 'bsr_spmm'],
                        help='cuSPARSE operation to perform')
    parser.add_argument('--alpha', type=float, default=1.0, help='Alpha parameter')
    parser.add_argument('--beta', type=float, default=0.0, help='Beta parameter')
    parser.add_argument('--block-size', type=int, default=4, help='Block size for BSR operations')
    parser.add_argument('--n-cols', type=int, default=32, help='Number of columns for SpMM operations')
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
    
    # Perform the requested operation
    timing_ms = None
    success = False
    
    if args.operation == 'csr_spmv':
        print(f"Performing CSR SpMV...", file=sys.stderr)
        timing_ms, success = perform_csr_spmv(matrix, args.alpha, args.beta, args.n_iterations)
    elif args.operation == 'csr_spmm':
        print(f"Performing CSR SpMM...", file=sys.stderr)
        timing_ms, success = perform_csr_spmm(matrix, args.alpha, args.beta, args.n_cols)
    elif args.operation == 'bsr_spmv':
        print(f"Performing BSR SpMV...", file=sys.stderr)
        timing_ms, success = perform_bsr_spmv(matrix, args.alpha, args.beta, args.block_size, args.n_iterations)
    elif args.operation == 'bsr_spmm':
        print(f"Performing BSR SpMM...", file=sys.stderr)
        timing_ms, success = perform_bsr_spmm(matrix, args.alpha, args.beta, args.block_size, args.n_cols)
    
    if success and timing_ms is not None:
        print(f"TIMING_MS:{timing_ms:.3f}")
        return 0
    else:
        print("TIMING_MS:0")
        return 1


if __name__ == '__main__':
    sys.exit(main())