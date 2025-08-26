# SMAT Integration Setup

This document describes how to set up and use the SMAT (SMaT) sparse matrix multiplication kernel in the ReorderingSurvey2025 framework.

## About SMAT

SMAT is a sparse matrix multiplication library that utilizes Tensor Cores for unstructured sparse matrices on NVIDIA GPUs. It provides high-performance SpMM operations by leveraging the low-level CUDA MMA (matrix-matrix-accumulate) API.

**Repository**: https://github.com/spcl/smat
**Paper**: [High Performance Unstructured SpMM Computation Using Tensor Cores](https://arxiv.org/pdf/2408.11551)

## Requirements

### Hardware
- NVIDIA GPU with Tensor Core support (A100, RTX 30xx series, etc.)
- Compute capability 8.0+ recommended

### Software
- CUDA Toolkit 12.0+
- GCC 12.3.0+
- gflags library
- NVIDIA Driver 530.30.02+

## Installation

1. **Install system dependencies**:
   ```bash
   sudo apt-get install libgflags-dev
   ```

2. **Build SMAT using bootstrap**:
   ```bash
   # Automated build (recommended)
   ./scripts/bootstrap_smat.sh
   
   # Or specify GPU architecture manually
   ./scripts/bootstrap_smat.sh 80  # For A100
   ./scripts/bootstrap_smat.sh 86  # For RTX 30xx series
   ```

3. **Manual installation** (alternative):
   ```bash
   # Clone SMAT repository
   git clone https://github.com/spcl/smat.git
   cd smat/src/cuda_hgemm
   
   # Build for your GPU architecture (e.g., 80 for A100, 86 for RTX 30xx)
   ./build.sh -a 80 -t Release -b OFF
   ```

4. **Set up environment** (if using manual installation):
   ```bash
   # Option 1: Add to PATH
   export PATH="$PATH:/path/to/smat/output/bin"
   
   # Option 2: Set SMAT_HOME
   export SMAT_HOME="/path/to/smat/output"
   ```

## Usage in ReorderingSurvey2025

Once SMAT is installed, it can be used like any other multiplication kernel:

### Basic Usage
```bash
# Run reordering first
bash Programs/Reorder.sbatch Raw_Matrices/dataset/matrix.mtx identity

# Run SMAT multiplication
bash Programs/Multiply.sbatch Results/Reordering/matrix/identity_default/results.csv smat
```

### With Parameters
```bash
# Custom iterations and multipliers (dimensions auto-detected from matrix)
bash Programs/Multiply.sbatch results.csv smat n_mult=2 profiling_iterations=20

# Override auto-detected dimensions if needed
bash Programs/Multiply.sbatch results.csv smat m=1024 n=1024 k=1024 n_mult=2
```

### Available Parameters
- `n_mult`: N multiplier (n_mult * MMA_N) - default: 1
- `warmup_iterations`: Number of warmup iterations - default: 1
- `profiling_iterations`: Number of profiling iterations - default: 10
- `m`, `n`, `k`: Matrix dimensions (auto-detected from .mtx file if not specified)
- `alpha`, `beta`: Compatibility parameters (not used by SMAT)

## Configuration

SMAT is configured in `config/multiply.yml`:

```yaml
smat:
  gpus: 1
  time: "00:15:00"
  modules: "cuda_cusparse"
  params:
    - n_mult: 1
      warmup_iterations: 1
      profiling_iterations: 10
    - n_mult: 2
      warmup_iterations: 2
      profiling_iterations: 20
```

Matrix dimensions (`m`, `n`, `k`) are automatically detected from the input .mtx file and do not need to be specified in the configuration.

## Troubleshooting

### Binary Not Found
```
Error: SMAT binary (hgemm) not found. Please install SMAT and ensure hgemm is in PATH or set SMAT_HOME.
```
**Solution**: Install SMAT and ensure the `hgemm` binary is accessible.

### CUDA Not Available
```
Warning: CUDA not detected. SMAT requires CUDA for GPU operations.
```
**Solution**: Install CUDA Toolkit and ensure `nvcc` is in PATH.

### Matrix Format Issues
SMAT expects Matrix Market (.mtx) format files. The framework automatically provides reordered matrices in the correct format.

## Performance Notes

- SMAT performs best on matrices with block-sparse structure
- Consider using reordering techniques that improve block density before SMAT multiplication
- Tensor Core utilization depends on matrix dimensions being multiples of specific sizes (16, 32)
- For optimal performance, tune `n_mult`, `warmup_iterations`, and `profiling_iterations` parameters
- Matrix dimensions are automatically detected from the input matrix, no manual tuning needed

## Integration Details

The SMAT integration consists of:
- `scripts/bootstrap_smat.sh`: Automated build script for SMAT
- `Programs/Multiplication/Techniques/operation_smat.sh`: Wrapper script that calls SMAT binary directly
- Configuration in `config/multiply.yml`
- Test suite in `tests/unit/test_multiplication_kernels.py`

Key improvements:
- **Automatic matrix dimension detection**: Matrix dimensions are auto-detected from .mtx files
- **Direct binary execution**: No Python wrapper needed - calls SMAT `hgemm` binary directly
- **Bootstrap integration**: SMAT is built automatically via `./scripts/bootstrap.sh`
- **SMAT-only timing**: Uses only timing provided by SMAT binary, no fallback to system timing

The implementation follows the framework's patterns and provides graceful failure when SMAT is not installed.