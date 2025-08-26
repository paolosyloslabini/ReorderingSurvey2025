#!/usr/bin/env python3
"""
Test the new unified cuSPARSE implementations.
Tests all cuSPARSE operations: CSR/BSR SpMV/SpMM with no CPU fallback.
"""
import os
import subprocess
import tempfile
from pathlib import Path


def test_cucsrspmv_script_functionality():
    """Test that the cucsrspmv script works properly and fails without GPU."""
    # Create a test matrix
    test_matrix = """%%MatrixMarket matrix coordinate real general
5 5 5
1 1 1
2 2 1
3 3 1
4 4 1
5 5 1
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mtx', delete=False) as f:
        f.write(test_matrix)
        matrix_path = f.name
    
    try:
        script_path = Path(__file__).parent.parent / "scripts" / "cucsrspmv.py"
        
        # Test basic functionality - should fail without GPU
        result = subprocess.run(
            ["python3", str(script_path), matrix_path, "--alpha", "1.5", "--beta", "0.5"],
            capture_output=True,
            text=True
        )
        
        # Check that GPU environment detection occurs (should be in stderr)
        assert "GPU Environment:" in result.stderr, f"No GPU detection in stderr: {result.stderr}"
        assert "Performing CSR SpMV" in result.stderr or "cuSPARSE/GPU environment not available" in result.stderr
        
        # Should either succeed with GPU or fail without it - no CPU fallback
        if result.returncode == 0:
            assert "TIMING_MS:" in result.stdout, f"No timing in output: {result.stdout}"
            timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
            timing_ms = float(timing_line.split(':')[1])
            assert timing_ms > 0, f"Invalid timing: {timing_ms}"
        else:
            # Should fail fast without GPU - no CPU fallback
            assert result.returncode == 1, "Should fail without GPU"
            assert "TIMING_MS:0" in result.stdout, "Should output zero timing on GPU failure"
            assert "cuSPARSE/GPU environment not available" in result.stderr
        
    finally:
        os.unlink(matrix_path)


def test_cucsrspmm_script_functionality():
    """Test that the cucsrspmm script works properly and fails without GPU."""
    # Create a test matrix
    test_matrix = """%%MatrixMarket matrix coordinate real general
5 5 5
1 1 1
2 2 1
3 3 1
4 4 1
5 5 1
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mtx', delete=False) as f:
        f.write(test_matrix)
        matrix_path = f.name
    
    try:
        script_path = Path(__file__).parent.parent / "scripts" / "cucsrspmm.py"
        
        # Test basic functionality - should fail without GPU
        result = subprocess.run(
            ["python3", str(script_path), matrix_path, "--alpha", "2.0", "--beta", "1.0"],
            capture_output=True,
            text=True
        )
        
        # Check that GPU environment detection occurs (should be in stderr)
        assert "GPU Environment:" in result.stderr, f"No GPU detection in stderr: {result.stderr}"
        assert "Performing CSR SpMM" in result.stderr or "cuSPARSE/GPU environment not available" in result.stderr
        
        # Should either succeed with GPU or fail without it - no CPU fallback
        if result.returncode == 0:
            assert "TIMING_MS:" in result.stdout, f"No timing in output: {result.stdout}"
            timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
            timing_ms = float(timing_line.split(':')[1])
            assert timing_ms > 0, f"Invalid timing: {timing_ms}"
        else:
            # Should fail fast without GPU - no CPU fallback
            assert result.returncode == 1, "Should fail without GPU"
            assert "TIMING_MS:0" in result.stdout, "Should output zero timing on GPU failure"
            assert "cuSPARSE/GPU environment not available" in result.stderr
        
    finally:
        os.unlink(matrix_path)


def test_cucsrspmv_wrapper_with_parameters():
    """Test the cucsrspmv wrapper with various parameters."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        outdir = Path(tmp_dir) / "output"
        outdir.mkdir()
        
        # Create a reordered matrix file
        reordered_mtx = outdir / "reordered.mtx"
        reordered_mtx.write_text("""%%MatrixMarket matrix coordinate real general
