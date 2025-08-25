# ReorderingSurvey2025: Sparse Matrix Reordering Framework

**ALWAYS reference these instructions first. Only search for additional information or run bash commands when you encounter information that does not match what is documented here.**

## Working Effectively

### Bootstrap and Build
- Install Python dependencies: `pip install -r requirements.txt` -- takes 30 seconds
- Install system dependencies (Ubuntu/Debian): `sudo apt-get install -y libboost-dev libnuma-dev google-perftools libgoogle-perftools-dev`
- Install pytest: `pip install pytest`
- Run bootstrap script: `./scripts/bootstrap.sh` -- **EXPECTED TO FAIL** in most environments due to Rabbit Order C++ compatibility issues. This is normal and does not prevent core functionality.

### Testing and Validation  
- Run full test suite: `python -m pytest tests/ -v` -- takes 8 seconds. NEVER CANCEL. All 13 tests should pass.
- Test module loading: `bash tests/test_module_loading.sh` -- takes <1 second, expects warnings about missing CUDA
- **NEVER CANCEL BUILD OR TEST COMMANDS** - Set timeouts to 60+ minutes for builds, 30+ minutes for tests

### Core Pipeline Operations
Always run these commands from the repository root:

#### Reordering Phase
```bash
# Basic identity reordering (always works)
export RESULTS_DIR=/tmp/results
bash Programs/Reorder.sbatch <matrix.mtx> identity

# RCM reordering (works with SciPy)
bash Programs/Reorder.sbatch <matrix.mtx> rcm
bash Programs/Reorder.sbatch <matrix.mtx> rcm symmetric=true

# Rabbit Order (WILL FAIL without proper C++ build)
bash Programs/Reorder.sbatch <matrix.mtx> ro
```

#### Multiplication Phase
```bash
# Mock multiplication (always works)
bash Programs/Multiply.sbatch <results.csv> mock alpha=1.0

# cuSPARSE multiplication (requires CUDA)
bash Programs/Multiply.sbatch <results.csv> cucsrspmm alpha=1.0 beta=0.0
```

### Timing Expectations
- Python dependency installation: 30 seconds  
- Test suite execution: 8 seconds
- Module loading test: <1 second
- Reordering operations: 1-2 seconds for small matrices
- Multiplication operations: <1 second for small matrices
- Bootstrap script: 1-3 seconds (fails compilation but completes quickly)

## Validation Scenarios

### Complete End-to-End Validation
After making changes, ALWAYS run this complete scenario:

```bash
# 1. Create test matrix
mkdir -p /tmp/sample_data
cat > /tmp/sample_data/test.mtx << 'EOF'
%%MatrixMarket matrix coordinate real general
4 4 4
1 1 1.0
2 2 2.0
3 3 3.0
4 4 4.0
EOF

# 2. Copy to proper location
mkdir -p Raw_Matrices/sample_data
cp /tmp/sample_data/test.mtx Raw_Matrices/sample_data/

# 3. Run reordering
export RESULTS_DIR=/tmp/validation_results
bash Programs/Reorder.sbatch Raw_Matrices/sample_data/test.mtx identity

# 4. Verify reordering output
ls -la $RESULTS_DIR/Reordering/test/identity_default/
cat $RESULTS_DIR/Reordering/test/identity_default/results.csv

# 5. Run multiplication  
bash Programs/Multiply.sbatch $RESULTS_DIR/Reordering/test/identity_default/results.csv mock

# 6. Verify complete pipeline
cat $RESULTS_DIR/Multiplication/test/identity_default/mock/results.csv
```

**Expected result**: Both CSV files should contain complete data rows with timing metrics and no errors.

## Directory Structure and Navigation

### Key Locations
- `Programs/Reorder.sbatch` - Main reordering driver (SLURM script, also works directly)
- `Programs/Multiply.sbatch` - Main multiplication driver  
- `Programs/Reordering/Techniques/` - Reordering algorithm wrappers (reordering_*.sh)
- `Programs/Multiplication/Techniques/` - Multiplication kernel wrappers (operation_*.sh)
- `config/` - YAML configuration files for techniques and parameters
- `config/modules/` - Module definition files for dependency management
- `scripts/` - Helper utilities and launch scripts
- `tests/` - Test suite (pytest-based)
- `Raw_Matrices/` - Input matrix storage location
- `Results/` - Output storage for reordered matrices and CSV results

### Configuration Files
- `config/reorder.yml` - Defines available reordering techniques and parameters
- `config/multiply.yml` - Defines available multiplication kernels and parameters  
- `config/sbatch.yml` - SLURM job configuration defaults
- `requirements.txt` - Python package dependencies

## Implementation Status and Techniques

