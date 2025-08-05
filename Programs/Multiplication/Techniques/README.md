# Multiplication Techniques

This directory contains wrapper scripts for sparse matrix multiplication kernels. Each script follows the contract:

```bash
operation_<kernel>.sh <output_directory> [key=value ...]
```

## Available Kernels

- `mock` - Mock multiplication kernel for testing (always succeeds)
- `cucsrspmm` - NVIDIA cuSPARSE CSR SpMM (placeholder implementation)

## Wrapper Contract

Each multiplication wrapper must:
1. Accept an output directory as the first argument
2. Find the reordered matrix at `<output_directory>/reordered.mtx`
3. Perform the multiplication operation
4. Accept optional key=value parameters (e.g., alpha=1.0, beta=0.0)
5. Exit with status 0 on success

The timing and other metrics are handled by the calling script (`Multiply.sbatch`).

## Adding New Kernels

1. Create `operation_<name>.sh` following the contract above
2. Make the script executable: `chmod +x operation_<name>.sh`
3. Add the kernel to `config/multiply.yml`
4. Update `TOOLS.md` with kernel details

## Implementation Notes

- The `mock` kernel is useful for testing the pipeline without requiring actual GPU libraries
- The `cucsrspmm` implementation is currently a placeholder and needs to be completed with actual cuSPARSE calls
- Consider adding proper error handling and performance measurement to new kernels
