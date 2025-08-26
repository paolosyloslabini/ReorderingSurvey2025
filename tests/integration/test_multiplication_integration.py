"""
Integration tests for multiplication with module loading.

Tests that multiplication kernels work correctly with the module loading system.
"""
import pytest
from pathlib import Path
from tests.utils.fixtures import (
    create_test_matrix, setup_test_environment, run_reordering_test, run_multiplication_test,
    validate_reordering_output, validate_multiplication_output, get_test_matrices
)


def setup_complete_pipeline_test(tmp_path, matrix_key: str, dataset: str, matrix_name: str):
    """Helper function to set up complete pipeline test with proper matrix placement."""
    matrices = get_test_matrices()
    matrix_path = create_test_matrix(tmp_path, matrices[matrix_key], dataset, matrix_name)
    test_env = setup_test_environment(tmp_path)
    
    # Copy matrix to Raw_Matrices for multiplication stage to find
    raw_matrices_dir = Path("Raw_Matrices") / dataset
    raw_matrices_dir.mkdir(parents=True, exist_ok=True)
    raw_matrix_path = raw_matrices_dir / f"{matrix_name}.mtx"
    raw_matrix_path.write_text(matrices[matrix_key])
    
    return matrix_path, test_env, raw_matrix_path


def cleanup_pipeline_test(raw_matrix_path: Path):
    """Helper function to clean up pipeline test."""
    if raw_matrix_path.exists():
        raw_matrix_path.unlink()
        try:
            raw_matrix_path.parent.rmdir()
        except OSError:
            pass  # Directory not empty


