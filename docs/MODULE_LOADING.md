# Module Loading System

This document describes the module loading system that allows techniques to specify their dependencies and automatically load the required modules when running Slurm jobs.

## Overview

The module loading system consists of:

1. **Module Definitions** (`config/modules/`): YAML files defining sets of modules and environment setup
2. **Technique Configuration** (`config/reorder.yml`, `config/multiply.yml`): Extended to specify which module set each technique requires
3. **Module Loading Script** (`Programs/load_modules.sh`): Script that reads configurations and loads appropriate modules
4. **Integration**: Automatic module loading in `Reorder.sbatch` and `Multiply.sbatch`

## Module Definitions

Module definition files in `config/modules/` define reusable sets of modules:

```yaml
name: "python_scipy"
description: "Python environment with SciPy for matrix operations"
modules:
  - "python/3.11"
  - "gcc/9.3.0"
  - "openmpi/4.1.0"
environment:
  PYTHONPATH: "${PROJECT_ROOT}/scripts:${PYTHONPATH:-}"
post_load:
  - "python -c 'import scipy, numpy; print(f\"SciPy {scipy.__version__}, NumPy {numpy.__version__}\")'"
```

Available module sets:
- `basic`: Minimal dependencies (GCC only)
- `python_scipy`: Python with SciPy/NumPy for matrix operations  
- `cuda_cusparse`: CUDA environment for GPU operations
- `metis`: METIS library for graph partitioning

## Technique Configuration

Techniques specify their module requirements in their configuration files:

```yaml
# config/reorder.yml
rcm:
  type: "2D"
  modules: "python_scipy"  # <-- NEW: Module requirement
  params:
    - symmetric: true
```

## Usage

Module loading happens automatically when running sbatch scripts:

```bash
# Automatically loads python_scipy modules for RCM
sbatch Programs/Reorder.sbatch /path/to/matrix.mtx rcm

# Automatically loads cuda_cusparse modules for cuSPARSE
sbatch Programs/Multiply.sbatch /path/to/results.csv cucsrspmm
```

The module loading process:
1. Reads technique configuration to determine required module set
2. Loads the module definition file
3. Calls `module load` for each specified module (if module system available)
4. Sets environment variables as specified
5. Runs post-load verification commands

## Adding New Techniques

To add a new technique with specific module requirements:

1. Create a module definition file in `config/modules/` if needed
2. Add the technique to `config/reorder.yml` or `config/multiply.yml` with a `modules` field
3. Create the technique wrapper script in `Programs/Reordering/Techniques/` or `Programs/Multiplication/Techniques/`

## Environment Compatibility

The system gracefully handles environments without a module system:
- Skips `module load` commands if `module` command is not available
- Still sets environment variables and runs verification commands
- Provides helpful warnings when tools are not available

This allows the same configuration to work in both HPC environments with module systems and development environments without them.