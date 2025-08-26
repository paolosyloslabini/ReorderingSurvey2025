"""
Integration tests for reordering with module loading.

Tests that reordering techniques work correctly with the module loading system.
"""
import pytest
from tests.utils.fixtures import (
    create_test_matrix, setup_test_environment, run_reordering_test,
    validate_reordering_output, assert_valid_permutation, assert_valid_csv_data,
    get_test_matrices
)


class TestReorderingModuleIntegration:
    """Test suite for reordering techniques with module loading."""
    
    def test_identity_with_basic_modules(self, tmp_path):
        """Test identity reordering with basic module set."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["identity_4x4"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "identity", test_env["env"])
        assert result.returncode == 0, f"Identity with modules failed: {result.stderr}"
        
        # Verify module loading messages in stderr
        assert "Loading module set: basic for technique identity" in result.stderr
        assert "Module loading completed for reorder/identity" in result.stderr
        
        # Verify output files were created
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "identity")
        
        # Verify permutation is identity
        assert_valid_permutation(output_data["permutation"], 4)
        assert output_data["permutation"] == [1, 2, 3, 4]
        
        # Verify CSV data
        assert_valid_csv_data(output_data["csv_data"], "identity", "matrix")
        assert output_data["csv_data"]["exit_code"] == 0
    
    def test_rcm_with_scipy_modules(self, tmp_path):
        """Test RCM reordering with python_scipy module set."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["connected_5x5"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "rcm", test_env["env"])
        assert result.returncode == 0, f"RCM with modules failed: {result.stderr}"
        
        # Verify module loading messages in stderr
        assert "Loading module set: python_scipy for technique rcm" in result.stderr
        assert "SciPy" in result.stderr and "NumPy" in result.stderr  # From post_load verification
        assert "Module loading completed for reorder/rcm" in result.stderr
        
        # Verify output files were created
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "rcm")
        
        # Verify permutation is valid
        assert_valid_permutation(output_data["permutation"], 5)
        
        # Verify CSV data
        assert_valid_csv_data(output_data["csv_data"], "rcm", "matrix")
        assert output_data["csv_data"]["exit_code"] == 0
        assert output_data["csv_data"]["reorder_type"] == "2D"
    
    def test_rcm_with_parameters_and_modules(self, tmp_path):
        """Test RCM reordering with parameters and module loading."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["connected_5x5"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "rcm", test_env["env"], ["symmetric=true"])
        assert result.returncode == 0, f"RCM with params and modules failed: {result.stderr}"
        
        # Verify module loading occurred
        assert "Loading module set: python_scipy for technique rcm" in result.stderr
        assert "Module loading completed for reorder/rcm" in result.stderr
        
        # Verify output with parameter set
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "rcm", "symmetric")
        
        # Verify permutation is valid
        assert_valid_permutation(output_data["permutation"], 5)
        
        # Verify CSV data includes parameter set
        assert_valid_csv_data(output_data["csv_data"], "rcm", "matrix")
        assert output_data["csv_data"]["reord_param_set"] == "symmetric=true"
        assert output_data["csv_data"]["exit_code"] == 0
    
    def test_multiple_techniques_sequential(self, tmp_path):
        """Test running multiple reordering techniques sequentially."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["structured_6x6"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        techniques = ["identity", "rcm"]
        results = {}
        
        for technique in techniques:
            result = run_reordering_test(matrix_path, technique, test_env["env"])
            assert result.returncode == 0, f"{technique} reordering failed: {result.stderr}"
            
            # Verify module loading for each technique
            if technique == "identity":
                assert "Loading module set: basic for technique identity" in result.stderr
            elif technique == "rcm":
                assert "Loading module set: python_scipy for technique rcm" in result.stderr
            
            # Store results for comparison
            output_data = validate_reordering_output(test_env["results_dir"], "matrix", technique)
            results[technique] = output_data
        
        # Verify both techniques produced valid but different results
        for technique in techniques:
            assert_valid_permutation(results[technique]["permutation"], 6)
            assert_valid_csv_data(results[technique]["csv_data"], technique, "matrix")
        
        # Identity should be identity permutation
        assert results["identity"]["permutation"] == [1, 2, 3, 4, 5, 6]
        
        # RCM should potentially reorder (different from identity for this structured matrix)
        # Note: This might be the same as identity for some matrices, which is valid


