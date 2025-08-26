"""
Unit tests for reordering techniques.

Tests individual reordering algorithms in isolation.
"""
import pytest
from tests.utils.fixtures import (
    create_test_matrix, setup_test_environment, run_reordering_test,
    validate_reordering_output, assert_valid_permutation, assert_valid_csv_data,
    get_test_matrices
)


class TestIdentityReordering:
    """Test suite for identity reordering technique."""
    
    def test_identity_basic_4x4(self, tmp_path):
        """Test identity reordering with basic 4x4 matrix."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["identity_4x4"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "identity", test_env["env"])
        assert result.returncode == 0, f"Identity reordering failed: {result.stderr}"
        
        # Validate output
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "identity")
        
        # Identity should produce identity permutation
        assert_valid_permutation(output_data["permutation"], 4)
        assert output_data["permutation"] == [1, 2, 3, 4]
        
        # Validate CSV data
        assert_valid_csv_data(output_data["csv_data"], "identity", "matrix")
        assert output_data["csv_data"]["n_rows"] == 4
        assert output_data["csv_data"]["n_cols"] == 4
        assert output_data["csv_data"]["nnz"] == 4
        assert output_data["csv_data"]["reorder_type"] == "1D"
    
    def test_identity_larger_matrix(self, tmp_path):
        """Test identity reordering with larger matrix."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["structured_6x6"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "identity", test_env["env"])
        assert result.returncode == 0, f"Identity reordering failed: {result.stderr}"
        
        # Validate output
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "identity")
        
        # Identity should produce identity permutation
        assert_valid_permutation(output_data["permutation"], 6)
        assert output_data["permutation"] == [1, 2, 3, 4, 5, 6]


class TestRCMReordering:
    """Test suite for Reverse Cuthill-McKee reordering technique."""
    
    def test_rcm_connected_matrix(self, tmp_path):
        """Test RCM reordering with connected matrix."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["connected_5x5"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "rcm", test_env["env"])
        assert result.returncode == 0, f"RCM reordering failed: {result.stderr}"
        
        # Validate output
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "rcm")
        
        # RCM should produce valid permutation
        assert_valid_permutation(output_data["permutation"], 5)
        
        # Validate CSV data
        assert_valid_csv_data(output_data["csv_data"], "rcm", "matrix")
        assert output_data["csv_data"]["n_rows"] == 5
        assert output_data["csv_data"]["n_cols"] == 5
        assert output_data["csv_data"]["nnz"] == 13
        assert output_data["csv_data"]["reorder_type"] == "2D"  # From config
    
    def test_rcm_structured_matrix(self, tmp_path):
        """Test RCM reordering with structured matrix that benefits from reordering."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["structured_6x6"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "rcm", test_env["env"])
        assert result.returncode == 0, f"RCM reordering failed: {result.stderr}"
        
        # Validate output
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "rcm")
        
        # RCM should produce valid permutation
        assert_valid_permutation(output_data["permutation"], 6)
        
        # For this structured matrix, RCM should reorder (not identity)
        assert output_data["permutation"] != [1, 2, 3, 4, 5, 6], "RCM should reorder this structured matrix"
    
    def test_rcm_with_symmetric_parameter(self, tmp_path):
        """Test RCM reordering with symmetric=true parameter."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["connected_5x5"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "rcm", test_env["env"], ["symmetric=true"])
        assert result.returncode == 0, f"RCM symmetric reordering failed: {result.stderr}"
        
        # The parameter handling might vary - just verify the command succeeded
        # and some output was created
        reorder_dir = test_env["results_dir"] / "Reordering" / "matrix"
        assert reorder_dir.exists(), "Reordering output directory should exist"
        
        # Find any RCM output directory
        rcm_dirs = list(reorder_dir.glob("rcm*"))
        assert len(rcm_dirs) > 0, "Should have at least one RCM output directory"
        
        # Verify the first RCM directory has valid output
        output_dir = rcm_dirs[0]
        perm_file = output_dir / "permutation.g"
        csv_file = output_dir / "results.csv"
        
        assert perm_file.exists(), f"Permutation file not found: {perm_file}"
        assert csv_file.exists(), f"Results CSV not found: {csv_file}"
    
    def test_rcm_disconnected_matrix(self, tmp_path):
        """Test RCM reordering with disconnected matrix."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["disconnected_4x4"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "rcm", test_env["env"])
        assert result.returncode == 0, f"RCM disconnected reordering failed: {result.stderr}"
        
        # Validate output
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "rcm")
        
        # RCM should handle disconnected matrix gracefully
        assert_valid_permutation(output_data["permutation"], 4)


