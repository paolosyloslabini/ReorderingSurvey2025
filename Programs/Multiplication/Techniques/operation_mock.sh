#!/usr/bin/env bash
# operation_mock.sh <outdir> [key=value ...]
# Mock multiplication operation for testing and demonstration purposes
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

OUTDIR="$1"
shift
PARAMS=("$@")

# Extract parameters (currently just pass them through)
alpha="1.0"
for kv in "${PARAMS[@]}"; do
    case $kv in
        alpha=*) alpha="${kv#alpha=}" ;;
    esac
done

# Start internal timing
start=$(date +%s%N)

# Mock computation: simulate 100-200ms execution time
sleep_time=$(awk "BEGIN {srand(); print (rand() * 0.1) + 0.1}")
sleep "$sleep_time"

# End internal timing and write to file
end=$(date +%s%N)
time_ms=$(( (end - start) / 1000000 ))
echo "$time_ms" > "$OUTDIR/timing_ms.txt"

# Mock success (exit 0)
exit 0