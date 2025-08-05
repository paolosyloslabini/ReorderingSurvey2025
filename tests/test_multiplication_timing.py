#!/usr/bin/env python3
"""
Test that multiplication wrappers return internal timing correctly.
"""
import os
import subprocess
import tempfile
from pathlib import Path


def test_mock_multiplication_timing():
    """Test that the mock multiplication wrapper outputs internal timing via stdout."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        outdir = Path(tmp_dir) / "output"
        outdir.mkdir()
        
        # Call the mock wrapper directly
        wrapper_path = Path(__file__).parent.parent / "Programs" / "Multiplication" / "Techniques" / "operation_mock.sh"
        
        env = os.environ.copy()
        env["PROJECT_ROOT"] = str(Path(__file__).parent.parent)
        
        result = subprocess.run(
            ["bash", str(wrapper_path), str(outdir), "alpha=2.0"],
            env=env,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Wrapper failed with: {result.stderr}"
        
        # Check that timing was output via stdout
        assert "TIMING_MS:" in result.stdout, f"No timing found in stdout: {result.stdout}"
        
        # Extract timing from stdout
        timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
        timing_ms = float(timing_line.split(':')[1])
        assert timing_ms > 0, f"Invalid timing: {timing_ms}"
        assert timing_ms < 300, f"Timing too large (expected ~100-200ms): {timing_ms}"


def test_cucsrspmm_multiplication_timing():
    """Test that the cucsrspmm multiplication wrapper outputs internal timing via stdout."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        outdir = Path(tmp_dir) / "output"
        outdir.mkdir()
        
        # Create a dummy reordered matrix
        reordered_mtx = outdir / "reordered.mtx"
        reordered_mtx.write_text("""%%MatrixMarket matrix coordinate real general
4 4 4
1 1 1
2 2 1
3 3 1
4 4 1
""")
        
        # Call the cucsrspmm wrapper directly
        wrapper_path = Path(__file__).parent.parent / "Programs" / "Multiplication" / "Techniques" / "operation_cucsrspmm.sh"
        
        env = os.environ.copy()
        env["PROJECT_ROOT"] = str(Path(__file__).parent.parent)
        
        result = subprocess.run(
            ["bash", str(wrapper_path), str(outdir), "alpha=1.0", "beta=0.0"],
            env=env,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Wrapper failed with: {result.stderr}"
        
        # Check that timing was output via stdout
        assert "TIMING_MS:" in result.stdout, f"No timing found in stdout: {result.stdout}"
        
        # Extract timing from stdout
        timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
        timing_ms = float(timing_line.split(':')[1])
        assert timing_ms > 0, f"Invalid timing: {timing_ms}"


if __name__ == "__main__":
    test_mock_multiplication_timing()
    test_cucsrspmm_multiplication_timing()
    print("All multiplication timing tests passed!")