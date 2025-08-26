"""
Test fixtures and utilities for ReorderingSurvey2025 test suite.

This module provides common fixtures, helper functions, and utilities
used across different test categories.
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import pytest


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def sample_matrix_4x4():
    """Create a simple 4x4 diagonal matrix in Matrix Market format."""
    return """%%MatrixMarket matrix coordinate real general
4 4 4
1 1 1.0
2 2 2.0
3 3 3.0
4 4 4.0
"""


@pytest.fixture
def sample_matrix_5x5_connected():
    """Create a 5x5 connected matrix for reordering tests."""
    return """%%MatrixMarket matrix coordinate real general
5 5 13
1 1 1.0
1 2 2.0
2 1 3.0
2 2 4.0
2 3 5.0
3 2 6.0
3 3 7.0
3 4 8.0
4 3 9.0
4 4 10.0
4 5 11.0
5 4 12.0
5 5 13.0
"""


@pytest.fixture
def sample_matrix_6x6_structured():
    """Create a 6x6 structured matrix that benefits from reordering."""
    return """%%MatrixMarket matrix coordinate real general
6 6 12
1 1 1.0
1 4 2.0
2 2 3.0
2 5 4.0
3 3 5.0
3 6 6.0
4 1 7.0
4 4 8.0
5 2 9.0
5 5 10.0
6 3 11.0
6 6 12.0
"""


def create_test_matrix(tmp_path: Path, matrix_content: str, 
                      dataset_name: str = "test_dataset",
                      matrix_name: str = "test_matrix") -> Path:
    """
    Create a test matrix file in the proper directory structure.
    
    Args:
        tmp_path: Temporary directory path
        matrix_content: Matrix Market format content
        dataset_name: Dataset directory name
        matrix_name: Matrix file name (without .mtx extension)
    
    Returns:
        Path to the created matrix file
    """
    dataset_dir = tmp_path / dataset_name
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    matrix_file = dataset_dir / f"{matrix_name}.mtx"
    matrix_file.write_text(matrix_content)
    
    return matrix_file


def setup_test_environment(tmp_path: Path) -> Dict[str, Any]:
    """
    Set up a complete test environment with results directory and environment variables.
    
    Args:
        tmp_path: Temporary directory path
    
    Returns:
        Dictionary containing paths and environment setup
    """
    results_dir = tmp_path / "results"
    results_dir.mkdir(exist_ok=True)
    
    env = os.environ.copy()
    env["RESULTS_DIR"] = str(results_dir)
    
    return {
        "results_dir": results_dir,
        "env": env,
        "tmp_path": tmp_path
    }


def run_reordering_test(matrix_path: Path, technique: str, 
                       env: Dict[str, str], params: Optional[list] = None) -> subprocess.CompletedProcess:
    """
    Run a reordering test with the specified technique.
    
    Args:
        matrix_path: Path to the matrix file
        technique: Reordering technique name
        env: Environment variables
        params: Optional additional parameters
    
    Returns:
        Completed subprocess result
    """
    cmd = ["bash", "Programs/Reorder.sbatch", str(matrix_path), technique]
    if params:
        cmd.extend(params)
    
    return subprocess.run(cmd, env=env, capture_output=True, text=True)


def run_multiplication_test(results_csv: Path, kernel: str,
                          env: Dict[str, str], params: Optional[list] = None) -> subprocess.CompletedProcess:
    """
    Run a multiplication test with the specified kernel.
    
    Args:
        results_csv: Path to the reordering results CSV
        kernel: Multiplication kernel name
        env: Environment variables  
        params: Optional additional parameters
    
    Returns:
        Completed subprocess result
    """
    cmd = ["bash", "Programs/Multiply.sbatch", str(results_csv), kernel]
    if params:
        cmd.extend(params)
    
    return subprocess.run(cmd, env=env, capture_output=True, text=True)


def validate_reordering_output(results_dir: Path, matrix_name: str, 
                             technique: str, param_set: str = "default") -> Dict[str, Any]:
    """
    Validate reordering output files and return parsed data.
    
    Args:
        results_dir: Results directory path
        matrix_name: Matrix name
        technique: Reordering technique
        param_set: Parameter set name
    
    Returns:
        Dictionary containing validation results
    """
    output_dir = results_dir / "Reordering" / matrix_name / f"{technique}_{param_set}"
    
    # Check required files exist
    perm_file = output_dir / "permutation.g"
    csv_file = output_dir / "results.csv"
    
    assert perm_file.exists(), f"Permutation file not found: {perm_file}"
    assert csv_file.exists(), f"Results CSV not found: {csv_file}"
    
    # Read and validate permutation
    perm_content = perm_file.read_text().strip()
    permutation = [int(x) for x in perm_content.split()]
    
    # Read and validate CSV
    df = pd.read_csv(csv_file)
    assert len(df) == 1, f"Expected 1 row in CSV, got {len(df)}"
    
    return {
        "permutation": permutation,
        "csv_data": df.iloc[0].to_dict(),
        "output_dir": output_dir,
        "perm_file": perm_file,
        "csv_file": csv_file
    }


def validate_multiplication_output(results_dir: Path, matrix_name: str,
                                 reorder_technique: str, mult_kernel: str,
                                 reorder_param_set: str = "default") -> Dict[str, Any]:
    """
    Validate multiplication output files and return parsed data.
    
    Args:
        results_dir: Results directory path
        matrix_name: Matrix name
        reorder_technique: Reordering technique name
        mult_kernel: Multiplication kernel name
        reorder_param_set: Reordering parameter set name
    
    Returns:
        Dictionary containing validation results
    """
    output_dir = results_dir / "Multiplication" / matrix_name / f"{reorder_technique}_{reorder_param_set}" / mult_kernel
    
    # Check required files exist
    csv_file = output_dir / "results.csv"
    assert csv_file.exists(), f"Results CSV not found: {csv_file}"
    
    # Read and validate CSV
    df = pd.read_csv(csv_file)
    assert len(df) == 1, f"Expected 1 row in CSV, got {len(df)}"
    
    return {
        "csv_data": df.iloc[0].to_dict(),
        "output_dir": output_dir,
        "csv_file": csv_file
    }


def assert_valid_permutation(permutation: list, expected_size: int):
    """
    Assert that a permutation is valid.
    
    Args:
        permutation: List of permutation indices
        expected_size: Expected size of the permutation
    """
    assert len(permutation) == expected_size, f"Expected permutation size {expected_size}, got {len(permutation)}"
    assert set(permutation) == set(range(1, expected_size + 1)), f"Invalid permutation: {permutation}"


def assert_valid_csv_data(csv_data: Dict[str, Any], expected_technique: str, expected_matrix: str):
    """
    Assert that CSV data contains expected values.
    
    Args:
        csv_data: Dictionary of CSV row data
        expected_technique: Expected technique name
        expected_matrix: Expected matrix name
    """
    assert csv_data["matrix_name"] == expected_matrix, f"Unexpected matrix name: {csv_data['matrix_name']}"
    assert csv_data["exit_code"] == 0, f"Non-zero exit code: {csv_data['exit_code']}"
    
    if "reorder_tech" in csv_data:
        assert csv_data["reorder_tech"] == expected_technique, f"Unexpected technique: {csv_data['reorder_tech']}"
    
    if "mult_type" in csv_data:
        assert csv_data["mult_type"] == expected_technique, f"Unexpected mult type: {csv_data['mult_type']}"


def get_test_matrices():
    """Return a dictionary of test matrices for various scenarios."""
    return {
        "identity_4x4": """%%MatrixMarket matrix coordinate real general
4 4 4
1 1 1.0
2 2 2.0
3 3 3.0
4 4 4.0
""",
        "connected_5x5": """%%MatrixMarket matrix coordinate real general
5 5 13
1 1 1.0
1 2 2.0
2 1 3.0
2 2 4.0
2 3 5.0
3 2 6.0
3 3 7.0
3 4 8.0
4 3 9.0
4 4 10.0
4 5 11.0
5 4 12.0
5 5 13.0
""",
        "structured_6x6": """%%MatrixMarket matrix coordinate real general
6 6 12
1 1 1.0
1 4 2.0
2 2 3.0
2 5 4.0
3 3 5.0
3 6 6.0
4 1 7.0
4 4 8.0
5 2 9.0
5 5 10.0
6 3 11.0
6 6 12.0
""",
        "disconnected_4x4": """%%MatrixMarket matrix coordinate real general
4 4 2
1 1 1.0
3 3 2.0
"""
    }