class TestMultiplicationModuleIntegration:
    """Test suite for multiplication kernels with module loading."""
    
    def test_mock_multiplication_with_basic_modules(self, tmp_path):
        """Test mock multiplication with basic module set."""
        matrix_path, test_env, raw_matrix_path = setup_complete_pipeline_test(
            tmp_path, "identity_4x4", "dataset", "matrix"
        )
        
        try:
            # Run reordering first
            reorder_result = run_reordering_test(matrix_path, "identity", test_env["env"])
            assert reorder_result.returncode == 0, f"Reordering failed: {reorder_result.stderr}"
            
            # Get reordering output
            reorder_output = validate_reordering_output(test_env["results_dir"], "matrix", "identity")
            results_csv = reorder_output["csv_file"]
            
            # Run multiplication
            mult_result = run_multiplication_test(results_csv, "mock", test_env["env"])
            assert mult_result.returncode == 0, f"Mock multiplication failed: {mult_result.stderr}"
            
            # Verify module loading messages
            assert "Loading module set: basic for technique mock" in mult_result.stderr
            assert "Module loading completed for multiply/mock" in mult_result.stderr
            
            # Verify internal timing was used
            assert "Using internal timing:" in mult_result.stderr
            
            # Verify output files
            mult_output = validate_multiplication_output(test_env["results_dir"], "matrix", "identity", "mock")
            
            # Verify CSV contains both reordering and multiplication data
            csv_data = mult_output["csv_data"]
            assert csv_data["matrix_name"] == "matrix"
            assert csv_data["reorder_tech"] == "identity"
            assert csv_data["mult_type"] == "mock"
            assert csv_data["exit_code"] == 0
            assert "mult_time_ms" in csv_data
            assert csv_data["mult_time_ms"] > 0
            
        finally:
            cleanup_pipeline_test(raw_matrix_path)
    
    def test_cusparse_multiplication_with_cuda_modules(self, tmp_path):
        """Test cuSPARSE multiplication with CUDA module set (fails without GPU)."""
        # First create a reordered matrix through the reordering pipeline
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["connected_5x5"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        # Run reordering first
        reorder_result = run_reordering_test(matrix_path, "rcm", test_env["env"])
        assert reorder_result.returncode == 0, f"Reordering failed: {reorder_result.stderr}"
        
        # Get reordering output
        reorder_output = validate_reordering_output(test_env["results_dir"], "matrix", "rcm")
        results_csv = reorder_output["csv_file"]
        
        # Run multiplication - should fail without GPU (no CPU fallback)
        mult_result = run_multiplication_test(results_csv, "cucsrspmm", test_env["env"])
        
        # Verify module loading messages
        assert "Loading module set: cuda_cusparse for technique cucsrspmm" in mult_result.stderr
        assert "Module loading completed for multiply/cucsrspmm" in mult_result.stderr
        
        # cuSPARSE should either succeed with GPU or fail without it (no CPU fallback)
        if mult_result.returncode == 0:
            # GPU available - should succeed
            assert "TIMING_MS:" in mult_result.stdout
            # Verify GPU environment detection
            assert "GPU Environment:" in mult_result.stderr
        else:
            # No GPU available - should fail (expected behavior)
            assert mult_result.returncode == 1, "Should fail without GPU"
            # Verify it properly indicates GPU failure
            assert "GPU not available" in mult_result.stderr or "CUDA not available" in mult_result.stderr
    
    def test_multiplication_with_parameters(self, tmp_path):
        """Test multiplication with parameter sets."""
        # Create reordered matrix
        matrix_path, test_env, raw_matrix_path = setup_complete_pipeline_test(
            tmp_path, "identity_4x4", "dataset", "matrix"
        )
        
        try:
            # Run reordering first
            reorder_result = run_reordering_test(matrix_path, "identity", test_env["env"])
            assert reorder_result.returncode == 0, f"Reordering failed: {reorder_result.stderr}"
            
            # Get reordering output
            reorder_output = validate_reordering_output(test_env["results_dir"], "matrix", "identity")
            results_csv = reorder_output["csv_file"]
            
            # Test different parameter combinations
            param_tests = [
                ["alpha=2.0"],
                ["alpha=1.5", "beta=0.5"],
            ]
            
            for params in param_tests:
                mult_result = run_multiplication_test(results_csv, "mock", test_env["env"], params)
                assert mult_result.returncode == 0, f"Mock multiplication with params {params} failed: {mult_result.stderr}"
                
                # Should complete successfully with any parameters
                assert "Module loading completed for multiply/mock" in mult_result.stderr
        finally:
            cleanup_pipeline_test(raw_matrix_path)
    
    def test_multiplication_error_handling(self, tmp_path):
        """Test multiplication error handling."""
        test_env = setup_test_environment(tmp_path)
        
        # Create a fake/invalid results CSV
        fake_csv = test_env["tmp_path"] / "fake_results.csv"
        fake_csv.write_text("invalid,csv,content\n")
        
        # Try to run multiplication with invalid input
        mult_result = run_multiplication_test(fake_csv, "mock", test_env["env"])
        
        # Should handle error gracefully (exact behavior depends on implementation)
        # At minimum, should not crash the system
        assert mult_result.returncode != 0 or "error" in mult_result.stderr.lower()


class TestReorderingMultiplicationPipeline:
    """Test suite for complete reordering → multiplication pipeline."""
    
    def test_complete_pipeline_identity_mock(self, tmp_path):
        """Test complete pipeline: identity reordering → mock multiplication."""
        matrix_path, test_env, raw_matrix_path = setup_complete_pipeline_test(
            tmp_path, "identity_4x4", "dataset", "matrix"
        )
        
        try:
            # Step 1: Reordering
            reorder_result = run_reordering_test(matrix_path, "identity", test_env["env"])
            assert reorder_result.returncode == 0, f"Reordering failed: {reorder_result.stderr}"
            
            reorder_output = validate_reordering_output(test_env["results_dir"], "matrix", "identity")
            assert reorder_output["permutation"] == [1, 2, 3, 4]  # Identity permutation
            
            # Step 2: Multiplication
            mult_result = run_multiplication_test(reorder_output["csv_file"], "mock", test_env["env"])
            assert mult_result.returncode == 0, f"Multiplication failed: {mult_result.stderr}"
            
            mult_output = validate_multiplication_output(test_env["results_dir"], "matrix", "identity", "mock")
            
            # Verify complete pipeline data
            csv_data = mult_output["csv_data"]
            assert csv_data["matrix_name"] == "matrix"
            assert csv_data["dataset"] == "dataset"
            assert csv_data["n_rows"] == 4
            assert csv_data["n_cols"] == 4
            assert csv_data["nnz"] == 4
            assert csv_data["reorder_tech"] == "identity"
            assert csv_data["mult_type"] == "mock"
            assert csv_data["exit_code"] == 0
            assert csv_data["reorder_time_ms"] >= 0
            assert csv_data["mult_time_ms"] > 0
        finally:
            cleanup_pipeline_test(raw_matrix_path)
    
    def test_complete_pipeline_rcm_cusparse(self, tmp_path):
        """Test complete pipeline: RCM reordering → cuSPARSE multiplication."""
        matrix_path, test_env, raw_matrix_path = setup_complete_pipeline_test(
            tmp_path, "connected_5x5", "dataset", "matrix"
        )
        
        try:
            # Step 1: Reordering
            reorder_result = run_reordering_test(matrix_path, "rcm", test_env["env"])
            assert reorder_result.returncode == 0, f"RCM reordering failed: {reorder_result.stderr}"
            
            reorder_output = validate_reordering_output(test_env["results_dir"], "matrix", "rcm")
            assert len(reorder_output["permutation"]) == 5  # Valid permutation
            
            # Step 2: Multiplication
            mult_result = run_multiplication_test(reorder_output["csv_file"], "cucsrspmm", test_env["env"])
            assert mult_result.returncode == 0, f"cuSPARSE multiplication failed: {mult_result.stderr}"
            
            mult_output = validate_multiplication_output(test_env["results_dir"], "matrix", "rcm", "cucsrspmm")
            
            # Verify complete pipeline data
            csv_data = mult_output["csv_data"]
            assert csv_data["matrix_name"] == "matrix"
            assert csv_data["dataset"] == "dataset"
            assert csv_data["n_rows"] == 5
            assert csv_data["n_cols"] == 5
            assert csv_data["nnz"] == 13
            assert csv_data["reorder_tech"] == "rcm"
            assert csv_data["mult_type"] == "cucsrspmm"
            assert csv_data["exit_code"] == 0
            assert csv_data["reorder_time_ms"] >= 0
            assert csv_data["mult_time_ms"] > 0
        finally:
            cleanup_pipeline_test(raw_matrix_path)
    
    def test_multiple_matrices_same_pipeline(self, tmp_path):
        """Test same pipeline on multiple matrices."""
        test_matrices = [
            ("identity_4x4", "small_matrix", 4),
            ("connected_5x5", "medium_matrix", 5),
        ]
        
        for matrix_content_key, matrix_name, size in test_matrices:
            matrix_path, test_env, raw_matrix_path = setup_complete_pipeline_test(
                tmp_path, matrix_content_key, "dataset", matrix_name
            )
            
            try:
                # Reordering
                reorder_result = run_reordering_test(matrix_path, "identity", test_env["env"])
                assert reorder_result.returncode == 0, f"Reordering {matrix_name} failed: {reorder_result.stderr}"
                
                reorder_output = validate_reordering_output(test_env["results_dir"], matrix_name, "identity")
                assert len(reorder_output["permutation"]) == size
                
                # Multiplication
                mult_result = run_multiplication_test(reorder_output["csv_file"], "mock", test_env["env"])
                assert mult_result.returncode == 0, f"Multiplication {matrix_name} failed: {mult_result.stderr}"
                
                mult_output = validate_multiplication_output(test_env["results_dir"], matrix_name, "identity", "mock")
                
                # Verify results
                csv_data = mult_output["csv_data"]
                assert csv_data["matrix_name"] == matrix_name
                assert csv_data["n_rows"] == size
                assert csv_data["n_cols"] == size
                assert csv_data["exit_code"] == 0
            finally:
                cleanup_pipeline_test(raw_matrix_path)
    
    def test_pipeline_with_parameters(self, tmp_path):
        """Test complete pipeline with parameter sets."""
        matrix_path, test_env, raw_matrix_path = setup_complete_pipeline_test(
            tmp_path, "connected_5x5", "dataset", "matrix"
        )
        
        try:
            # Reordering with parameters
            reorder_result = run_reordering_test(matrix_path, "rcm", test_env["env"], ["symmetric=true"])
            assert reorder_result.returncode == 0, f"RCM reordering with params failed: {reorder_result.stderr}"
            
            reorder_output = validate_reordering_output(test_env["results_dir"], "matrix", "rcm", "symmetric-true")
            assert reorder_output["csv_data"]["reord_param_set"] == "symmetric=true"
            
            # Multiplication with parameters
            mult_result = run_multiplication_test(reorder_output["csv_file"], "mock", test_env["env"], ["alpha=2.5"])
            assert mult_result.returncode == 0, f"Mock multiplication with params failed: {mult_result.stderr}"
            
            mult_output = validate_multiplication_output(test_env["results_dir"], "matrix", "rcm", "mock", "symmetric-true")
            csv_data = mult_output["csv_data"]
            
            # Verify parameter propagation
            assert csv_data["reord_param_set"] == "symmetric=true"
            assert csv_data["mult_type"] == "mock"
            assert csv_data["exit_code"] == 0
        finally:
            cleanup_pipeline_test(raw_matrix_path)


class TestTimingIntegration:
    """Test suite for timing integration across pipeline."""
    
    def test_timing_consistency(self, tmp_path):
        """Test that timing data is consistent across pipeline stages."""
        matrix_path, test_env, raw_matrix_path = setup_complete_pipeline_test(
            tmp_path, "identity_4x4", "dataset", "matrix"
        )
        
        try:
            # Complete pipeline
            reorder_result = run_reordering_test(matrix_path, "identity", test_env["env"])
            assert reorder_result.returncode == 0
            
            reorder_output = validate_reordering_output(test_env["results_dir"], "matrix", "identity")
            
            mult_result = run_multiplication_test(reorder_output["csv_file"], "mock", test_env["env"])
            assert mult_result.returncode == 0
            
            mult_output = validate_multiplication_output(test_env["results_dir"], "matrix", "identity", "mock")
            
            # Verify timing data
            csv_data = mult_output["csv_data"]
            
            # Both reordering and multiplication timing should be present and positive
            assert csv_data["reorder_time_ms"] >= 0, "Reordering time should be non-negative"
            assert csv_data["mult_time_ms"] > 0, "Multiplication time should be positive"
            
            # Timing should be reasonable (not extremely large)
            assert csv_data["reorder_time_ms"] < 10000, "Reordering time seems too large"
            assert csv_data["mult_time_ms"] < 1000, "Multiplication time seems too large"
        finally:
            cleanup_pipeline_test(raw_matrix_path)
    
    def test_internal_timing_integration(self, tmp_path):
        """Test that internal timing is properly integrated into results."""
        matrix_path, test_env, raw_matrix_path = setup_complete_pipeline_test(
            tmp_path, "identity_4x4", "dataset", "matrix"
        )
        
        try:
            # Complete pipeline
            reorder_result = run_reordering_test(matrix_path, "identity", test_env["env"])
            assert reorder_result.returncode == 0
            
            reorder_output = validate_reordering_output(test_env["results_dir"], "matrix", "identity")
            
            mult_result = run_multiplication_test(reorder_output["csv_file"], "mock", test_env["env"])
            assert mult_result.returncode == 0
            
            # Verify internal timing was detected and used
            assert "Using internal timing:" in mult_result.stderr, "Internal timing should be detected and used"
            
            # Verify timing value is in reasonable range for mock kernel
            mult_output = validate_multiplication_output(test_env["results_dir"], "matrix", "identity", "mock")
            mult_time = mult_output["csv_data"]["mult_time_ms"]
            
            # Mock kernel should take 100-200ms based on its implementation
            assert 50 < mult_time < 300, f"Mock timing should be ~100-200ms, got {mult_time}ms"
        finally:
            cleanup_pipeline_test(raw_matrix_path)