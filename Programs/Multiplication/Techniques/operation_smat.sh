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
# Note: m, n, k will be auto-detected from matrix, but can be overridden
m=""
n=""
k=""
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

# Auto-detect matrix dimensions from the .mtx file if not provided
if [[ -z "$m" || -z "$n" || -z "$k" ]]; then
    # Extract dimensions from Matrix Market file
    # Skip comment lines starting with %, get first data line: rows cols nnz
    matrix_dims=$(grep -v '^%' "$REORDERED" | head -1)
    matrix_rows=$(echo "$matrix_dims" | cut -d' ' -f1)
    matrix_cols=$(echo "$matrix_dims" | cut -d' ' -f2)
    
    # Use auto-detected dimensions if not overridden
    [[ -z "$m" ]] && m="$matrix_rows"
    [[ -z "$n" ]] && n="$matrix_cols"
    [[ -z "$k" ]] && k="$matrix_cols"  # For SpMM, k typically equals matrix cols
    
    echo "Auto-detected matrix dimensions: m=$m, n=$n, k=$k" >&2
fi

# Find SMAT binary
SMAT_BINARY=""
# Look in common locations for SMAT binary
possible_paths=(
    "$PROJECT_ROOT/build/smat/output/bin/hgemm"
    "/opt/smat/bin/hgemm"
    "/usr/local/bin/hgemm"
    "/usr/bin/hgemm"
    "hgemm"  # In PATH
)

if [[ -n "${SMAT_HOME:-}" ]]; then
    possible_paths=("$SMAT_HOME/bin/hgemm" "${possible_paths[@]}")
fi

for path in "${possible_paths[@]}"; do
    if command -v "$path" &> /dev/null; then
        SMAT_BINARY="$path"
        break
    fi
done

if [[ -z "$SMAT_BINARY" ]]; then
    echo "Error: SMAT binary (hgemm) not found. Please install SMAT using:" >&2
    echo "  ./scripts/bootstrap_smat.sh" >&2
    echo "Or ensure hgemm is in PATH or set SMAT_HOME." >&2
    echo "TIMING_MS:0"
    exit 1
fi

# Build SMAT command line arguments
SMAT_ARGS=(
    "-M=$m"
    "-N=$n"
    "-K=$k"
    "-enable_wmma=true"
    "-enable_mma=true"
    "-warmup_iterations=$warmup_iterations"
    "-profiling_iterations=$profiling_iterations"
    "-sleep_duration=100"
    "-enable_check=false"
    "-n_mult=$n_mult"
    "-filename=$REORDERED"
)

echo "Running SMAT command: $SMAT_BINARY ${SMAT_ARGS[*]}" >&2

# Execute SMAT binary directly
set +e
SMAT_OUTPUT=$("$SMAT_BINARY" "${SMAT_ARGS[@]}" 2>&1)
SMAT_STATUS=$?
set -e

if [[ $SMAT_STATUS -ne 0 ]]; then
    echo "Error: SMAT execution failed with return code $SMAT_STATUS" >&2
    echo "SMAT output: $SMAT_OUTPUT" >&2
    echo "TIMING_MS:0"
    exit 1
fi

# Parse SMAT output for timing information
# SMAT outputs timing information in its stdout
timing_ms=""
while IFS= read -r line; do
    # Look for timing patterns in SMAT output (adjust pattern as needed)
    if [[ "$line" =~ avg.*[0-9]+\.?[0-9]*.*ms ]] || [[ "$line" =~ time.*[0-9]+\.?[0-9]* ]]; then
        # Extract numeric value from the line
        timing_ms=$(echo "$line" | grep -oE '[0-9]+\.?[0-9]*' | head -1)
        break
    fi
done <<< "$SMAT_OUTPUT"

if [[ -z "$timing_ms" ]]; then
    echo "Error: Could not parse timing from SMAT output" >&2
    echo "SMAT output: $SMAT_OUTPUT" >&2
    echo "TIMING_MS:0"
    exit 1
fi

echo "TIMING_MS:$timing_ms"
exit 0