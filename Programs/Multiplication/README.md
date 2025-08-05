# Multiplication

Wrapper scripts for sparse multiplication kernels. Each implementation is named `operation_<impl>.sh` and takes a reordered matrix directory and parameter list.

## Available Implementations

### cucsrspmm - NVIDIA cuSPARSE CSR SpMM

Implementation of sparse matrix-matrix multiplication using NVIDIA cuSPARSE CSR format.

**Requirements:**
- NVIDIA GPU with CUDA Compute Capability 6.0 or higher
- CUDA toolkit 11.0 or later
- cuSPARSE library (included with CUDA toolkit)

**Parameters:**
- `alpha`: Scalar multiplier for A*B (default: 1.0)
- `beta`: Scalar multiplier for C (default: 0.0)
- `num_cols_B`: Number of columns in dense matrix B (default: 64)

**Building:**
The cuSPARSE implementation is automatically built when first used. To build manually:
```bash
cd Programs/Multiplication
make clean && make
```

**Testing CUDA Environment:**
```bash
cd Programs/Multiplication
make test-env
```

### mock - Mock multiplication (for testing)

Simple mock implementation that simulates multiplication with random timing.

**Parameters:**
- `alpha`: Scalar parameter (for testing parameter passing)

## Usage Examples

```bash
# cuSPARSE with default parameters
sbatch Programs/Multiply.sbatch results.csv cucsrspmm

# cuSPARSE with custom parameters
sbatch Programs/Multiply.sbatch results.csv cucsrspmm alpha=2.0 beta=1.0 num_cols_B=128

# Mock multiplication
sbatch Programs/Multiply.sbatch results.csv mock alpha=1.0
```

## Output Format

All multiplication kernels update the results CSV with timing and performance metrics:
- `mult_type`: Implementation name
- `mult_param_set`: Semicolon-separated parameter list
- `mult_time_ms`: Execution time in milliseconds
- `gflops`: Performance in GFLOPS (for cuSPARSE)
- `mult_metrics`: Additional implementation-specific metrics
- `exit_code`: 0 for success, non-zero for failure
- `timestamp`: ISO-8601 timestamp
