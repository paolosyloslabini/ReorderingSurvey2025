#!/usr/bin/env python3
"""Tests for GraphBLAS integration"""

import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def test_graphblas_csv_helper():
    """Test that GraphBLAS csv_helper produces correct results"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test matrix
        matrix = tmpdir / "test.mtx"
        matrix.write_text("""%%MatrixMarket matrix coordinate real general
4 4 6
1 1 1.0
1 2 2.0
2 2 3.0
3 3 4.0
4 3 5.0
4 4 6.0""")
        
        # Create test CSV
        csv = tmpdir / "results.csv"
        csv.write_text("""matrix_name,reorder_tech,exit_code
test,identity,0""")
        
        # Run GraphBLAS csv_helper
        result = subprocess.run([
            "python", "scripts/csv_helper_graphblas.py",
            str(matrix), str(csv)
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        
        # Check results
        df = pd.read_csv(csv)
        assert "bandwidth" in df.columns
        assert "block_density" in df.columns
        assert df.loc[0, "bandwidth"] >= 0  # Should have valid bandwidth


def test_graphblas_reorder_matrix():
    """Test that GraphBLAS reorder_matrix works correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test matrix
        matrix = tmpdir / "test.mtx"
        matrix.write_text("""%%MatrixMarket matrix coordinate real general
3 3 3
1 1 1.0
2 2 2.0
3 3 3.0""")
        
        # Create identity permutation
        perm = tmpdir / "perm.g"
        perm.write_text("1\n2\n3\n")
        
        # Create output path
        output = tmpdir / "reordered.mtx"
        
        # Run GraphBLAS reorder
        result = subprocess.run([
            "python", "scripts/reorder_matrix_graphblas.py",
            str(matrix), str(perm), "1D", str(output)
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert output.exists()
        
        # Check that output is valid Matrix Market format
        content = output.read_text()
        assert "%%MatrixMarket" in content


def test_hybrid_csv_helper_uses_graphblas():
    """Test that hybrid csv_helper uses GraphBLAS when available"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test matrix
        matrix = tmpdir / "test.mtx"
        matrix.write_text("""%%MatrixMarket matrix coordinate real general
2 2 2
1 1 1.0
2 2 1.0""")
        
        # Create test CSV
        csv = tmpdir / "results.csv"
        csv.write_text("""matrix_name,reorder_tech,exit_code
test,identity,0""")
        
        # Run hybrid csv_helper
        result = subprocess.run([
            "python", "scripts/csv_helper.py",
            str(matrix), str(csv)
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Using GraphBLAS backend" in result.stdout
        
        # Check results are valid
        df = pd.read_csv(csv)
        assert "bandwidth" in df.columns
        assert "block_density" in df.columns


def test_graphblas_module_configuration():
    """Test that GraphBLAS module configuration exists and is valid"""
    config_path = Path("config/modules/python_graphblas.yml")
    assert config_path.exists()
    
    import yaml
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    assert config["name"] == "python_graphblas"
    assert "python/3.11" in config["modules"]
    assert "post_load" in config


def test_rcm_graphblas_technique_exists():
    """Test that RCM GraphBLAS technique is properly configured"""
    # Check reorder configuration
    config_path = Path("config/reorder.yml")
    import yaml
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    assert "rcm_graphblas" in config
    assert config["rcm_graphblas"]["modules"] == "python_graphblas"
    
    # Check technique script exists and is executable
    script_path = Path("Programs/Reordering/Techniques/reordering_rcm_graphblas.sh")
    assert script_path.exists()
    assert os.access(script_path, os.X_OK)


if __name__ == "__main__":
    pytest.main([__file__])