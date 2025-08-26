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

2. **Clone and build SMAT**:
   ```bash
   # Clone SMAT repository
   git clone https://github.com/spcl/smat.git
   cd smat/src/cuda_hgemm
   
   # Build for your GPU architecture (e.g., 80 for A100, 86 for RTX 30xx)
   ./build.sh -a 80 -t Release -b OFF
   ```

3. **Set up environment**:
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
# Custom dimensions and iterations
bash Programs/Multiply.sbatch results.csv smat m=1024 n=1024 k=1024 n_mult=2 profiling_iterations=20
```

### Available Parameters
- `m`, `n`, `k`: Matrix dimensions for SpMM (A: m×k, B: k×n, C: m×n)
- `n_mult`: N multiplier (n_mult * MMA_N)
- `warmup_iterations`: Number of warmup iterations (default: 1)
- `profiling_iterations`: Number of profiling iterations (default: 10)
- `alpha`, `beta`: Compatibility parameters (not used by SMAT)

## Configuration

SMAT is configured in `config/multiply.yml`:

```yaml
smat:
  gpus: 1
  time: "00:15:00"
  modules: "cuda_cusparse"
  params:
    - alpha: 1.0
      beta: 0.0
      m: 512
      n: 512
      k: 512
    - alpha: 1.0
      beta: 0.0
      m: 1024
      n: 1024
      k: 1024
      n_mult: 2
```

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
- For optimal performance, tune `m`, `n`, `k` parameters based on your matrix characteristics

## Integration Details

The SMAT integration consists of:
- `scripts/smat.py`: Python interface to SMAT binary
- `Programs/Multiplication/Techniques/operation_smat.sh`: Wrapper script
- Configuration in `config/multiply.yml`
- Test suite in `tests/unit/test_multiplication_kernels.py`

The implementation follows the framework's patterns and provides graceful failure when SMAT is not installed.