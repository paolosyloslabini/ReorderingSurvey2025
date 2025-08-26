#!/usr/bin/env bash
# operation_csrcusparse.sh <outdir> [key=value ...]
# CSR cuSPARSE multiplication wrapper with direct cuSPARSE implementation
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

OUTDIR="$1"
shift
PARAMS=("$@")

# Extract parameters
alpha="1.0"
beta="0.0"
force_cpu="false"
for kv in "${PARAMS[@]}"; do
    case $kv in
        alpha=*) alpha="${kv#alpha=}" ;;
        beta=*) beta="${kv#beta=}" ;;
        force_cpu=*) force_cpu="${kv#force_cpu=}" ;;
    esac
done

# Check if reordered matrix exists
REORDERED="$OUTDIR/reordered.mtx"
if [[ ! -f "$REORDERED" ]]; then
    echo "Error: Reordered matrix not found at $REORDERED" >&2
    echo "TIMING_MS:0"
    exit 1
fi

# Use the Python CSR cuSPARSE implementation
CSRCUSPARSE_SCRIPT="$PROJECT_ROOT/scripts/csrcusparse_multiply.py"
if [[ ! -f "$CSRCUSPARSE_SCRIPT" ]]; then
    echo "Error: CSR cuSPARSE script not found at $CSRCUSPARSE_SCRIPT" >&2
    echo "TIMING_MS:0"
    exit 1
fi

# Build command line arguments
CSRCUSPARSE_ARGS=("$REORDERED" "--alpha" "$alpha" "--beta" "$beta")
if [[ "$force_cpu" == "true" ]]; then
    CSRCUSPARSE_ARGS+=("--force-cpu")
fi

# Execute the CSR cuSPARSE implementation
# The script will output timing to stdout and diagnostics to stderr
set +e
CSRCUSPARSE_OUTPUT=$(python3 "$CSRCUSPARSE_SCRIPT" "${CSRCUSPARSE_ARGS[@]}" 2>&1)
CSRCUSPARSE_STATUS=$?
set -e

# Parse output - timing should be on stdout, diagnostics on stderr
if echo "$CSRCUSPARSE_OUTPUT" | grep -q "^TIMING_MS:"; then
    # Extract timing from output
    echo "$CSRCUSPARSE_OUTPUT" | grep "^TIMING_MS:" | head -1
else
    echo "Error: No timing output from CSR cuSPARSE implementation" >&2
    echo "CSR cuSPARSE output: $CSRCUSPARSE_OUTPUT" >&2
    echo "TIMING_MS:0"
    exit 1
fi

exit $CSRCUSPARSE_STATUS