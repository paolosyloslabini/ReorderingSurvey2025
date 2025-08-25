import os
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def test_rcm_reorder_basic(tmp_path):
    """Test RCM reordering with a basic connected matrix"""
    # Create a simple 5x5 tridiagonal matrix that RCM can meaningfully reorder
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
        ["bash", "Programs/Reorder.sbatch", str(mtx), "rcm"],
        capture_output=True,
        text=True,
        env=env,
    )

    # Check that the command succeeded
    assert result.returncode == 0, f"RCM command failed with stderr: {result.stderr}"

    # Verify that the permutation and results CSV were produced
    out_dir = results_dir / "Reordering" / "matrix" / "rcm_default"
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
    assert df.loc[0, "reorder_tech"] == "rcm"
    assert df.loc[0, "exit_code"] == 0
    assert df.loc[0, "reorder_time_ms"] >= 0


def test_rcm_reorder_larger_matrix(tmp_path):
    """Test RCM reordering with a larger structured matrix"""
    # Create a 6x6 grid-like matrix structure that benefits from RCM
    # This represents a small grid graph
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    mtx = dataset / "matrix.mtx"
    mtx.write_text(
        """%%MatrixMarket matrix coordinate real general
6 6 16
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
5 6 1
6 5 1
6 6 1
"""
    )

    # Run the reordering driver
    env = os.environ.copy()
    results_dir = tmp_path / "results"
    env["RESULTS_DIR"] = str(results_dir)
    subprocess.run(
        ["bash", "Programs/Reorder.sbatch", str(mtx), "rcm"],
        check=True,
        env=env,
    )

    # Verify outputs
    out_dir = results_dir / "Reordering" / "matrix" / "rcm_default"
    perm_file = out_dir / "permutation.g"
    
    # Read and validate the permutation
    perm = np.loadtxt(perm_file, dtype=int)
    assert len(perm) == 6, f"Expected permutation length 6, got {len(perm)}"
    assert set(perm) == {1, 2, 3, 4, 5, 6}, f"Permutation should be a valid reordering of 1-6, got {perm}"
    
    # Check that it's not the identity permutation (RCM should reorder this matrix)
    assert not np.array_equal(perm, [1, 2, 3, 4, 5, 6]), "RCM should produce a non-identity reordering for this matrix"


def test_rcm_reorder_with_parameters(tmp_path):
    """Test RCM reordering with custom parameters"""
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
        ["bash", "Programs/Reorder.sbatch", str(mtx), "rcm", "symmetric=false"],
        capture_output=True,
        text=True,
        env=env,
    )

    # Check that the command succeeded
    assert result.returncode == 0, f"RCM with parameters failed with stderr: {result.stderr}"

    # Verify outputs with parameter set ID
    out_dir = results_dir / "Reordering" / "matrix" / "rcm_symmetric-false"
    assert (out_dir / "permutation.g").exists()
    assert (out_dir / "results.csv").exists()
    
    # Verify the parameter set is recorded in CSV
    df = pd.read_csv(out_dir / "results.csv")
    assert df.loc[0, "reord_param_set"] == "symmetric=false"


def test_rcm_reorder_disconnected_matrix(tmp_path):
    """Test RCM reordering with a disconnected matrix (multiple components)"""
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
        ["bash", "Programs/Reorder.sbatch", str(mtx), "rcm"],
        check=True,
        env=env,
    )

    # Verify outputs - RCM should handle disconnected components gracefully
    out_dir = results_dir / "Reordering" / "matrix" / "rcm_default"
    perm_file = out_dir / "permutation.g"
    
    # Read and validate the permutation
    perm = np.loadtxt(perm_file, dtype=int)
    assert len(perm) == 6, f"Expected permutation length 6, got {len(perm)}"
    assert set(perm) == {1, 2, 3, 4, 5, 6}, f"Permutation should be a valid reordering of 1-6, got {perm}"
    
    # Verify successful completion
    df = pd.read_csv(out_dir / "results.csv")
    assert df.loc[0, "exit_code"] == 0