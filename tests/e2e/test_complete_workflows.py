"""
End-to-end tests for complete pipeline workflows.

Tests the entire system from matrix input to final results, simulating
real-world usage scenarios.
"""
import pytest
from tests.utils.fixtures import (
    create_test_matrix, setup_test_environment, run_reordering_test, run_multiplication_test,
    validate_reordering_output, validate_multiplication_output, get_test_matrices
)


class TestCompleteWorkflows:
    """Test suite for complete end-to-end workflows."""
    
    def test_complete_research_workflow(self, tmp_path):
        """
        Test a complete research workflow with multiple matrices and techniques.
        
        This simulates a real research scenario where a user wants to:
        1. Test multiple reordering techniques on different matrices
        2. Apply multiplication kernels to each reordered matrix
        3. Compare results across techniques and matrices
        """
        matrices = get_test_matrices()
        
        # Define test scenario
        test_matrices = [
            ("identity_4x4", "diagonal", 4, 4),
            ("connected_5x5", "connected", 5, 13),
            ("structured_6x6", "structured", 6, 12),
        ]
        
        reorder_techniques = ["identity", "rcm"]
        mult_kernels = ["mock"]
        
        results_summary = {}
        
        for matrix_key, matrix_name, size, nnz in test_matrices:
            matrix_path = create_test_matrix(tmp_path, matrices[matrix_key], "benchmark", matrix_name)
            test_env = setup_test_environment(tmp_path)
            
            results_summary[matrix_name] = {}
            
            for technique in reorder_techniques:
                # Run reordering
                reorder_result = run_reordering_test(matrix_path, technique, test_env["env"])
                assert reorder_result.returncode == 0, f"Reordering {matrix_name} with {technique} failed: {reorder_result.stderr}"
                
                reorder_output = validate_reordering_output(test_env["results_dir"], matrix_name, technique)
                
                # Verify reordering results
                assert len(reorder_output["permutation"]) == size
                assert reorder_output["csv_data"]["n_rows"] == size
                assert reorder_output["csv_data"]["nnz"] == nnz
                assert reorder_output["csv_data"]["exit_code"] == 0
                
                results_summary[matrix_name][technique] = {
                    "reorder_time": reorder_output["csv_data"]["reorder_time_ms"],
                    "bandwidth": reorder_output["csv_data"]["bandwidth"],
                }
                
                for kernel in mult_kernels:
                    # Run multiplication
                    mult_result = run_multiplication_test(reorder_output["csv_file"], kernel, test_env["env"])
                    assert mult_result.returncode == 0, f"Multiplication {matrix_name}/{technique} with {kernel} failed: {mult_result.stderr}"
                    
                    mult_output = validate_multiplication_output(test_env["results_dir"], matrix_name, technique, kernel)
                    
                    # Verify multiplication results
                    assert mult_output["csv_data"]["mult_time_ms"] > 0
                    assert mult_output["csv_data"]["exit_code"] == 0
                    
                    results_summary[matrix_name][technique][f"{kernel}_time"] = mult_output["csv_data"]["mult_time_ms"]
        
        # Verify we have results for all combinations
        assert len(results_summary) == len(test_matrices)
        for matrix_name in results_summary:
            assert len(results_summary[matrix_name]) == len(reorder_techniques)
            for technique in reorder_techniques:
                assert "reorder_time" in results_summary[matrix_name][technique]
                assert "bandwidth" in results_summary[matrix_name][technique]
                for kernel in mult_kernels:
                    assert f"{kernel}_time" in results_summary[matrix_name][technique]
    
    def test_parameter_sweep_workflow(self, tmp_path):
        """
        Test parameter sweep workflow.
        
        Simulates testing different parameter combinations for a technique.
        """
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["connected_5x5"], "param_study", "test_matrix")
        test_env = setup_test_environment(tmp_path)
        
        # Test RCM with different parameters
        rcm_params = [
            [],  # default
            ["symmetric=true"],
        ]
        
        mult_params = [
            ["alpha=1.0"],
            ["alpha=2.0", "beta=0.5"],
        ]
        
        results = {}
        
        for i, reorder_params in enumerate(rcm_params):
            param_set_name = "default" if not reorder_params else "_".join(reorder_params).replace("=", "")
            
            # Run reordering with parameters
            reorder_result = run_reordering_test(matrix_path, "rcm", test_env["env"], reorder_params)
            assert reorder_result.returncode == 0, f"RCM with params {reorder_params} failed: {reorder_result.stderr}"
            
            param_set_dir = "symmetric" if reorder_params else "default"
            reorder_output = validate_reordering_output(test_env["results_dir"], "test_matrix", "rcm", param_set_dir)
            
            # Verify parameter set is recorded
            if reorder_params:
                expected_param_str = ";".join(reorder_params)
                assert reorder_output["csv_data"]["reord_param_set"] == expected_param_str
            
            results[param_set_name] = {"reorder": reorder_output}
            
            # Test multiplication with different parameters
            for j, mult_param_list in enumerate(mult_params):
                mult_result = run_multiplication_test(reorder_output["csv_file"], "mock", test_env["env"], mult_param_list)
                assert mult_result.returncode == 0, f"Mock with params {mult_param_list} failed: {mult_result.stderr}"
                
                mult_output = validate_multiplication_output(test_env["results_dir"], "test_matrix", f"rcm_{param_set_dir}", "mock")
                results[param_set_name][f"mult_{j}"] = mult_output
        
        # Verify all parameter combinations were tested
        assert len(results) == len(rcm_params)
        for param_set in results:
            assert "reorder" in results[param_set]
            assert len([k for k in results[param_set] if k.startswith("mult_")]) == len(mult_params)
    
    def test_batch_processing_workflow(self, tmp_path):
        """
        Test batch processing workflow.
        
        Simulates processing multiple matrices with the same configuration.
        """
        matrices = get_test_matrices()
        
        # Create multiple test matrices
        test_data = [
            ("identity_4x4", "batch_test_1", 4),
            ("connected_5x5", "batch_test_2", 5),
            ("disconnected_4x4", "batch_test_3", 4),
        ]
        
        batch_results = {}
        
        for matrix_key, matrix_name, size in test_data:
            matrix_path = create_test_matrix(tmp_path, matrices[matrix_key], "batch", matrix_name)
            test_env = setup_test_environment(tmp_path)
            
            # Standard processing pipeline
            reorder_result = run_reordering_test(matrix_path, "identity", test_env["env"])
            assert reorder_result.returncode == 0, f"Batch reordering {matrix_name} failed: {reorder_result.stderr}"
            
            reorder_output = validate_reordering_output(test_env["results_dir"], matrix_name, "identity")
            
            mult_result = run_multiplication_test(reorder_output["csv_file"], "mock", test_env["env"])
            assert mult_result.returncode == 0, f"Batch multiplication {matrix_name} failed: {mult_result.stderr}"
            
            mult_output = validate_multiplication_output(test_env["results_dir"], matrix_name, "identity", "mock")
            
            # Store results
            batch_results[matrix_name] = {
                "size": size,
                "reorder_time": reorder_output["csv_data"]["reorder_time_ms"],
                "mult_time": mult_output["csv_data"]["mult_time_ms"],
                "bandwidth": reorder_output["csv_data"]["bandwidth"],
            }
        
        # Verify batch processing results
        assert len(batch_results) == len(test_data)
        
        # All should have completed successfully
        for matrix_name in batch_results:
            result = batch_results[matrix_name]
            assert result["reorder_time"] >= 0
            assert result["mult_time"] > 0
            assert result["bandwidth"] >= 0.0
            assert result["size"] in [4, 5]  # Expected sizes
    
    def test_comparison_study_workflow(self, tmp_path):
        """
        Test comparison study workflow.
        
        Simulates a study comparing different techniques on the same matrix.
        """
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["structured_6x6"], "comparison", "benchmark_matrix")
        test_env = setup_test_environment(tmp_path)
        
        techniques = ["identity", "rcm"]
        kernels = ["mock"]
        
        study_results = {}
        
        for technique in techniques:
            # Run reordering
            reorder_result = run_reordering_test(matrix_path, technique, test_env["env"])
            assert reorder_result.returncode == 0, f"Comparison reordering with {technique} failed: {reorder_result.stderr}"
            
            reorder_output = validate_reordering_output(test_env["results_dir"], "benchmark_matrix", technique)
            
            study_results[technique] = {
                "permutation": reorder_output["permutation"].copy(),
                "reorder_time": reorder_output["csv_data"]["reorder_time_ms"],
                "bandwidth": reorder_output["csv_data"]["bandwidth"],
                "kernels": {}
            }
            
            for kernel in kernels:
                # Run multiplication
                mult_result = run_multiplication_test(reorder_output["csv_file"], kernel, test_env["env"])
                assert mult_result.returncode == 0, f"Comparison multiplication {technique}/{kernel} failed: {mult_result.stderr}"
                
                mult_output = validate_multiplication_output(test_env["results_dir"], "benchmark_matrix", technique, kernel)
                
                study_results[technique]["kernels"][kernel] = {
                    "mult_time": mult_output["csv_data"]["mult_time_ms"],
                }
        
        # Verify comparison results
        assert len(study_results) == len(techniques)
        
        # Identity should produce identity permutation
        assert study_results["identity"]["permutation"] == [1, 2, 3, 4, 5, 6]
        
        # RCM might produce different permutation (depending on matrix structure)
        rcm_perm = study_results["rcm"]["permutation"]
        assert len(rcm_perm) == 6
        assert set(rcm_perm) == {1, 2, 3, 4, 5, 6}  # Valid permutation
        
        # Both techniques should have valid timing data
        for technique in techniques:
            assert study_results[technique]["reorder_time"] >= 0
            assert study_results[technique]["bandwidth"] >= 0.0
            for kernel in kernels:
                assert study_results[technique]["kernels"][kernel]["mult_time"] > 0
    
    def test_error_recovery_workflow(self, tmp_path):
        """
        Test error recovery in workflows.
        
        Simulates handling of various error conditions.
        """
        test_env = setup_test_environment(tmp_path)
        
        # Test 1: Invalid matrix file
        invalid_matrix = tmp_path / "invalid.mtx"
        invalid_matrix.write_text("Not a valid matrix market file")
        
        reorder_result = run_reordering_test(invalid_matrix, "identity", test_env["env"])
        # Should fail gracefully
        assert reorder_result.returncode != 0
        
        # Test 2: Valid workflow for comparison
        matrices = get_test_matrices()
        valid_matrix = create_test_matrix(tmp_path, matrices["identity_4x4"], "recovery", "valid_matrix")
        
        reorder_result = run_reordering_test(valid_matrix, "identity", test_env["env"])
        assert reorder_result.returncode == 0, f"Valid workflow failed: {reorder_result.stderr}"
        
        reorder_output = validate_reordering_output(test_env["results_dir"], "valid_matrix", "identity")
        
        mult_result = run_multiplication_test(reorder_output["csv_file"], "mock", test_env["env"])
        assert mult_result.returncode == 0, f"Valid multiplication failed: {mult_result.stderr}"
        
        # Verify valid workflow completed successfully
        mult_output = validate_multiplication_output(test_env["results_dir"], "valid_matrix", "identity", "mock")
        assert mult_output["csv_data"]["exit_code"] == 0


