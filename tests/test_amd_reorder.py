import os
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def test_amd_reorder_basic(tmp_path):
    """Test AMD reordering with a basic matrix"""
    # Create a simple 5x5 tridiagonal matrix where AMD can reorder meaningfully
    # This represents a chain graph: 1-2-3-4-5
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    mtx = dataset / "matrix.mtx"
    mtx.write_text(
        """%%MatrixMarket matrix coordinate real general
5 5 13
1 1 1
1 2 1
2 1 1
2 2 1
2 3 1
3 2 1
3 3 1
3 4 1
4 3 1
4 4 1
4 5 1
5 4 1
5 5 1
"""
    )

    # Run the reordering driver
    env = os.environ.copy()
    results_dir = tmp_path / "results"
    env["RESULTS_DIR"] = str(results_dir)
    result = subprocess.run(
        ["bash", "Programs/Reorder.sbatch", str(mtx), "amd"],
        capture_output=True,
        text=True,
        env=env,
    )

    # Check that the command succeeded
    assert result.returncode == 0, f"AMD command failed with stderr: {result.stderr}"

    # Verify that the permutation and results CSV were produced
    out_dir = results_dir / "Reordering" / "matrix" / "amd_default"
    perm_file = out_dir / "permutation.g"
    csv_file = out_dir / "results.csv"
    
    assert perm_file.exists(), "Permutation file not created"
    assert csv_file.exists(), "Results CSV file not created"

    # Read and validate the permutation
    perm = np.loadtxt(perm_file, dtype=int)
    assert len(perm) == 5, f"Expected permutation length 5, got {len(perm)}"
    assert set(perm) == {1, 2, 3, 4, 5}, f"Permutation should be a valid reordering of 1-5, got {perm}"

    # Verify results CSV
    df = pd.read_csv(csv_file)
    assert df.loc[0, "matrix_name"] == "matrix"
    assert df.loc[0, "dataset"] == "dataset"
    assert df.loc[0, "n_rows"] == 5
    assert df.loc[0, "n_cols"] == 5
    assert df.loc[0, "nnz"] == 13
    assert df.loc[0, "reorder_type"] == "2D"  # From config/reorder.yml
    assert df.loc[0, "reorder_tech"] == "amd"
    assert df.loc[0, "exit_code"] == 0
    assert df.loc[0, "reorder_time_ms"] >= 0


def test_amd_reorder_star_graph(tmp_path):
    """Test AMD reordering with a star graph (center node should be eliminated last)"""
    # Create a star graph where node 1 is connected to all others
    # AMD should eliminate the leaves (degree 1) first, then the center
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    mtx = dataset / "matrix.mtx"
    mtx.write_text(
        """%%MatrixMarket matrix coordinate real general
5 5 13
1 1 1
1 2 1
1 3 1
1 4 1
1 5 1
2 1 1
2 2 1
3 1 1
3 3 1
4 1 1
4 4 1
5 1 1
5 5 1
"""
    )

    # Run the reordering driver
    env = os.environ.copy()
    results_dir = tmp_path / "results"
    env["RESULTS_DIR"] = str(results_dir)
    subprocess.run(
        ["bash", "Programs/Reorder.sbatch", str(mtx), "amd"],
        check=True,
        env=env,
    )

    # Verify outputs
    out_dir = results_dir / "Reordering" / "matrix" / "amd_default"
    perm_file = out_dir / "permutation.g"
    
    # Read and validate the permutation
    perm = np.loadtxt(perm_file, dtype=int)
    assert len(perm) == 5, f"Expected permutation length 5, got {len(perm)}"
    assert set(perm) == {1, 2, 3, 4, 5}, f"Permutation should be a valid reordering of 1-5, got {perm}"
    
    # For a star graph, AMD should eliminate the center node (1) last since it has highest degree
    # The leaves (2, 3, 4, 5) should come before the center in the elimination ordering
    center_pos = np.where(perm == 1)[0][0]  # Position of center node in elimination order
    assert center_pos >= 2, f"Center node should be eliminated after most leaves, but was at position {center_pos}"


