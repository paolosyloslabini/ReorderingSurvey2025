# Cluster-wide environment and path definitions

# Determine the absolute project root (one level up from this file)
export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Allow overriding dataset and result locations.  By default both
# directories live inside the repository, but large deployments can
# point them elsewhere before sourcing this file.
export MATRIX_DIR="${MATRIX_DIR:-$PROJECT_ROOT/Raw_Matrices}"
export RESULTS_DIR="${RESULTS_DIR:-$PROJECT_ROOT/Results}"

# CUDA/cuSPARSE environment setup
# Check if we're in a cluster environment with module system
if command -v module &> /dev/null; then
    # Load CUDA and related modules if available
    # Adjust these module names according to your cluster
    module load cuda/12.0 2>/dev/null || module load cuda/11.8 2>/dev/null || true
    module load gcc/9.0 2>/dev/null || module load gcc/8.0 2>/dev/null || true
fi

# Set CUDA paths if not already set
if [[ -z "${CUDA_HOME:-}" ]]; then
    for cuda_path in /usr/local/cuda /opt/cuda /usr/cuda; do
        if [[ -d "$cuda_path" && -x "$cuda_path/bin/nvcc" ]]; then
            export CUDA_HOME="$cuda_path"
            break
        fi
    done
fi

# Add CUDA to PATH if found
if [[ -n "${CUDA_HOME:-}" ]]; then
    export PATH="$CUDA_HOME/bin:$PATH"
    export LD_LIBRARY_PATH="$CUDA_HOME/lib64:${LD_LIBRARY_PATH:-}"
fi