6 6 8
1 1 2.0
1 2 1.0
2 2 3.0
3 3 4.0
4 4 5.0
5 5 6.0
6 6 7.0
2 3 1.5
""")
        
        wrapper_path = Path(__file__).parent.parent / "Programs" / "Multiplication" / "Techniques" / "operation_cucsrspmv.sh"
        
        env = os.environ.copy()
        env["PROJECT_ROOT"] = str(Path(__file__).parent.parent)
        
        # Test with different parameter combinations
        test_cases = [
            ["alpha=1.0", "beta=0.0"],
            ["alpha=2.5", "beta=1.5", "n_iterations=5"],
        ]
        
        for params in test_cases:
            result = subprocess.run(
                ["bash", str(wrapper_path), str(outdir)] + params,
                env=env,
                capture_output=True,
                text=True
            )
            
            # Should either succeed with GPU or fail without it
            if result.returncode == 0:
                assert "TIMING_MS:" in result.stdout, f"No timing with params {params}: {result.stdout}"
                timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
                timing_ms = float(timing_line.split(':')[1])
                assert timing_ms > 0, f"Invalid timing with params {params}: {timing_ms}"
            else:
                # Should fail without GPU - no CPU fallback
                assert result.returncode == 1, f"Should fail without GPU for params {params}"
                assert "TIMING_MS:0" in result.stdout, f"Should output zero timing for params {params}"


def test_cucbrspmv_wrapper_functionality():
    """Test the cucbrspmv wrapper functionality."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        outdir = Path(tmp_dir) / "output"
        outdir.mkdir()
        
        # Create a reordered matrix file suitable for BSR
        reordered_mtx = outdir / "reordered.mtx"
        reordered_mtx.write_text("""%%MatrixMarket matrix coordinate real general
8 8 16
1 1 2.0
1 2 1.0
2 1 1.0
2 2 3.0
3 3 4.0
3 4 2.0
4 3 2.0
4 4 5.0
5 5 6.0
5 6 3.0
6 5 3.0
6 6 7.0
7 7 8.0
7 8 4.0
8 7 4.0
8 8 9.0
""")
        
        wrapper_path = Path(__file__).parent.parent / "Programs" / "Multiplication" / "Techniques" / "operation_cucbrspmv.sh"
        
        env = os.environ.copy()
        env["PROJECT_ROOT"] = str(Path(__file__).parent.parent)
        
        # Test BSR SpMV with block size parameters
        result = subprocess.run(
            ["bash", str(wrapper_path), str(outdir), "alpha=1.0", "beta=0.0", "block_size=4"],
            env=env,
            capture_output=True,
            text=True
        )
        
        # Should either succeed with GPU or fail without it
        if result.returncode == 0:
            assert "TIMING_MS:" in result.stdout, f"No timing in output: {result.stdout}"
        else:
            # Should fail without GPU - no CPU fallback
            assert result.returncode == 1, "Should fail without GPU"
            assert "TIMING_MS:0" in result.stdout, "Should output zero timing on GPU failure"


def test_cusparse_operations_error_handling():
    """Test error handling in cuSPARSE wrappers."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        outdir = Path(tmp_dir) / "output"
        outdir.mkdir()
        
        # Test without reordered.mtx file
        wrapper_path = Path(__file__).parent.parent / "Programs" / "Multiplication" / "Techniques" / "operation_cucsrspmv.sh"
        
        env = os.environ.copy()
        env["PROJECT_ROOT"] = str(Path(__file__).parent.parent)
        
        result = subprocess.run(
            ["bash", str(wrapper_path), str(outdir), "alpha=1.0"],
            env=env,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1, "Should fail when reordered.mtx is missing"
        assert "TIMING_MS:0" in result.stdout, "Should output zero timing on error"
        assert "Reordered matrix not found" in result.stderr


def test_unified_cusparse_operations_script():
    """Test the unified cuSPARSE operations script."""
    # Create a test matrix
    test_matrix = """%%MatrixMarket matrix coordinate real general
4 4 4
1 1 1
2 2 1
3 3 1
4 4 1
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mtx', delete=False) as f:
        f.write(test_matrix)
        matrix_path = f.name
    
    try:
        script_path = Path(__file__).parent.parent / "scripts" / "cusparse_operations.py"
        
        # Test different operations
        operations = ['csr_spmv', 'csr_spmm', 'bsr_spmv', 'bsr_spmm']
        
        for operation in operations:
            result = subprocess.run(
                ["python3", str(script_path), matrix_path, operation, "--alpha", "1.0"],
                capture_output=True,
                text=True
            )
            
            # Check that GPU environment detection occurs
            assert "GPU Environment:" in result.stderr, f"No GPU detection for {operation}: {result.stderr}"
            
            # Should either succeed with GPU or fail without it
            if result.returncode == 0:
                assert "TIMING_MS:" in result.stdout, f"No timing for {operation}: {result.stdout}"
                timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
                timing_ms = float(timing_line.split(':')[1])
                assert timing_ms > 0, f"Invalid timing for {operation}: {timing_ms}"
            else:
                # Should fail without GPU - no CPU fallback
                assert result.returncode == 1, f"Should fail without GPU for {operation}"
                assert "TIMING_MS:0" in result.stdout, f"Should output zero timing for {operation}"
                assert "cuSPARSE/GPU environment not available" in result.stderr
        
    finally:
        os.unlink(matrix_path)


if __name__ == "__main__":
    test_cucsrspmv_script_functionality()
    test_cucsrspmm_script_functionality()
    test_cucsrspmv_wrapper_with_parameters()
    test_cucbrspmv_wrapper_functionality()
    test_cusparse_operations_error_handling()
    test_unified_cusparse_operations_script()
    print("All unified cuSPARSE tests passed!")