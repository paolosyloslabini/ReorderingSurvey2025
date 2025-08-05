# Programs Directory

This directory contains the main Slurm batch scripts and technique wrappers for the reordering and multiplication pipeline.

## Structure

- `Reorder.sbatch` - Main driver for reordering experiments
- `Multiply.sbatch` - Main driver for multiplication experiments  
- `exp_config.sh` - Environment configuration and path setup
- `Reordering/` - Reordering technique implementations
- `Multiplication/` - Sparse multiplication kernel implementations

## Usage

### Reordering
```bash
sbatch Programs/Reorder.sbatch <matrix.mtx> <technique> [key=value ...]
```

### Multiplication
```bash
sbatch Programs/Multiply.sbatch <reordering_results.csv> <kernel> [key=value ...]
```

## Configuration

Runtime paths are configured in `exp_config.sh`. Set the `MATRIX_DIR` and `RESULTS_DIR` environment variables before sourcing it if you want to store the dataset or experiment output outside the repository.

## Adding New Techniques

1. Create a wrapper script in the appropriate `Techniques/` directory
2. Follow the naming convention: `reordering_<name>.sh` or `operation_<name>.sh`
3. Register the technique in the corresponding YAML config file
4. Update `TOOLS.md` with the technique description