### Working Reordering Techniques
- `identity` - ✅ Identity permutation (testing/baseline)
- `rcm` - ✅ Reverse Cuthill-McKee (via SciPy) 
- `ro` - ❌ Rabbit Order (C++ build issues, wrapper exists)

### Working Multiplication Kernels  
- `mock` - ✅ Mock kernel with simulated timing (always works)
- `cucsrspmm` - ❌ cuSPARSE CSR SpMM (requires CUDA environment)

### Module Loading System
The framework automatically loads required dependencies:
- `basic` - Minimal dependencies (always available)
- `python_scipy` - Python + SciPy/NumPy for matrix operations
- `cuda_cusparse` - CUDA environment for GPU operations  
- `metis` - METIS library for graph partitioning (planned)

Test module loading with: `bash tests/test_module_loading.sh`

## Common Tasks and Commands

### Adding New Reordering Technique
1. Create `Programs/Reordering/Techniques/reordering_<name>.sh` following the contract:
   ```bash
   #!/usr/bin/env bash
   # reordering_<name>.sh <matrix.mtx> <permutation.g> [key=value ...]
   ```
2. Add entry to `config/reorder.yml` with module requirements
3. Update `TOOLS.md` status table
4. Add test case in `tests/`

### Adding New Multiplication Kernel  
1. Create `Programs/Multiplication/Techniques/operation_<name>.sh` following the contract:
   ```bash
   #!/usr/bin/env bash  
   # operation_<name>.sh <output_directory> [key=value ...]
   ```
2. Add entry to `config/multiply.yml` with module requirements
3. Update `TOOLS.md` status table
4. Add test case in `tests/`

### Debugging Pipeline Issues
1. Check module loading: `source Programs/load_modules.sh <type> <technique>`
2. Test wrapper directly: `bash Programs/Reordering/Techniques/reordering_<name>.sh <args>`
3. Verify CSV output format matches expected schema (see `AGENTS.md` section 4)
4. Check file permissions: all `.sh` files must be executable

## Known Issues and Workarounds

### Build and Dependencies
- **Rabbit Order compilation fails**: Normal in sandboxed environments. Requires Boost ≥1.58.0, libnuma ≥2.0.9, tcmalloc. Install system dependencies first: `sudo apt-get install -y libboost-dev libnuma-dev google-perftools`
- **CUDA tools not available**: Expected in environments without GPU. Module loading will show warnings but continue.
- **Missing pytest**: Install with `pip install pytest`

### Pipeline Execution
- **Matrix file not found in multiplication phase**: Ensure matrix exists in `Raw_Matrices/<dataset>/<matrix>.mtx` path
- **Permission denied on wrapper scripts**: Run `chmod +x Programs/*/Techniques/*.sh`
- **Empty permutation files**: Check wrapper script exit codes and error messages

### Common Error Patterns
- **"Wrapper not found"**: Script missing or not executable in `Programs/*/Techniques/`
- **"CSV not found"**: Reordering phase must complete successfully before multiplication
- **"Module load failed"**: Normal if module system unavailable, framework continues with warnings

## Validation Requirements

### Before Committing Changes
Always run and validate:
1. `python -m pytest tests/ -v` - All 13 tests must pass
2. Complete end-to-end validation scenario (above)
3. `bash tests/test_module_loading.sh` - Should complete with warnings only
4. Check that new techniques work with both small and larger test matrices

### Performance and Timing
- Small matrices (4x4): Reordering <2s, Multiplication <1s
- Larger matrices (10x10): Reordering <3s, Multiplication <2s  
- Test suite: 8 seconds total
- Module loading: <1 second per technique

## Environment Variables

### Required for Pipeline Operation
- `PROJECT_ROOT` - Automatically set by `Programs/exp_config.sh`
- `RESULTS_DIR` - Override default `Results/` directory (use `/tmp/results` for testing)
- `MATRIX_DIR` - Override default `Raw_Matrices/` directory

### Optional for Module System
- `PYTHONPATH` - Extended automatically by python_scipy module set
- `CUDA_VISIBLE_DEVICES` - Set by cuda_cusparse module set  
- `LD_LIBRARY_PATH` - Extended for CUDA libraries when available

## Architecture Notes

This is a **Slurm-based HPC framework** for benchmarking sparse matrix reordering algorithms. The core design supports:

- **Heterogeneous compute nodes**: CPU techniques vs GPU techniques  
- **Modular technique integration**: Drop-in wrappers for new algorithms
- **Automated dependency management**: Module loading system handles environment setup
- **Reproducible experiments**: Pinned commits, seeded algorithms, comprehensive logging
- **Result aggregation**: CSV-based output for downstream analysis

The framework works both in SLURM environments and standalone for development/testing.