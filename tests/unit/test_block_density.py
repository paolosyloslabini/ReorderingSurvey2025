"""Unit tests for block density calculations."""

import numpy as np
import pytest
import scipy.sparse
from pathlib import Path
import sys
import os

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.csv_helper_scipy import block_metrics


class TestBlockDensity:
    """Test block density calculations."""
    
    def test_identity_matrix_block_density(self):
        """Test block density calculation for identity matrix."""
        # Create 4x4 identity matrix
        matrix = scipy.sparse.eye(4, format='coo')
        
        # Test different block sizes
        # For identity matrix: block density = nnz / (num_nonzero_blocks * block_size^2)
        
        # Block size 1: each nonzero is in its own block
        # 4 nonzeros in 4 blocks of size 1x1 each = 4/4 = 1.0
        density = block_metrics(matrix, 1)
        assert abs(density - 1.0) < 1e-10
        
        # Block size 2: 4 nonzeros in 2 blocks of size 2x2 each = 4/8 = 0.5
        density = block_metrics(matrix, 2)
        assert abs(density - 0.5) < 1e-10
        
        # Block size 4: 4 nonzeros in 1 block of size 4x4 = 4/16 = 0.25
        density = block_metrics(matrix, 4)
        assert abs(density - 0.25) < 1e-10
    
    def test_mixed_pattern_matrix_block_density(self):
        """Test block density with a more complex pattern."""
        # Create test matrix with known pattern
        rows = [0, 1, 2, 3, 0, 1]  
        cols = [0, 1, 2, 3, 4, 5]
        data = [1.0] * len(rows)
        matrix = scipy.sparse.coo_matrix((data, (rows, cols)), shape=(8, 8))
        
        # Block size 2: 6 nonzeros in 3 blocks of size 2x2 each = 6/12 = 0.5
        density = block_metrics(matrix, 2)
        assert abs(density - 0.5) < 1e-10
        
        # Block size 4: 6 nonzeros in 2 blocks of size 4x4 each = 6/32 = 0.1875
        density = block_metrics(matrix, 4)
        assert abs(density - 0.1875) < 1e-10
        
        # Block size 8: 6 nonzeros in 1 block of size 8x8 = 6/64 = 0.09375
        density = block_metrics(matrix, 8)
        assert abs(density - 0.09375) < 1e-10
    
    def test_empty_matrix_block_density(self):
        """Test block density for empty matrix."""
        matrix = scipy.sparse.coo_matrix(([], ([], [])), shape=(4, 4))
        
        for block_size in [1, 2, 4]:
            density = block_metrics(matrix, block_size)
            assert density == 0.0
    
    def test_single_element_matrix_block_density(self):
        """Test block density for matrix with single nonzero."""
        matrix = scipy.sparse.coo_matrix(([1.0], ([0], [0])), shape=(4, 4))
        
        # Block size 1: 1 nonzero in 1 block of size 1x1 = 1/1 = 1.0
        density = block_metrics(matrix, 1)
        assert abs(density - 1.0) < 1e-10
        
        # Block size 2: 1 nonzero in 1 block of size 2x2 = 1/4 = 0.25
        density = block_metrics(matrix, 2)
        assert abs(density - 0.25) < 1e-10
        
        # Block size 4: 1 nonzero in 1 block of size 4x4 = 1/16 = 0.0625
        density = block_metrics(matrix, 4)
        assert abs(density - 0.0625) < 1e-10
    
    def test_full_block_matrix_block_density(self):
        """Test block density for a matrix where entire blocks are filled."""
        # Create a 4x4 matrix where the upper-left 2x2 block is completely filled
        rows = [0, 0, 1, 1]
        cols = [0, 1, 0, 1] 
        data = [1.0] * 4
        matrix = scipy.sparse.coo_matrix((data, (rows, cols)), shape=(4, 4))
        
        # Block size 2: 4 nonzeros in 1 block of size 2x2 = 4/4 = 1.0
        density = block_metrics(matrix, 2)
        assert abs(density - 1.0) < 1e-10
        
        # Block size 4: 4 nonzeros in 1 block of size 4x4 = 4/16 = 0.25  
        density = block_metrics(matrix, 4)
        assert abs(density - 0.25) < 1e-10
    
    def test_regression_no_always_one_density(self):
        """Regression test: ensure block density doesn't always return 1.0."""
        # This was the original problem - all block sizes returned 1.0
        matrix = scipy.sparse.eye(8, format='coo')
        
        densities = []
        for block_size in [1, 2, 4, 8]:
            density = block_metrics(matrix, block_size)
            densities.append(density)
        
        # Assert that not all densities are 1.0
        assert not all(abs(d - 1.0) < 1e-10 for d in densities), \
            f"All densities are 1.0: {densities}, which indicates the bug is not fixed"
        
        # Assert that they are decreasing (larger blocks have lower density for identity matrix)
        for i in range(1, len(densities)):
            assert densities[i] <= densities[i-1], \
                f"Densities should be non-increasing: {densities}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])