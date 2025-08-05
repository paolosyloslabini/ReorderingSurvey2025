#!/usr/bin/env bash
# operation_cucsrspmm.sh <outdir> [key=value ...]
# NVIDIA cuSPARSE CSR SpMM wrapper
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

OUTDIR="$1"
shift
PARAMS=("$@")

REORDERED="$OUTDIR/reordered.mtx"
if [[ ! -f "$REORDERED" ]]; then
    echo "Error: reordered matrix file not found: $REORDERED" >&2
    exit 1
fi

# Check for GPU environment
if ! command -v nvidia-smi &> /dev/null; then
    echo "Error: nvidia-smi not found. GPU environment required for cuSPARSE." >&2
    exit 1
fi

# Check for CUDA/cuSPARSE
if ! command -v nvcc &> /dev/null; then
    echo "Error: nvcc not found. Please load CUDA module." >&2
    exit 1
fi

# Extract parameters
alpha="1.0"
beta="0.0"
num_cols_B="64"
for kv in "${PARAMS[@]}"; do
    case $kv in
        alpha=*) alpha="${kv#alpha=}" ;;
        beta=*) beta="${kv#beta=}" ;;
        num_cols_B=*) num_cols_B="${kv#num_cols_B=}" ;;
    esac
done

# Build cuSPARSE implementation if needed
IMPL_DIR="$(dirname "$0")/.."
EXECUTABLE="$IMPL_DIR/cusparse_spmm"

if [[ ! -x "$EXECUTABLE" ]]; then
    echo "Building cuSPARSE implementation..." >&2
    cd "$IMPL_DIR"
    make clean && make || {
        echo "Error: Failed to build cuSPARSE implementation. Check CUDA installation." >&2
        exit 1
    }
    cd - > /dev/null
fi

# Run cuSPARSE SpMM
RESULTS_FILE="$OUTDIR/cusparse_results.txt"
"$EXECUTABLE" "$REORDERED" "$RESULTS_FILE" "$alpha" "$beta" "$num_cols_B" || {
    echo "Error: cuSPARSE SpMM execution failed" >&2
    exit 1
}

# Check if results file was created
if [[ ! -f "$RESULTS_FILE" ]]; then
    echo "Error: Results file not created" >&2
    exit 1
fi

echo "cuSPARSE SpMM completed successfully" >&2
exit 0