def test_amd_reorder_with_parameters(tmp_path):
    """Test AMD reordering with custom parameters"""
    # Create a test matrix
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    mtx = dataset / "matrix.mtx"
    mtx.write_text(
        """%%MatrixMarket matrix coordinate real general
4 4 10
1 1 1
1 2 1
2 1 1
2 2 1
2 3 1
3 2 1
3 3 1
3 4 1
4 3 1
4 4 1
"""
    )

    # Run the reordering driver with symmetric=false parameter
    env = os.environ.copy()
    results_dir = tmp_path / "results"
    env["RESULTS_DIR"] = str(results_dir)
    
    result = subprocess.run(
        ["bash", "Programs/Reorder.sbatch", str(mtx), "amd", "symmetric=false"],
        capture_output=True,
        text=True,
        env=env,
    )

    # Check that the command succeeded
    assert result.returncode == 0, f"AMD with parameters failed with stderr: {result.stderr}"

    # Verify outputs with parameter set ID
    out_dir = results_dir / "Reordering" / "matrix" / "amd_symmetric-false"
    assert (out_dir / "permutation.g").exists()
    assert (out_dir / "results.csv").exists()
    
    # Verify the parameter set is recorded in CSV
    df = pd.read_csv(out_dir / "results.csv")
    assert df.loc[0, "reord_param_set"] == "symmetric=false"


def test_amd_reorder_disconnected_matrix(tmp_path):
    """Test AMD reordering with a disconnected matrix (multiple components)"""
    # Create a matrix with two disconnected components
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    mtx = dataset / "matrix.mtx"
    mtx.write_text(
        """%%MatrixMarket matrix coordinate real general
6 6 9
1 1 1
1 2 1
2 1 1
2 2 1
4 4 1
4 5 1
5 4 1
5 5 1
6 6 1
"""
    )

    # Run the reordering driver
    env = os.environ.copy()
    results_dir = tmp_path / "results"
    env["RESULTS_DIR"] = str(results_dir)
    subprocess.run(
        ["bash", "Programs/Reorder.sbatch", str(mtx), "amd"],
        check=True,
        env=env,
    )

    # Verify outputs - AMD should handle disconnected components gracefully
    out_dir = results_dir / "Reordering" / "matrix" / "amd_default"
    perm_file = out_dir / "permutation.g"
    
    # Read and validate the permutation
    perm = np.loadtxt(perm_file, dtype=int)
    assert len(perm) == 6, f"Expected permutation length 6, got {len(perm)}"
    assert set(perm) == {1, 2, 3, 4, 5, 6}, f"Permutation should be a valid reordering of 1-6, got {perm}"
    
    # Verify successful completion
    df = pd.read_csv(out_dir / "results.csv")
    assert df.loc[0, "exit_code"] == 0


def test_amd_reorder_single_node(tmp_path):
    """Test AMD reordering with a single node matrix"""
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    mtx = dataset / "matrix.mtx"
    mtx.write_text(
        """%%MatrixMarket matrix coordinate real general
1 1 1
1 1 1.0
"""
    )

    # Run the reordering driver
    env = os.environ.copy()
    results_dir = tmp_path / "results"
    env["RESULTS_DIR"] = str(results_dir)
    subprocess.run(
        ["bash", "Programs/Reorder.sbatch", str(mtx), "amd"],
        check=True,
        env=env,
    )

    # Verify outputs
    out_dir = results_dir / "Reordering" / "matrix" / "amd_default"
    perm_file = out_dir / "permutation.g"
    
    # Read and validate the permutation
    perm = np.loadtxt(perm_file, dtype=int)
    perm = np.atleast_1d(perm)  # Ensure it's an array even for single values
    assert len(perm) == 1, f"Expected permutation length 1, got {len(perm)}"
    assert perm[0] == 1, f"Single node permutation should be [1], got {perm}"


def test_amd_wrapper_direct_call(tmp_path):
    """Test calling the AMD wrapper script directly"""
    # Create test matrix
    mtx = tmp_path / "test.mtx"
    mtx.write_text(
        """%%MatrixMarket matrix coordinate real general
3 3 6
1 1 1
1 2 1
2 1 1
2 2 1
2 3 1
3 2 1
"""
    )
    
    perm_file = tmp_path / "perm.g"
    
    # Call wrapper directly
    result = subprocess.run(
        ["bash", "Programs/Reordering/Techniques/reordering_amd.sh", str(mtx), str(perm_file)],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0, f"Direct wrapper call failed: {result.stderr}"
    assert perm_file.exists(), "Permutation file not created by direct wrapper call"
    
    # Validate permutation
    perm = np.loadtxt(perm_file, dtype=int)
    assert len(perm) == 3
    assert set(perm) == {1, 2, 3}