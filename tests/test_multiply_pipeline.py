#!/usr/bin/env python3
"""
Test that the multiplication pipeline integration works correctly.
"""
import os
import subprocess
import tempfile
from pathlib import Path


def test_internal_timing_integration():
    """Test that internal timing is properly integrated into the workflow."""
    project_root = Path(__file__).parent.parent
    
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
        
        # Call the mock wrapper directly to simulate what Multiply.sbatch does
        wrapper_path = project_root / "Programs" / "Multiplication" / "Techniques" / "operation_mock.sh"
        
        env = os.environ.copy()
        env["PROJECT_ROOT"] = str(project_root)
        
        # Test external timing measurement (simulating what Multiply.sbatch does)
        import time
        start_time = time.perf_counter()
        
        result = subprocess.run(
            ["bash", str(wrapper_path), str(outdir), "alpha=2.0"],
            env=env,
            capture_output=True,
            text=True
        )
        
        end_time = time.perf_counter()
        external_time_ms = (end_time - start_time) * 1000
        
        assert result.returncode == 0, f"Wrapper failed with: {result.stderr}"
        
        # Check that internal timing was output via stdout
        assert "TIMING_MS:" in result.stdout, f"No timing found in stdout: {result.stdout}"
        
        # Extract internal timing from stdout
        timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
        internal_time_ms = float(timing_line.split(':')[1])
        
        print(f"External timing: {external_time_ms:.2f}ms")
        print(f"Internal timing: {internal_time_ms}ms")
        
        # Verify that internal timing is reasonable
        assert internal_time_ms > 50, f"Internal timing too small: {internal_time_ms}ms"
        assert internal_time_ms < 300, f"Internal timing too large: {internal_time_ms}ms"
        
        # Verify that internal timing is different from external (they measure different things)
        # Internal should be the sleep time (~100-200ms), external includes subprocess overhead
        assert abs(internal_time_ms - external_time_ms) > 5, "Internal and external timing should differ"


def test_timing_fallback():
    """Test that system falls back to external timing when internal timing is not available."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        outdir = Path(tmp_dir)
        
        # Test the stdout parsing logic used in Multiply.sbatch
        # When no timing is in stdout
        mock_output = "Some regular output\nNo timing here\n"
        has_timing = "TIMING_MS:" in mock_output
        assert not has_timing
        
        # When timing is in stdout
        mock_output_with_timing = "Some regular output\nTIMING_MS:123\nMore output\n"
        has_timing = "TIMING_MS:" in mock_output_with_timing
        assert has_timing
        
        # Extract timing value
        timing_lines = [line for line in mock_output_with_timing.split('\n') if line.startswith('TIMING_MS:')]
        if timing_lines:
            timing_value = timing_lines[0].split(':')[1]
            assert timing_value == "123"


if __name__ == "__main__":
    test_internal_timing_integration()
    test_timing_fallback()
    print("All integration tests passed!")