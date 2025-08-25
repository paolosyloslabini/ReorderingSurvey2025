# GraphBLAS Integration

This document describes the GraphBLAS integration in the ReorderingSurvey2025 framework, which provides significant performance improvements for large sparse matrix operations.

## Overview

The framework now supports SuiteSparse GraphBLAS as an alternative to SciPy for matrix operations. GraphBLAS provides better performance and memory efficiency, especially for large sparse matrices, by avoiding costly format conversions and leveraging optimized sparse matrix operations.

## Key Components

### 1. Matrix I/O and Reordering
- **`scripts/reorder_matrix_graphblas.py`**: Pure GraphBLAS implementation for matrix permutation
- **`scripts/reorder_matrix.py`**: Hybrid implementation that automatically uses GraphBLAS when available

### 2. Structural Metrics Calculation
- **`scripts/csv_helper_graphblas.py`**: Pure GraphBLAS implementation for computing bandwidth and block densities
- **`scripts/csv_helper.py`**: Enhanced hybrid implementation that automatically detects and uses GraphBLAS

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
The hybrid implementations automatically choose the best backend:
```python
# Automatically uses GraphBLAS if available, falls back to SciPy
A = read_mm(matrix_path)  # Uses GraphBLAS I/O when possible
bandwidth = compute_bandwidth(A)  # Uses GraphBLAS operations when possible
```

## Usage

### Running GraphBLAS-optimized Reordering
```bash
# Use GraphBLAS-optimized RCM
sbatch Programs/Reorder.sbatch matrix.mtx rcm_graphblas

# Hybrid approach (automatically uses GraphBLAS when available)
sbatch Programs/Reorder.sbatch matrix.mtx rcm
```

### Direct Script Usage
```bash
# Pure GraphBLAS matrix reordering
python scripts/reorder_matrix_graphblas.py matrix.mtx perm.g 2D output.mtx

# Pure GraphBLAS structural metrics
python scripts/csv_helper_graphblas.py matrix.mtx results.csv

# Hybrid approach (recommended)
python scripts/csv_helper.py matrix.mtx results.csv
```

## Backward Compatibility

The integration maintains full backward compatibility:
- All existing scripts and configurations continue to work unchanged
- SciPy implementations remain as fallbacks when GraphBLAS is not available
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