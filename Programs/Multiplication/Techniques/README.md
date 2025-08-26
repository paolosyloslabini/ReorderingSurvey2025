# Multiplication Techniques

This directory contains wrapper scripts for sparse matrix multiplication kernels. Each script follows the contract:

```bash
operation_<kernel>.sh <output_directory> [key=value ...]
```

## Available Kernels

- `mock` - Mock multiplication kernel for testing (always succeeds)
- `cucsrspmm` - NVIDIA cuSPARSE CSR SpMM with real GPU implementation and CPU fallback
- `smat` - SMAT (SMaT) Tensor Core-accelerated sparse matrix multiplication

## Wrapper Contract

Each multiplication wrapper must:
1. Accept an output directory as the first argument
2. Find the reordered matrix at `<output_directory>/reordered.mtx`
3. Perform the multiplication operation
4. Accept optional key=value parameters (e.g., alpha=1.0, beta=0.0)
5. Exit with status 0 on success

### cucsrspmm Parameters
- `alpha` - Scalar multiplier for the matrix product (default: 1.0)
- `beta` - Scalar multiplier for the result accumulation (default: 0.0)  
- `force_cpu` - Force CPU implementation even if GPU available (default: false)

### smat Parameters
- `alpha` - Scalar multiplier for the matrix product (default: 1.0, for compatibility)
- `beta` - Scalar multiplier for the result accumulation (default: 0.0, for compatibility)
- `m` - M dimension for SpMM (default: 512)
- `n` - N dimension for SpMM (default: 512)
- `k` - K dimension for SpMM (default: 512)
- `n_mult` - N multiplier (n_mult * MMA_N, default: 1)
- `warmup_iterations` - Number of warmup iterations (default: 1)
- `profiling_iterations` - Number of profiling iterations (default: 10)

The timing and other metrics are handled by the calling script (`Multiply.sbatch`).

## Adding New Kernels

1. Create `operation_<name>.sh` following the contract above
2. Make the script executable: `chmod +x operation_<name>.sh`
3. Add the kernel to `config/multiply.yml`
4. Update `TOOLS.md` with kernel details

## Implementation Notes

- The `mock` kernel is useful for testing the pipeline without requiring actual GPU libraries
- The `cucsrspmm` implementation now features:
  - Real GPU computation using CuPy/cuSPARSE when available
  - Comprehensive GPU environment detection (CUDA runtime, cuSPARSE libraries, nvidia-smi)
  - Graceful fallback to CPU-based sparse matrix multiplication when GPU unavailable
  - Support for alpha/beta parameters and force_cpu option
  - Proper error handling and performance measurement
- Consider adding proper error handling and performance measurement to new kernels
