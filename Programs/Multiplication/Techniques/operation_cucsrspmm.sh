#!/usr/bin/env bash
# operation_cucsrspmm.sh <outdir> [key=value ...]
# NVIDIA cuSPARSE CSR SpMM wrapper (placeholder implementation)
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

OUTDIR="$1"
shift
PARAMS=("$@")

# Check if this is a real GPU environment (placeholder check)
if ! command -v nvidia-smi &> /dev/null; then
    echo "Warning: nvidia-smi not found, running in mock mode" >&2
fi

# Extract parameters
alpha="1.0"
beta="0.0"
for kv in "${PARAMS[@]}"; do
    case $kv in
        alpha=*) alpha="${kv#alpha=}" ;;
        beta=*) beta="${kv#beta=}" ;;
    esac
done

# Start internal timing
start=$(date +%s%N)

# TODO: Implement actual cuSPARSE CSR SpMM call here
# For now, just simulate execution time based on matrix size
REORDERED="$OUTDIR/reordered.mtx"
if [[ -f "$REORDERED" ]]; then
    # Extract matrix size for simulated timing
    nnz=$(awk 'NR>1 && !/^%/ {print $3; exit}' "$REORDERED" 2>/dev/null || echo "1000")
    # Simulate execution time: 1-5ms base + 0.001ms per nnz
    sleep_time=$(awk -v nnz="$nnz" "BEGIN {print (0.001 + nnz * 0.000001)}")
    sleep "$sleep_time"
fi

# End internal timing and write to file
end=$(date +%s%N)
time_ms=$(( (end - start) / 1000000 ))
echo "$time_ms" > "$OUTDIR/timing_ms.txt"

exit 0