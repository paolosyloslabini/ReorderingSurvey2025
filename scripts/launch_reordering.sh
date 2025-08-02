#!/usr/bin/env bash
# Submit a reordering job via sbatch
# Usage: launch_reordering.sh <matrix_path> <reorder_tech> [key=value ...]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROGRAM="$ROOT/Programs/Reorder.sbatch"

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <matrix_path> <reorder_tech> [key=value ...]" >&2
    exit 1
fi

MATRIX="$1"
TECH="$2"
shift 2
PARAMS=("$@")

if (( ${#PARAMS[@]} )); then
    PARAM_SET=$(IFS=';'; echo "${PARAMS[*]}")
    PARAM_ID=$(echo "$PARAM_SET" | tr ';' '_' | tr '=' '-')
else
    PARAM_ID="default"
fi

MATRIX_NAME=$(basename "$MATRIX" .mtx)
EXP_NAME="Reordering_${MATRIX_NAME}_${TECH}_${PARAM_ID}"
LOG_DIR=${LOG_DIR:-"$ROOT/logs"}
HOST=$(hostname)
OUT_DIR="$LOG_DIR/$HOST/$EXP_NAME"
mkdir -p "$OUT_DIR"

SBATCH_OPTS=("--job-name=$EXP_NAME" "--output=$OUT_DIR/${EXP_NAME}_%j.out" "--error=$OUT_DIR/${EXP_NAME}_%j.err")
[[ -n "${PARTITION:-}" ]] && SBATCH_OPTS+=("--partition=$PARTITION")
[[ -n "${ACCOUNT:-}" ]] && SBATCH_OPTS+=("--account=$ACCOUNT")
[[ -n "${TIME:-}" ]] && SBATCH_OPTS+=("--time=$TIME")
[[ -n "${QOS:-}" ]] && SBATCH_OPTS+=("--qos=$QOS")
[[ -n "${NODES:-}" ]] && SBATCH_OPTS+=("--nodes=$NODES")
[[ -n "${GPUS:-}" ]] && SBATCH_OPTS+=("--gres=gpu:$GPUS")
[[ -n "${NTASKS:-}" ]] && SBATCH_OPTS+=("--ntasks=$NTASKS")
[[ -n "${CPUS_PER_TASK:-}" ]] && SBATCH_OPTS+=("--cpus-per-task=$CPUS_PER_TASK")

sbatch "${SBATCH_OPTS[@]}" "$PROGRAM" "$MATRIX" "$TECH" "${PARAMS[@]}"
