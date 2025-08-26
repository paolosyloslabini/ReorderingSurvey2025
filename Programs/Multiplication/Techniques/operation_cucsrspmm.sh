#!/usr/bin/env bash
# operation_cucsrspmm.sh <outdir> [key=value ...]
# NVIDIA cuSPARSE CSR SpMM wrapper (updated to remove CPU fallback)
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

OUTDIR="$1"
shift
PARAMS=("$@")

# Extract parameters
alpha="1.0"
beta="0.0"
for kv in "${PARAMS[@]}"; do
    case $kv in
        alpha=*) alpha="${kv#alpha=}" ;;
        beta=*) beta="${kv#beta=}" ;;
    esac
done

# Check if reordered matrix exists
REORDERED="$OUTDIR/reordered.mtx"
if [[ ! -f "$REORDERED" ]]; then
    echo "Error: Reordered matrix not found at $REORDERED" >&2
    echo "TIMING_MS:0"
    exit 1
fi

# Use the Python cuSPARSE CSR SpMM implementation
CUSPARSE_SCRIPT="$PROJECT_ROOT/scripts/cucsrspmm.py"
if [[ ! -f "$CUSPARSE_SCRIPT" ]]; then
    echo "Error: cuSPARSE CSR SpMM script not found at $CUSPARSE_SCRIPT" >&2
    echo "TIMING_MS:0"
    exit 1
fi

# Build command line arguments
CUSPARSE_ARGS=("$REORDERED" "--alpha" "$alpha" "--beta" "$beta")
# Note: force_cpu option removed - GPU operations fail if GPU not available

# Execute the cuSPARSE implementation
# The script will output timing to stdout and diagnostics to stderr
set +e
CUSPARSE_OUTPUT=$(python "$CUSPARSE_SCRIPT" "${CUSPARSE_ARGS[@]}" 2>&1)
CUSPARSE_STATUS=$?
set -e

# Parse output - timing should be on stdout, diagnostics on stderr
if echo "$CUSPARSE_OUTPUT" | grep -q "^TIMING_MS:"; then
    # Extract timing from output
    echo "$CUSPARSE_OUTPUT" | grep "^TIMING_MS:" | head -1
else
    echo "Error: No timing output from cuSPARSE CSR SpMM implementation" >&2
    echo "cuSPARSE output: $CUSPARSE_OUTPUT" >&2
    echo "TIMING_MS:0"
    exit 1
fi

exit $CUSPARSE_STATUS