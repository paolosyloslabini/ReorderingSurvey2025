#!/usr/bin/env python3
"""
Test for AMD (Approximate Minimum Degree) reordering implementation.
"""

import pytest
import numpy as np
import tempfile
import subprocess
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.absolute()
SCRIPT_PATH = PROJECT_ROOT / "Programs" / "Reordering" / "Techniques" / "reordering_amd.sh"


def test_amd_script_exists():
    """Test that the AMD script exists and is executable."""
    assert SCRIPT_PATH.exists(), f"AMD script not found at {SCRIPT_PATH}"
    assert os.access(SCRIPT_PATH, os.X_OK), f"AMD script not executable at {SCRIPT_PATH}"


def test_amd_basic_functionality():
    """Test basic AMD functionality with a simple symmetric matrix."""
    # Create a test matrix (4x4 symmetric)
    matrix_content = """%%MatrixMarket matrix coordinate real symmetric
4 4 6
1 1 4.0
2 1 1.0
2 2 3.0
3 2 2.0
3 3 2.0
4 4 1.0"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        matrix_file = os.path.join(tmpdir, "test.mtx")
        perm_file = os.path.join(tmpdir, "perm.txt")
        
        # Write test matrix
        with open(matrix_file, "w") as f:
            f.write(matrix_content)
        
        # Run AMD reordering
        result = subprocess.run([
            str(SCRIPT_PATH), matrix_file, perm_file
        ], capture_output=True, text=True, cwd=PROJECT_ROOT)
        
        assert result.returncode == 0, f"AMD script failed: {result.stderr}"
        assert os.path.exists(perm_file), "Permutation file was not created"
        
        # Check permutation format
        perm = np.loadtxt(perm_file, dtype=int)
        assert len(perm) == 4, f"Expected 4 elements, got {len(perm)}"
        assert set(perm) == {1, 2, 3, 4}, f"Invalid permutation: {perm}"
        assert "AMD ordering completed successfully" in result.stderr


def test_amd_empty_matrix():
    """Test AMD behavior with edge cases."""
    # Test 1x1 matrix
    matrix_content = """%%MatrixMarket matrix coordinate real general
1 1 1
1 1 1.0"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        matrix_file = os.path.join(tmpdir, "test.mtx")
        perm_file = os.path.join(tmpdir, "perm.txt")
        
        with open(matrix_file, "w") as f:
            f.write(matrix_content)
        
        result = subprocess.run([
            str(SCRIPT_PATH), matrix_file, perm_file
        ], capture_output=True, text=True, cwd=PROJECT_ROOT)
        
        assert result.returncode == 0, f"AMD script failed: {result.stderr}"
        
        perm = np.loadtxt(perm_file, dtype=int)
        perm = np.atleast_1d(perm)  # Ensure it's an array even for single values
        assert len(perm) == 1
        assert perm[0] == 1


def test_amd_invalid_matrix():
    """Test AMD error handling with non-square matrix."""
    matrix_content = """%%MatrixMarket matrix coordinate real general
3 4 3
1 1 1.0
2 2 2.0
3 3 3.0"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        matrix_file = os.path.join(tmpdir, "test.mtx")
        perm_file = os.path.join(tmpdir, "perm.txt")
        
        with open(matrix_file, "w") as f:
            f.write(matrix_content)
        
        result = subprocess.run([
            str(SCRIPT_PATH), matrix_file, perm_file
        ], capture_output=True, text=True, cwd=PROJECT_ROOT)
        
        assert result.returncode != 0, "AMD should fail for non-square matrix"
        assert "Matrix must be square" in result.stderr


def test_amd_larger_matrix():
    """Test AMD with a slightly larger matrix to verify it handles real computation."""
    # Create a 5x5 symmetric matrix with some structure
    matrix_content = """%%MatrixMarket matrix coordinate real symmetric
5 5 9
1 1 2.0
2 1 1.0
2 2 3.0
3 2 1.0
3 3 4.0
4 3 1.0
4 4 2.0
5 4 1.0
5 5 1.0"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        matrix_file = os.path.join(tmpdir, "test.mtx")
        perm_file = os.path.join(tmpdir, "perm.txt")
        
        with open(matrix_file, "w") as f:
            f.write(matrix_content)
        
        result = subprocess.run([
            str(SCRIPT_PATH), matrix_file, perm_file
        ], capture_output=True, text=True, cwd=PROJECT_ROOT)
        
        assert result.returncode == 0, f"AMD script failed: {result.stderr}"
        
        perm = np.loadtxt(perm_file, dtype=int)
        assert len(perm) == 5
        assert set(perm) == {1, 2, 3, 4, 5}


if __name__ == "__main__":
    pytest.main([__file__])