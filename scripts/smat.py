#!/usr/bin/env python3
"""
SMAT (SMaT) SpMM implementation using the SMAT library.
SMAT is a sparse matrix multiplication library that utilizes Tensor Cores for unstructured sparse matrices.
"""

import sys
import os
import subprocess
import time
import argparse
from pathlib import Path
import numpy as np
from scipy.io import mmread


def detect_smat_environment():
    """Detect if SMAT environment is properly configured."""
    smat_info = {
        'cuda_available': False,
        'nvidia_smi': False,
        'smat_binary': False,
        'binary_path': None
    }
    
    # Check for nvidia-smi
    try:
        result = subprocess.run(['nvidia-smi', '-L'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and 'GPU' in result.stdout:
            smat_info['nvidia_smi'] = True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check for CUDA runtime
    try:
        result = subprocess.run(['nvcc', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            smat_info['cuda_available'] = True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check for SMAT binary (look in common installation paths)
    possible_paths = [
        '/opt/smat/bin/hgemm',
        '/usr/local/bin/hgemm',
        '/usr/bin/hgemm',
        './build/smat/bin/hgemm',
        './smat/output/bin/hgemm',
        os.path.expanduser('~/smat/output/bin/hgemm'),
        os.path.join(os.environ.get('SMAT_HOME', ''), 'bin', 'hgemm'),
    ]
    
    for path in possible_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            smat_info['smat_binary'] = True
            smat_info['binary_path'] = path
            break
    
    return smat_info


def load_matrix(matrix_path):
    """Load a Matrix Market file and return basic info."""
    try:
        matrix = mmread(matrix_path)
        if hasattr(matrix, 'tocsr'):
            matrix = matrix.tocsr()
        return matrix
    except Exception as e:
        print(f"Error loading matrix {matrix_path}: {e}", file=sys.stderr)
        return None


def run_smat_multiplication(matrix_path, binary_path, m=512, n=512, k=512, n_mult=1, warmup_iterations=1, profiling_iterations=10):
    """
    Run SMAT sparse matrix multiplication.
    
    Args:
        matrix_path: Path to Matrix Market file
        binary_path: Path to SMAT hgemm binary
        m, n, k: Matrix dimensions for SpMM (A: m×k, B: k×n, C: m×n)
        n_mult: Multiplier for N dimension
        warmup_iterations: Number of warmup iterations
        profiling_iterations: Number of profiling iterations
    
    Returns:
        (timing_ms, success): Timing in milliseconds and success flag
    """
    try:
        # Prepare SMAT command
        cmd = [
            binary_path,
            f'-M={m}',
            f'-N={n}',
            f'-K={k}',
            '-enable_wmma=true',
            '-enable_mma=true',
            f'-warmup_iterations={warmup_iterations}',
            f'-profiling_iterations={profiling_iterations}',
            '-sleep_duration=100',
            '-enable_check=false',
            f'-n_mult={n_mult}',
            f'-filename={matrix_path}'
        ]
        
        print(f"Running SMAT command: {' '.join(cmd)}", file=sys.stderr)
        
        # Run SMAT with timing
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        end_time = time.time()
        
        if result.returncode != 0:
            print(f"SMAT execution failed with return code {result.returncode}", file=sys.stderr)
            print(f"STDERR: {result.stderr}", file=sys.stderr)
            return None, False
        
        # Parse output for timing information
        # SMAT outputs timing information to stdout
        output_lines = result.stdout.strip().split('\n')
        timing_ms = None
        
        for line in output_lines:
            # Look for timing patterns in SMAT output
            if 'avg' in line.lower() and ('ms' in line.lower() or 'time' in line.lower()):
                # Try to extract timing from various possible formats
                try:
                    # Look for patterns like "avg: 1.234 ms" or "time: 1.234"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'avg' in part.lower() or 'time' in part.lower():
                            # Look for a number in the next few parts
                            for j in range(i+1, min(i+4, len(parts))):
                                try:
                                    val = float(parts[j])
                                    timing_ms = val
                                    break
                                except ValueError:
                                    continue
                            if timing_ms is not None:
                                break
                except (ValueError, IndexError):
                    continue
                
                if timing_ms is not None:
                    break
        
        # If we couldn't parse timing from output, use wall-clock time as fallback
        if timing_ms is None:
            timing_ms = (end_time - start_time) * 1000
            print(f"Could not parse SMAT timing, using wall-clock time: {timing_ms:.3f}ms", file=sys.stderr)
        else:
            print(f"Parsed SMAT timing: {timing_ms:.3f}ms", file=sys.stderr)
        
        return timing_ms, True
        
    except subprocess.TimeoutExpired:
        print("SMAT execution timed out", file=sys.stderr)
        return None, False
    except Exception as e:
        print(f"Error running SMAT: {e}", file=sys.stderr)
        return None, False


def main_smat():
    parser = argparse.ArgumentParser(description='SMAT SpMM implementation')
    parser.add_argument('matrix_path', help='Path to Matrix Market file')
    parser.add_argument('--alpha', type=float, default=1.0, help='Alpha parameter (for compatibility, not used by SMAT)')
    parser.add_argument('--beta', type=float, default=0.0, help='Beta parameter (for compatibility, not used by SMAT)')
    parser.add_argument('--m', type=int, default=512, help='M dimension')
    parser.add_argument('--n', type=int, default=512, help='N dimension')
    parser.add_argument('--k', type=int, default=512, help='K dimension')
    parser.add_argument('--n-mult', type=int, default=1, help='N multiplier (n_mult * MMA_N)')
    parser.add_argument('--warmup-iterations', type=int, default=1, help='Number of warmup iterations')
    parser.add_argument('--profiling-iterations', type=int, default=10, help='Number of profiling iterations')
    
    args = parser.parse_args()
    
    # Load matrix for basic validation
    matrix = load_matrix(args.matrix_path)
    if matrix is None:
        print("TIMING_MS:0")
        return 1
    
    # Detect SMAT environment
    smat_info = detect_smat_environment()
    print(f"SMAT Environment: {smat_info}", file=sys.stderr)
    
    if not smat_info['smat_binary']:
        print("Error: SMAT binary (hgemm) not found. Please install SMAT and ensure hgemm is in PATH or set SMAT_HOME.", file=sys.stderr)
        print("TIMING_MS:0")
        return 1
    
    if not smat_info['cuda_available']:
        print("Warning: CUDA not detected. SMAT requires CUDA for GPU operations.", file=sys.stderr)
        # Continue anyway as SMAT might work with different CUDA setup
    
    # Run SMAT multiplication
    print(f"Performing SMAT SpMM with matrix {args.matrix_path}...", file=sys.stderr)
    timing_ms, success = run_smat_multiplication(
        args.matrix_path, 
        smat_info['binary_path'],
        args.m, args.n, args.k, args.n_mult,
        args.warmup_iterations, args.profiling_iterations
    )
    
    if success and timing_ms is not None:
        print(f"TIMING_MS:{timing_ms:.3f}")
        return 0
    else:
        print("TIMING_MS:0")
        return 1


if __name__ == '__main__':
    sys.exit(main_smat())