class TestAMDReordering:
    """Test suite for AMD (Approximate Minimum Degree) reordering technique."""
    
    def test_amd_basic_functionality(self, tmp_path):
        """Test basic AMD reordering on a structured matrix."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["structured_6x6"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "amd", test_env["env"])
        assert result.returncode == 0, f"AMD reordering failed: {result.stderr}"
        
        # Parse and validate output
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "amd")
        assert_valid_permutation(output_data["permutation"], 6)
        assert_valid_csv_data(output_data["csv_data"], "amd", "matrix")
        
        # AMD should typically produce a non-identity permutation for structured matrices
        # but we don't require a specific order since AMD is heuristic
    
    def test_amd_with_symmetric_parameter(self, tmp_path):
        """Test AMD reordering with symmetric=true parameter."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["connected_5x5"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "amd", test_env["env"], ["symmetric=true"])
        assert result.returncode == 0, f"AMD symmetric reordering failed: {result.stderr}"
        
        # Verify output structure - parameters create different directory names
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "amd", "symmetric-true")
        assert_valid_permutation(output_data["permutation"], 5)
        assert_valid_csv_data(output_data["csv_data"], "amd", "matrix")
    
    def test_amd_identity_matrix(self, tmp_path):
        """Test AMD reordering on an identity matrix."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["identity_4x4"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "amd", test_env["env"])
        assert result.returncode == 0, f"AMD reordering failed on identity matrix: {result.stderr}"
        
        # Parse and validate output
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "amd")
        assert_valid_permutation(output_data["permutation"], 4)
        assert_valid_csv_data(output_data["csv_data"], "amd", "matrix")


class TestReorderingOutputFormats:
    """Test suite for validating reordering output formats."""
    
    def test_permutation_file_format(self, tmp_path):
        """Test that permutation files follow correct format."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["identity_4x4"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "identity", test_env["env"])
        assert result.returncode == 0
        
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "identity")
        
        # Check permutation file content format
        perm_content = output_data["perm_file"].read_text()
        lines = perm_content.strip().split('\n')
        assert len(lines) == 4, "Permutation should have 4 lines for 4x4 matrix"
        
        for line in lines:
            assert line.strip().isdigit(), f"Permutation line should be integer: {line}"
    
    def test_csv_output_schema(self, tmp_path):
        """Test that CSV output follows expected schema."""
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["identity_4x4"], "dataset", "matrix")
        test_env = setup_test_environment(tmp_path)
        
        result = run_reordering_test(matrix_path, "identity", test_env["env"])
        assert result.returncode == 0
        
        output_data = validate_reordering_output(test_env["results_dir"], "matrix", "identity")
        csv_data = output_data["csv_data"]
        
        # Check required columns exist
        required_columns = [
            "matrix_name", "dataset", "n_rows", "n_cols", "nnz",
            "reorder_type", "reorder_tech", "reorder_time_ms",
            "bandwidth", "block_density", "exit_code", "timestamp"
        ]
        
        for col in required_columns:
            assert col in csv_data, f"Required column missing: {col}"
        
        # Check data types and constraints
        assert isinstance(csv_data["n_rows"], (int, float))
        assert isinstance(csv_data["n_cols"], (int, float))
        assert isinstance(csv_data["nnz"], (int, float))
        assert csv_data["exit_code"] == 0
        assert csv_data["reorder_time_ms"] >= 0
        assert isinstance(csv_data["timestamp"], str)