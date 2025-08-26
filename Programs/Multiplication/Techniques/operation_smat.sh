#!/usr/bin/env bash
# operation_smat.sh <outdir> [key=value ...]
# SMAT (SMaT) sparse matrix multiplication wrapper
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

OUTDIR="$1"
shift
PARAMS=("$@")

# Extract parameters
alpha="1.0"
beta="0.0"
m="512"
n="512"
k="512"
n_mult="1"
warmup_iterations="1"
profiling_iterations="10"

for kv in "${PARAMS[@]}"; do
    case $kv in
        alpha=*) alpha="${kv#alpha=}" ;;
        beta=*) beta="${kv#beta=}" ;;
        m=*) m="${kv#m=}" ;;
        n=*) n="${kv#n=}" ;;
        k=*) k="${kv#k=}" ;;
        n_mult=*) n_mult="${kv#n_mult=}" ;;
        warmup_iterations=*) warmup_iterations="${kv#warmup_iterations=}" ;;
        profiling_iterations=*) profiling_iterations="${kv#profiling_iterations=}" ;;
    esac
done

# Check if reordered matrix exists
REORDERED="$OUTDIR/reordered.mtx"
if [[ ! -f "$REORDERED" ]]; then
    echo "Error: Reordered matrix not found at $REORDERED" >&2
    echo "TIMING_MS:0"
    exit 1
fi

# Use the Python SMAT implementation
SMAT_SCRIPT="$PROJECT_ROOT/scripts/smat.py"
if [[ ! -f "$SMAT_SCRIPT" ]]; then
    echo "Error: SMAT script not found at $SMAT_SCRIPT" >&2
    echo "TIMING_MS:0"
    exit 1
fi

# Build command line arguments
SMAT_ARGS=(
    "$REORDERED" 
    "--alpha" "$alpha" 
    "--beta" "$beta"
    "--m" "$m"
    "--n" "$n" 
    "--k" "$k"
    "--n-mult" "$n_mult"
    "--warmup-iterations" "$warmup_iterations"
    "--profiling-iterations" "$profiling_iterations"
)

# Execute the SMAT implementation
# The script will output timing to stdout and diagnostics to stderr
set +e
SMAT_OUTPUT=$(python3 "$SMAT_SCRIPT" "${SMAT_ARGS[@]}" 2>&1)
SMAT_STATUS=$?
set -e

# Parse output - timing should be on stdout, diagnostics on stderr
if echo "$SMAT_OUTPUT" | grep -q "^TIMING_MS:"; then
    # Extract timing from output
    echo "$SMAT_OUTPUT" | grep "^TIMING_MS:" | head -1
else
    echo "Error: No timing output from SMAT implementation" >&2
    echo "SMAT output: $SMAT_OUTPUT" >&2
    echo "TIMING_MS:0"
    exit 1
fi

exit $SMAT_STATUS