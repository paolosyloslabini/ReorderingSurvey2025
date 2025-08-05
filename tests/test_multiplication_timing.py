#!/usr/bin/env python3
"""
Test that multiplication wrappers return internal timing correctly.
"""
import os
import subprocess
import tempfile
from pathlib import Path


def test_mock_multiplication_timing():
    """Test that the mock multiplication wrapper writes internal timing."""
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
        
        # Check that timing file was created
        timing_file = outdir / "timing_ms.txt"
        assert timing_file.exists(), "Timing file was not created"
        
        # Check that timing is a valid number
        timing_ms = float(timing_file.read_text().strip())
        assert timing_ms > 0, f"Invalid timing: {timing_ms}"
        assert timing_ms < 300, f"Timing too large (expected ~100-200ms): {timing_ms}"


def test_cucsrspmm_multiplication_timing():
    """Test that the cucsrspmm multiplication wrapper writes internal timing."""
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
        
        # Check that timing file was created
        timing_file = outdir / "timing_ms.txt"
        assert timing_file.exists(), "Timing file was not created"
        
        # Check that timing is a valid number
        timing_ms = float(timing_file.read_text().strip())
        assert timing_ms > 0, f"Invalid timing: {timing_ms}"


if __name__ == "__main__":
    test_mock_multiplication_timing()
    test_cucsrspmm_multiplication_timing()
    print("All multiplication timing tests passed!")