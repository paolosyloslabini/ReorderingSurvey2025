#!/usr/bin/env python3
"""
Direct CSR cuSPARSE multiplication implementation.
Focuses specifically on CSR format operations with cuSPARSE.
Falls back to CPU-based sparse matrix multiplication when GPU not available.
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
        import subprocess
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


def perform_csr_multiply_gpu(matrix, alpha=1.0, beta=0.0):
    """Perform CSR sparse matrix multiplication using cuSPARSE directly."""
    try:
        import cupy as cp
        import cupyx.scipy.sparse as cusp
        
        # Ensure matrix is in CSR format
        if not sp.isspmatrix_csr(matrix):
            matrix = matrix.tocsr()
        
        # Convert to GPU CSR matrix
        gpu_matrix = cusp.csr_matrix(matrix)
        
        # For CSR SpMV (matrix-vector multiplication), create a vector
        # For a more comprehensive benchmark, we'll do multiple SpMV operations
        vector_size = matrix.shape[1]
        test_vector = cp.random.rand(vector_size, dtype=cp.float32)
        
        # Warm up
        _ = gpu_matrix.dot(test_vector)
        cp.cuda.Device().synchronize()
        
        # Timed operation - perform multiple SpMV operations for better timing
        n_iterations = 10
        start_time = time.perf_counter()
        
        for _ in range(n_iterations):
            result = alpha * gpu_matrix.dot(test_vector)
            if beta != 0.0:
                # Add beta * previous result (for more complex operation)
                result = result + beta * result
        
        # Ensure all operations are complete
        cp.cuda.Device().synchronize()
        
        end_time = time.perf_counter()
        timing_ms = (end_time - start_time) * 1000 / n_iterations  # Average per operation
        
        return timing_ms, True
        
    except Exception as e:
        print(f"GPU CSR multiply failed: {e}", file=sys.stderr)
        return None, False


def perform_csr_multiply_cpu(matrix, alpha=1.0, beta=0.0):
    """Perform CSR sparse matrix multiplication using CPU (SciPy)."""
    try:
        # Ensure matrix is in CSR format
        if not sp.isspmatrix_csr(matrix):
            matrix = matrix.tocsr()
        
        # Create a test vector
        np.random.seed(42)  # For reproducible timing
        test_vector = np.random.rand(matrix.shape[1]).astype(np.float32)
        
        # Perform multiple operations for better timing
        n_iterations = 10
        start_time = time.perf_counter()
        
        for _ in range(n_iterations):
            result = alpha * matrix.dot(test_vector)
            if beta != 0.0:
                # Add beta * previous result (for more complex operation)
                result = result + beta * result
        
        end_time = time.perf_counter()
        timing_ms = (end_time - start_time) * 1000 / n_iterations  # Average per operation
        
        return timing_ms, True
        
    except Exception as e:
        print(f"CPU CSR multiply failed: {e}", file=sys.stderr)
        return None, False


def load_matrix(matrix_path):
    """Load matrix from Matrix Market file."""
    try:
        matrix = mmread(matrix_path)
        if not sp.issparse(matrix):
            matrix = sp.csr_matrix(matrix)
        print(f"Loaded matrix: {matrix.shape}, nnz={matrix.nnz}", file=sys.stderr)
        return matrix
    except Exception as e:
        print(f"Failed to load matrix: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description='CSR cuSPARSE multiplication implementation')
    parser.add_argument('matrix_path', help='Path to Matrix Market file')
    parser.add_argument('--alpha', type=float, default=1.0, help='Alpha parameter')
    parser.add_argument('--beta', type=float, default=0.0, help='Beta parameter')
    parser.add_argument('--force-cpu', action='store_true', help='Force CPU implementation')
    
    args = parser.parse_args()
    
    # Load matrix
    matrix = load_matrix(args.matrix_path)
    if matrix is None:
        print("TIMING_MS:0")
        return 1
    
    # Detect GPU environment
    gpu_info = detect_gpu_environment()
    
    # Print environment info to stderr
    print(f"GPU Environment: {gpu_info}", file=sys.stderr)
    print(f"CSR cuSPARSE implementation starting...", file=sys.stderr)
    
    timing_ms = None
    success = False
    
    # Try GPU implementation first if available and not forced to CPU
    if not args.force_cpu and gpu_info['cusparse_available']:
        print("Attempting GPU CSR cuSPARSE multiply...", file=sys.stderr)
        timing_ms, success = perform_csr_multiply_gpu(matrix, args.alpha, args.beta)
        if success:
            print("GPU CSR multiply completed successfully", file=sys.stderr)
    
    # Fall back to CPU implementation
    if not success:
        print("Using CPU CSR sparse matrix multiplication", file=sys.stderr)
        timing_ms, success = perform_csr_multiply_cpu(matrix, args.alpha, args.beta)
    
    if success and timing_ms is not None:
        print(f"TIMING_MS:{timing_ms:.3f}")
        return 0
    else:
        print("TIMING_MS:0")
        return 1


if __name__ == '__main__':
    sys.exit(main())