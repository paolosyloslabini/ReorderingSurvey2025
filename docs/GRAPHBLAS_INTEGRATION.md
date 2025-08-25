# GraphBLAS Integration

This document describes the GraphBLAS integration in the ReorderingSurvey2025 framework, which provides significant performance improvements for large sparse matrix operations.

## Overview

The framework now supports SuiteSparse GraphBLAS as an alternative to SciPy for matrix operations. GraphBLAS provides better performance and memory efficiency, especially for large sparse matrices, by avoiding costly format conversions and leveraging optimized sparse matrix operations.

## Key Components

### 1. Matrix I/O and Reordering
- **`scripts/reorder_matrix.py`**: GraphBLAS implementation for matrix permutation (default)
- **`scripts/reorder_matrix_scipy.py`**: SciPy-based implementation (for compatibility)

### 2. Structural Metrics Calculation
- **`scripts/csv_helper.py`**: GraphBLAS implementation for computing bandwidth and block densities (default)
- **`scripts/csv_helper_scipy.py`**: SciPy-based implementation (for compatibility)

### 3. Module Configuration
- **`config/modules/python_graphblas.yml`**: Module definition for GraphBLAS-based techniques
- **`config/reorder.yml`**: Updated to include GraphBLAS-based technique variants

### 4. Reordering Techniques
- **`Programs/Reordering/Techniques/reordering_rcm_graphblas.sh`**: GraphBLAS-optimized RCM implementation

## Performance Benefits

### Large Matrix Efficiency
GraphBLAS provides significant advantages for large matrices (>100,000 entries):
- **Memory efficiency**: Avoids intermediate format conversions (CSR → COO → CSR)
- **Optimized operations**: Native sparse matrix operations without dense intermediate arrays
- **Parallel execution**: Built-in parallelization for matrix operations

### Automatic Backend Selection
GraphBLAS is now the default for matrix operations:
```python
# Uses GraphBLAS for efficient sparse matrix operations
A = read_mm(matrix_path)  # Uses GraphBLAS I/O
bandwidth = compute_bandwidth(A)  # Uses GraphBLAS operations
```

SciPy versions are preserved for compatibility in `*_scipy.py` files when needed.

## Usage

### Running GraphBLAS-optimized Reordering
```bash
# Use GraphBLAS-optimized RCM
sbatch Programs/Reorder.sbatch matrix.mtx rcm_graphblas

# Standard approach (now uses GraphBLAS by default)
sbatch Programs/Reorder.sbatch matrix.mtx rcm
```

### Direct Script Usage
```bash
# GraphBLAS matrix reordering (default)
python scripts/reorder_matrix.py matrix.mtx perm.g 2D output.mtx

# GraphBLAS structural metrics (default)
python scripts/csv_helper.py matrix.mtx results.csv

# SciPy versions (for compatibility when needed)
python scripts/reorder_matrix_scipy.py matrix.mtx perm.g 2D output.mtx
python scripts/csv_helper_scipy.py matrix.mtx results.csv
```

## Backward Compatibility

GraphBLAS is now the default implementation:
- All existing scripts and configurations work unchanged
- SciPy implementations are preserved in `*_scipy.py` files for compatibility when GraphBLAS is not available
- Existing technique implementations are unaffected

## Configuration

### Module Requirements
GraphBLAS-based techniques specify their module requirements:
```yaml
rcm_graphblas:
  type: "2D"
  modules: "python_graphblas"  # Loads GraphBLAS environment
  params:
    - symmetric: true
```

### Dependencies
The GraphBLAS integration requires:
- `python-graphblas` package (included in requirements.txt)
- SuiteSparse GraphBLAS library (automatically installed with python-graphblas)

## Technical Details

### Matrix Market I/O
- **GraphBLAS**: Uses native `graphblas.io.mmread/mmwrite` for optimal performance
- **SciPy fallback**: Maintains compatibility with existing Matrix Market files

### Coordinate Extraction
- **GraphBLAS**: Uses `Matrix.to_coo()` for efficient coordinate access
- **SciPy**: Uses traditional `.tocoo()` conversion

### Permutation Application
- **GraphBLAS**: Leverages native slicing operations `A[idx, :][:, idx]`
- **SciPy**: Uses traditional matrix indexing with format conversions

## Testing

Comprehensive tests ensure correctness and compatibility:
```bash
# Run GraphBLAS-specific tests
python -m pytest tests/test_graphblas_integration.py -v

# Run all tests (includes GraphBLAS and compatibility tests)
python -m pytest tests/ -v
```

## Future Extensions

The GraphBLAS integration provides a foundation for:
- GPU-accelerated matrix operations (when SuiteSparse GraphBLAS GPU support is available)
- Advanced graph algorithms for reordering (e.g., spectral methods)
- Distributed sparse matrix operations for very large datasets