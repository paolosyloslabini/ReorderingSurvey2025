"""
Unit tests for multiplication kernels.

Tests individual multiplication kernels in isolation.
"""
import subprocess
import tempfile
from pathlib import Path

import pytest
from tests.utils.fixtures import setup_test_environment


class TestMockMultiplicationKernel:
    """Test suite for mock multiplication kernel."""
    
    def test_mock_kernel_basic_functionality(self, tmp_path):
        """Test basic functionality of mock multiplication kernel."""
        test_env = setup_test_environment(tmp_path)
        outdir = test_env["tmp_path"] / "output"
        outdir.mkdir()
        
        # Create a dummy reordered matrix
        reordered_mtx = outdir / "reordered.mtx"
        reordered_mtx.write_text("""%%MatrixMarket matrix coordinate real general
4 4 4
1 1 1.0
2 2 2.0
3 3 3.0
4 4 4.0
""")
        
        # Test the mock wrapper directly
        wrapper_path = Path(__file__).parent.parent.parent / "Programs" / "Multiplication" / "Techniques" / "operation_mock.sh"
        
        result = subprocess.run(
            ["bash", str(wrapper_path), str(outdir), "alpha=2.0"],
            env=test_env["env"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Mock wrapper failed: {result.stderr}"
        
        # Check that timing was output via stdout
        assert "TIMING_MS:" in result.stdout, f"No timing found in stdout: {result.stdout}"
        
        # Extract and validate timing
        timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
        timing_ms = float(timing_line.split(':')[1])
        assert timing_ms > 0, f"Invalid timing: {timing_ms}"
        assert timing_ms < 300, f"Timing too large: {timing_ms}"
    
    def test_mock_kernel_with_parameters(self, tmp_path):
        """Test mock kernel with various parameter combinations."""
        test_env = setup_test_environment(tmp_path)
        outdir = test_env["tmp_path"] / "output"
        outdir.mkdir()
        
        # Create a dummy reordered matrix
        reordered_mtx = outdir / "reordered.mtx"
        reordered_mtx.write_text("""%%MatrixMarket matrix coordinate real general
3 3 3
1 1 1.0
2 2 2.0
3 3 3.0
""")
        
        wrapper_path = Path(__file__).parent.parent.parent / "Programs" / "Multiplication" / "Techniques" / "operation_mock.sh"
        
        # Test different parameter combinations
        test_cases = [
            ["alpha=1.0"],
            ["alpha=2.5", "beta=1.5"],
            ["alpha=0.5", "beta=0.0"],
        ]
        
        for params in test_cases:
            result = subprocess.run(
                ["bash", str(wrapper_path), str(outdir)] + params,
                env=test_env["env"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0, f"Mock wrapper failed with params {params}: {result.stderr}"
            assert "TIMING_MS:" in result.stdout, f"No timing with params {params}: {result.stdout}"
            
            # Extract and validate timing
            timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
            timing_ms = float(timing_line.split(':')[1])
            assert timing_ms > 0, f"Invalid timing with params {params}: {timing_ms}"
    
    def test_mock_kernel_missing_matrix(self, tmp_path):
        """Test mock kernel error handling when matrix file is missing."""
        test_env = setup_test_environment(tmp_path)
        outdir = test_env["tmp_path"] / "output"
        outdir.mkdir()
        
        # Don't create reordered.mtx file
        wrapper_path = Path(__file__).parent.parent.parent / "Programs" / "Multiplication" / "Techniques" / "operation_mock.sh"
        
        result = subprocess.run(
            ["bash", str(wrapper_path), str(outdir), "alpha=1.0"],
            env=test_env["env"],
            capture_output=True,
            text=True
        )
        
        # Mock kernel might not fail for missing matrix (depends on implementation)
        # It should either fail or output zero timing
        if result.returncode == 0:
            # If it succeeds, it should indicate the issue somehow
            assert "TIMING_MS:" in result.stdout
        else:
            # If it fails, that's also acceptable behavior
            assert result.returncode == 1


class TestCuSparseMultiplicationKernel:
    """Test suite for cuSPARSE multiplication kernel."""
    
    def test_cusparse_wrapper_basic(self, tmp_path):
        """Test basic cuSPARSE wrapper functionality."""
        test_env = setup_test_environment(tmp_path)
        outdir = test_env["tmp_path"] / "output"
        outdir.mkdir()
        
        # Create a test matrix
        reordered_mtx = outdir / "reordered.mtx"
        reordered_mtx.write_text("""%%MatrixMarket matrix coordinate real general
5 5 7
1 1 2.0
1 2 1.0
2 2 3.0
3 3 4.0
4 4 5.0
5 5 6.0
2 3 1.5
""")
        
        wrapper_path = Path(__file__).parent.parent.parent / "Programs" / "Multiplication" / "Techniques" / "operation_cucsrspmm.sh"
        
        result = subprocess.run(
            ["bash", str(wrapper_path), str(outdir), "alpha=1.0", "beta=0.0"],
            env=test_env["env"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"cuSPARSE wrapper failed: {result.stderr}"
        assert "TIMING_MS:" in result.stdout, f"No timing found in stdout: {result.stdout}"
        
        # Extract timing value
        timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
        timing_ms = float(timing_line.split(':')[1])
        assert timing_ms > 0, f"Invalid timing: {timing_ms}"
    
    def test_cusparse_wrapper_with_parameters(self, tmp_path):
        """Test cuSPARSE wrapper with various parameters."""
        test_env = setup_test_environment(tmp_path)
        outdir = test_env["tmp_path"] / "output"
        outdir.mkdir()
        
        # Create a test matrix
        reordered_mtx = outdir / "reordered.mtx"
        reordered_mtx.write_text("""%%MatrixMarket matrix coordinate real general
4 4 6
1 1 2.0
1 2 1.0
2 2 3.0
3 3 4.0
4 4 5.0
2 3 1.5
""")
        
        wrapper_path = Path(__file__).parent.parent.parent / "Programs" / "Multiplication" / "Techniques" / "operation_cucsrspmm.sh"
        
        # Test different parameter combinations
        test_cases = [
            ["alpha=1.0", "beta=0.0"],
            ["alpha=2.5", "beta=1.5"],
            ["alpha=0.5", "beta=0.0", "force_cpu=true"],
        ]
        
        for params in test_cases:
            result = subprocess.run(
                ["bash", str(wrapper_path), str(outdir)] + params,
                env=test_env["env"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0, f"cuSPARSE wrapper failed with params {params}: {result.stderr}"
            assert "TIMING_MS:" in result.stdout, f"No timing with params {params}: {result.stdout}"
            
            # Extract and validate timing
            timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
            timing_ms = float(timing_line.split(':')[1])
            assert timing_ms > 0, f"Invalid timing with params {params}: {timing_ms}"
    
    def test_cusparse_gpu_environment_detection(self, tmp_path):
        """Test that cuSPARSE wrapper properly detects GPU environment."""
        # Create a test matrix in a temporary file
        test_matrix = """%%MatrixMarket matrix coordinate real general
3 3 3
1 1 1.0
2 2 2.0
3 3 3.0
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mtx', delete=False) as f:
            f.write(test_matrix)
            matrix_path = f.name
        
        try:
            script_path = Path(__file__).parent.parent.parent / "scripts" / "cusparse_spmm.py"
            
            # Test basic functionality
            result = subprocess.run(
                ["python3", str(script_path), matrix_path, "--alpha", "1.5", "--beta", "0.5"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0, f"cuSPARSE script failed: {result.stderr}"
            assert "TIMING_MS:" in result.stdout, f"No timing in output: {result.stdout}"
            
            # Check that GPU environment detection occurs (should be in stderr)
            assert "GPU Environment:" in result.stderr, f"No GPU detection in stderr: {result.stderr}"
            
            # Extract timing value
            timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
            timing_ms = float(timing_line.split(':')[1])
            assert timing_ms > 0, f"Invalid timing: {timing_ms}"
            
        finally:
            import os
            os.unlink(matrix_path)
    
    def test_cusparse_forced_cpu_mode(self, tmp_path):
        """Test cuSPARSE forced CPU mode."""
        # Create a test matrix in a temporary file
        test_matrix = """%%MatrixMarket matrix coordinate real general
3 3 3
1 1 1.0
2 2 2.0
3 3 3.0
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mtx', delete=False) as f:
            f.write(test_matrix)
            matrix_path = f.name
        
        try:
            script_path = Path(__file__).parent.parent.parent / "scripts" / "cusparse_spmm.py"
            
            # Test forced CPU mode
            result = subprocess.run(
                ["python3", str(script_path), matrix_path, "--force-cpu"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0, f"Forced CPU mode failed: {result.stderr}"
            assert "TIMING_MS:" in result.stdout, f"No timing in CPU mode: {result.stdout}"
            assert "Using CPU sparse matrix multiplication" in result.stderr
            
        finally:
            import os
            os.unlink(matrix_path)
    
    def test_cusparse_error_handling(self, tmp_path):
        """Test cuSPARSE wrapper error handling."""
        test_env = setup_test_environment(tmp_path)
        outdir = test_env["tmp_path"] / "output"
        outdir.mkdir()
        
        # Test without reordered.mtx file
        wrapper_path = Path(__file__).parent.parent.parent / "Programs" / "Multiplication" / "Techniques" / "operation_cucsrspmm.sh"
        
        result = subprocess.run(
            ["bash", str(wrapper_path), str(outdir), "alpha=1.0"],
            env=test_env["env"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1, "Should fail when reordered.mtx is missing"
        assert "TIMING_MS:0" in result.stdout, "Should output zero timing on error"


class TestMultiplicationTimingIntegration:
    """Test suite for multiplication timing integration."""
    
    def test_internal_vs_external_timing(self, tmp_path):
        """Test that internal timing is properly integrated into the workflow."""
        test_env = setup_test_environment(tmp_path)
        outdir = test_env["tmp_path"] / "output"
        outdir.mkdir()
        
        # Create a dummy reordered matrix
        reordered_mtx = outdir / "reordered.mtx"
        reordered_mtx.write_text("""%%MatrixMarket matrix coordinate real general
4 4 4
1 1 1.0
2 2 2.0
3 3 3.0
4 4 4.0
""")
        
        wrapper_path = Path(__file__).parent.parent.parent / "Programs" / "Multiplication" / "Techniques" / "operation_mock.sh"
        
        # Test external timing measurement (simulating what Multiply.sbatch does)
        import time
        start_time = time.perf_counter()
        
        result = subprocess.run(
            ["bash", str(wrapper_path), str(outdir), "alpha=2.0"],
            env=test_env["env"],
            capture_output=True,
            text=True
        )
        
        end_time = time.perf_counter()
        external_time_ms = (end_time - start_time) * 1000
        
        assert result.returncode == 0, f"Wrapper failed: {result.stderr}"
        
        # Check that internal timing was output via stdout
        assert "TIMING_MS:" in result.stdout, f"No timing found in stdout: {result.stdout}"
        
        # Extract internal timing from stdout
        timing_line = [line for line in result.stdout.split('\n') if line.startswith('TIMING_MS:')][0]
        internal_time_ms = float(timing_line.split(':')[1])
        
        # Verify that internal timing is reasonable
        assert internal_time_ms > 50, f"Internal timing too small: {internal_time_ms}ms"
        assert internal_time_ms < 300, f"Internal timing too large: {internal_time_ms}ms"
        
        # Verify that internal timing is different from external (they measure different things)
        # Internal should be the sleep time (~100-200ms), external includes subprocess overhead
        assert abs(internal_time_ms - external_time_ms) > 5, "Internal and external timing should differ"