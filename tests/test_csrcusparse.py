#!/usr/bin/env python3
"""
Test the new csrcusparse implementation.
"""
import os
import subprocess
import tempfile
from pathlib import Path


def test_csrcusparse_script_functionality():
    """Test that the csrcusparse script works properly."""
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
        script_path = Path(__file__).parent.parent / "scripts" / "csrcusparse_multiply.py"
        
        # Test basic functionality
        result = subprocess.run(
            ["python3", str(script_path), matrix_path, "--alpha", "1.5", "--beta", "0.5"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert "TIMING_MS:" in result.stdout, f"No timing in output: {result.stdout}"
        
        # Check that GPU environment detection occurs (should be in stderr)
        assert "GPU Environment:" in result.stderr, f"No GPU detection in stderr: {result.stderr}"
        assert "CSR cuSPARSE implementation starting" in result.stderr, f"No CSR cuSPARSE message: {result.stderr}"
        
        # Extract timing value
        timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
        timing_ms = float(timing_line.split(':')[1])
        assert timing_ms > 0, f"Invalid timing: {timing_ms}"
        
        # Test forced CPU mode
        result_cpu = subprocess.run(
            ["python3", str(script_path), matrix_path, "--force-cpu"],
            capture_output=True,
            text=True
        )
        
        assert result_cpu.returncode == 0, f"Forced CPU mode failed: {result_cpu.stderr}"
        assert "TIMING_MS:" in result_cpu.stdout, f"No timing in CPU mode: {result_cpu.stdout}"
        assert "Using CPU CSR sparse matrix multiplication" in result_cpu.stderr
        
    finally:
        os.unlink(matrix_path)


def test_csrcusparse_wrapper_with_parameters():
    """Test the csrcusparse wrapper with various parameters."""
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
        
        wrapper_path = Path(__file__).parent.parent / "Programs" / "Multiplication" / "Techniques" / "operation_csrcusparse.sh"
        
        env = os.environ.copy()
        env["PROJECT_ROOT"] = str(Path(__file__).parent.parent)
        
        # Test with different parameter combinations
        test_cases = [
            ["alpha=1.0", "beta=0.0"],
            ["alpha=2.5", "beta=1.5"],
            ["alpha=0.5", "beta=0.0", "force_cpu=true"],
        ]
        
        for params in test_cases:
            result = subprocess.run(
                ["bash", str(wrapper_path), str(outdir)] + params,
                env=env,
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0, f"Wrapper failed with params {params}: {result.stderr}"
            assert "TIMING_MS:" in result.stdout, f"No timing with params {params}: {result.stdout}"
            
            # Extract and validate timing
            timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
            timing_ms = float(timing_line.split(':')[1])
            assert timing_ms > 0, f"Invalid timing with params {params}: {timing_ms}"


def test_csrcusparse_error_handling():
    """Test error handling in csrcusparse wrapper."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        outdir = Path(tmp_dir) / "output"
        outdir.mkdir()
        
        # Test without reordered.mtx file
        wrapper_path = Path(__file__).parent.parent / "Programs" / "Multiplication" / "Techniques" / "operation_csrcusparse.sh"
        
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


if __name__ == "__main__":
    test_csrcusparse_script_functionality()
    test_csrcusparse_wrapper_with_parameters()
    test_csrcusparse_error_handling()
    print("All csrcusparse tests passed!")