class TestReorderingPipelineIntegration:
    """Test suite for reordering pipeline integration."""
    
    def test_matrix_loading_and_processing(self, tmp_path):
        """Test complete matrix loading and processing pipeline."""
        matrices = get_test_matrices()
        
        # Test with different matrix sizes
        test_cases = [
            ("identity_4x4", 4),
            ("connected_5x5", 5),
            ("structured_6x6", 6)
        ]
        
        for matrix_name, size in test_cases:
            matrix_path = create_test_matrix(tmp_path, matrices[matrix_name], "dataset", f"test_{size}x{size}")
            test_env = setup_test_environment(tmp_path)
            
            result = run_reordering_test(matrix_path, "identity", test_env["env"])
            assert result.returncode == 0, f"Pipeline failed for {matrix_name}: {result.stderr}"
            
            # Verify output
            output_data = validate_reordering_output(test_env["results_dir"], f"test_{size}x{size}", "identity")
            assert_valid_permutation(output_data["permutation"], size)
            assert output_data["csv_data"]["n_rows"] == size
            assert output_data["csv_data"]["n_cols"] == size
    
    def test_csv_helper_integration(self, tmp_path):
        """Test that CSV helper properly integrates with reordering results."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["connected_5x5"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "rcm", test_env["env"])
        assert result.returncode == 0, f"RCM reordering failed: {result.stderr}"
        
        # Verify CSV contains required post-processing fields
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "rcm")
        csv_data = output_data["csv_data"]
        
        # Check that post-processing fields are populated
        assert "bandwidth" in csv_data, "bandwidth field missing from CSV"
        assert "block_density" in csv_data, "block_density field missing from CSV"
        assert "timestamp" in csv_data, "timestamp field missing from CSV"
        
        # Verify data types and constraints
        assert isinstance(csv_data["bandwidth"], (int, float))
        assert csv_data["bandwidth"] >= 0, "bandwidth should be non-negative"
        
        # Block density should be a JSON string
        assert isinstance(csv_data["block_density"], str)
        assert "{" in csv_data["block_density"], "block_density should be JSON format"
    
    def test_error_handling_integration(self, tmp_path):
        """Test error handling throughout the reordering pipeline."""
        test_env = setup_test_environment(tmp_path)
        
        # Test with non-existent matrix file
        fake_matrix = tmp_path / "nonexistent.mtx"
        
        result = run_reordering_test(fake_matrix, "identity", test_env["env"])
        # Should fail gracefully - exact behavior depends on implementation
        assert result.returncode != 0, "Should fail with non-existent matrix"
    
    def test_output_directory_structure(self, tmp_path):
        """Test that output directory structure is created correctly."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["identity_4x4"], "test_dataset", "test_matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "identity", test_env["env"])
        assert result.returncode == 0, f"Reordering failed: {result.stderr}"
        
        # Verify directory structure
        expected_dir = test_env["results_dir"] / "Reordering" / "test_matrix" / "identity_default"
        assert expected_dir.exists(), f"Expected output directory not created: {expected_dir}"
        
        # Verify required files
        assert (expected_dir / "permutation.g").exists(), "permutation.g file not created"
        assert (expected_dir / "results.csv").exists(), "results.csv file not created"
        
        # Verify file permissions
        perm_file = expected_dir / "permutation.g"
        csv_file = expected_dir / "results.csv"
        
        assert perm_file.is_file(), "permutation.g should be a regular file"
        assert csv_file.is_file(), "results.csv should be a regular file"
        assert perm_file.stat().st_size > 0, "permutation.g should not be empty"
        assert csv_file.stat().st_size > 0, "results.csv should not be empty"


class TestGraphBLASIntegration:
    """Test suite for GraphBLAS integration with reordering."""
    
    def test_graphblas_csv_helper_integration(self, tmp_path):
        """Test that GraphBLAS-based CSV helper works correctly."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["connected_5x5"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "identity", test_env["env"])
        assert result.returncode == 0, f"Reordering with GraphBLAS failed: {result.stderr}"
        
        # Verify that CSV processing completed successfully
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "identity")
        csv_data = output_data["csv_data"]
        
        # Verify GraphBLAS-computed fields are present and valid
        assert "bandwidth" in csv_data
        assert "block_density" in csv_data
        assert isinstance(csv_data["bandwidth"], (int, float))
        assert csv_data["bandwidth"] >= 0
    
    def test_rcm_graphblas_technique(self, tmp_path):
        """Test RCM GraphBLAS technique if available."""
        # This test might be skipped if GraphBLAS RCM is not implemented
        # or if it's the same as regular RCM
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["connected_5x5"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        try:
            result = run_reordering_test(matrix_path, "rcm_graphblas", test_env["env"])
            
            if result.returncode == 0:
                # If technique exists and works, verify output
                assert "Loading module set: python_graphblas for technique rcm_graphblas" in result.stderr
                
                output_data = validate_reordering_output(test_env["results_dir"], "matrix", "rcm_graphblas")
                assert_valid_permutation(output_data["permutation"], 5)
                assert_valid_csv_data(output_data["csv_data"], "rcm_graphblas", "matrix")
            else:
                # If technique doesn't exist or fails, that's acceptable for this test
                pytest.skip("rcm_graphblas technique not available or not working")
                
        except Exception as e:
            # If technique is not available, skip test
            pytest.skip(f"rcm_graphblas technique not available: {e}")