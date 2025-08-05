#!/usr/bin/env bash
# Submit a reordering job via sbatch
# Usage: launch_reordering.sh <matrix_path> <reorder_tech> [key=value ...]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROGRAM="$ROOT/Programs/Reorder.sbatch"
SBATCH_CFG="$ROOT/config/sbatch.yml"

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

# Base SBATCH options from global config
mapfile -t CFG_OPTS < <(
    yq -r 'to_entries | map(select(.value != null and .value != "")) | .[] |
    "--" + (.key|gsub("_";"-")) + "=" + (.value|tostring)' "$SBATCH_CFG"
)

SBATCH_OPTS=("--job-name=$EXP_NAME" "--output=$OUT_DIR/${EXP_NAME}_%j.out" "--error=$OUT_DIR/${EXP_NAME}_%j.err" "${CFG_OPTS[@]}")

# Time and GPU usage from reordering config
GPUS=$(yq eval ".[\"$TECH\"].gpus // 0" "$ROOT/config/reorder.yml")
TIME=$(yq eval ".[\"$TECH\"].time // \"\"" "$ROOT/config/reorder.yml")
[[ "$GPUS" != 0 ]] && SBATCH_OPTS+=("--gres=gpu:$GPUS")
[[ -n "$TIME" ]] && SBATCH_OPTS+=("--time=$TIME")

sbatch "${SBATCH_OPTS[@]}" "$PROGRAM" "$MATRIX" "$TECH" "${PARAMS[@]}"