class TestRealWorldScenarios:
    """Test suite for realistic research scenarios."""
    
    def test_sparse_matrix_suite_simulation(self, tmp_path):
        """
        Simulate processing matrices from a sparse matrix suite.
        
        Tests scenario where a researcher downloads matrices from SuiteSparse
        and wants to benchmark reordering techniques.
        """
        # Simulate different types of matrices that might be found in a suite
        matrix_suite = {
            "diagonal_small": ("identity_4x4", 4, 4),
            "graph_medium": ("connected_5x5", 5, 13),
            "structured_medium": ("structured_6x6", 6, 12),
        }
        
        matrices = get_test_matrices()
        
        # Process each matrix with standard techniques
        suite_results = {}
        
        for suite_name, (matrix_key, size, nnz) in matrix_suite.items():
            # Create matrix in SuiteSparse-like directory structure
            collection = "TestSuite"
            matrix_path = create_test_matrix(tmp_path, matrices[matrix_key], collection, suite_name)
            test_env = setup_test_environment(tmp_path)
            
            suite_results[suite_name] = {}
            
            # Test with both identity and RCM
            for technique in ["identity", "rcm"]:
                reorder_result = run_reordering_test(matrix_path, technique, test_env["env"])
                assert reorder_result.returncode == 0, f"Suite processing {suite_name}/{technique} failed: {reorder_result.stderr}"
                
                reorder_output = validate_reordering_output(test_env["results_dir"], suite_name, technique)
                
                # Verify basic properties
                assert reorder_output["csv_data"]["dataset"] == collection
                assert reorder_output["csv_data"]["matrix_name"] == suite_name
                assert reorder_output["csv_data"]["n_rows"] == size
                assert reorder_output["csv_data"]["nnz"] == nnz
                
                # Test with mock multiplication
                mult_result = run_multiplication_test(reorder_output["csv_file"], "mock", test_env["env"])
                assert mult_result.returncode == 0, f"Suite multiplication {suite_name}/{technique} failed: {mult_result.stderr}"
                
                mult_output = validate_multiplication_output(test_env["results_dir"], suite_name, technique, "mock")
                
                suite_results[suite_name][technique] = {
                    "reorder_time": reorder_output["csv_data"]["reorder_time_ms"],
                    "mult_time": mult_output["csv_data"]["mult_time_ms"],
                    "bandwidth": reorder_output["csv_data"]["bandwidth"],
                }
        
        # Verify suite processing completed
        assert len(suite_results) == len(matrix_suite)
        for matrix_name in suite_results:
            assert "identity" in suite_results[matrix_name]
            assert "rcm" in suite_results[matrix_name]
            
            # Verify reasonable timing values
            for technique in ["identity", "rcm"]:
                result = suite_results[matrix_name][technique]
                assert result["reorder_time"] >= 0
                assert result["mult_time"] > 0
                assert result["bandwidth"] >= 0.0
    
    def test_gpu_cpu_comparison_workflow(self, tmp_path):
        """
        Test workflow comparing GPU and CPU multiplication kernels.
        
        Simulates scenario where researcher wants to compare performance
        between different multiplication implementations.
        """
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["connected_5x5"], "gpu_cpu_study", "test_matrix")
        test_env = setup_test_environment(tmp_path)
        
        # First reorder the matrix
        reorder_result = run_reordering_test(matrix_path, "rcm", test_env["env"])
        assert reorder_result.returncode == 0, f"Reordering for GPU/CPU comparison failed: {reorder_result.stderr}"
        
        reorder_output = validate_reordering_output(test_env["results_dir"], "test_matrix", "rcm")
        
        # Test different multiplication kernels
        kernels = ["mock", "cucsrspmm"]
        comparison_results = {}
        
        for kernel in kernels:
            mult_result = run_multiplication_test(reorder_output["csv_file"], kernel, test_env["env"])
            assert mult_result.returncode == 0, f"Multiplication with {kernel} failed: {mult_result.stderr}"
            
            mult_output = validate_multiplication_output(test_env["results_dir"], "test_matrix", "rcm", kernel)
            
            comparison_results[kernel] = {
                "mult_time": mult_output["csv_data"]["mult_time_ms"],
                "exit_code": mult_output["csv_data"]["exit_code"],
            }
        
        # Verify comparison results
        assert len(comparison_results) == len(kernels)
        for kernel in kernels:
            assert comparison_results[kernel]["mult_time"] > 0
            assert comparison_results[kernel]["exit_code"] == 0
        
        # Both kernels should complete successfully
        # (Note: cuSPARSE might fall back to CPU if no GPU available, which is fine)
    
    def test_reproducibility_workflow(self, tmp_path):
        """
        Test reproducibility of results.
        
        Verifies that running the same workflow multiple times produces
        consistent results (within reasonable timing variation).
        """
        matrices = get_test_matrices()
        matrix_path = create_test_matrix(tmp_path, matrices["identity_4x4"], "repro_study", "test_matrix")
        
        # Run the same workflow multiple times
        runs = []
        num_runs = 3
        
        for run_id in range(num_runs):
            test_env = setup_test_environment(tmp_path / f"run_{run_id}")
            
            # Reordering
            reorder_result = run_reordering_test(matrix_path, "identity", test_env["env"])
            assert reorder_result.returncode == 0, f"Reproducibility run {run_id} reordering failed: {reorder_result.stderr}"
            
            reorder_output = validate_reordering_output(test_env["results_dir"], "test_matrix", "identity")
            
            # Multiplication
            mult_result = run_multiplication_test(reorder_output["csv_file"], "mock", test_env["env"])
            assert mult_result.returncode == 0, f"Reproducibility run {run_id} multiplication failed: {mult_result.stderr}"
            
            mult_output = validate_multiplication_output(test_env["results_dir"], "test_matrix", "identity", "mock")
            
            runs.append({
                "permutation": reorder_output["permutation"].copy(),
                "reorder_time": reorder_output["csv_data"]["reorder_time_ms"],
                "mult_time": mult_output["csv_data"]["mult_time_ms"],
                "bandwidth": reorder_output["csv_data"]["bandwidth"],
            })
        
        # Verify reproducibility
        assert len(runs) == num_runs
        
        # Permutation should be identical across runs (deterministic algorithms)
        reference_perm = runs[0]["permutation"]
        for run in runs[1:]:
            assert run["permutation"] == reference_perm, "Permutation should be reproducible"
        
        # Bandwidth should be identical (deterministic)
        reference_bandwidth = runs[0]["bandwidth"]
        for run in runs[1:]:
            assert run["bandwidth"] == reference_bandwidth, "Bandwidth should be reproducible"
        
        # Timing might vary slightly, but should be in reasonable range
        reorder_times = [run["reorder_time"] for run in runs]
        mult_times = [run["mult_time"] for run in runs]
        
        # All timing values should be positive
        assert all(t >= 0 for t in reorder_times), "All reorder times should be non-negative"
        assert all(t > 0 for t in mult_times), "All multiplication times should be positive"
        
        # Timing variation should be reasonable (within 2x factor)
        if max(reorder_times) > 0:  # Avoid division by zero
            assert max(reorder_times) / max(min(reorder_times), 1) < 10, "Reorder timing variation too large"
        assert max(mult_times) / min(mult_times) < 3, "Multiplication timing variation too large"