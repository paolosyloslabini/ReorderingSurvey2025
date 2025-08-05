#!/usr/bin/env bash
# Submit a multiplication job via sbatch
# Usage: launch_multiply.sh <reorder_csv> <mult_impl> [key=value ...]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROGRAM="$ROOT/Programs/Multiply.sbatch"
SBATCH_CFG="$ROOT/config/sbatch.yml"

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <reorder_csv> <mult_impl> [key=value ...]" >&2
    exit 1
fi

CSV_SRC="$1"
IMPL="$2"
shift 2
PARAMS=("$@")

if [[ ! -f "$CSV_SRC" ]]; then
    echo "CSV $CSV_SRC not found" >&2
    exit 1
fi

MAT_DIR="$(dirname "$CSV_SRC")"
PERM="$MAT_DIR/permutation.g"
if [[ ! -f "$PERM" ]]; then
    echo "Permutation file $PERM not found" >&2
    exit 1
fi

MATRIX_NAME=$(basename "$(dirname "$MAT_DIR")")
TECH_PARAM=$(basename "$MAT_DIR")

if (( ${#PARAMS[@]} )); then
    PARAM_SET=$(IFS=';'; echo "${PARAMS[*]}")
    PARAM_ID=$(echo "$PARAM_SET" | tr ';' '_' | tr '=' '-')
else
    PARAM_ID="default"
fi

EXP_NAME="${MATRIX_NAME}_${TECH_PARAM}_${IMPL}_${PARAM_ID}"
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

# Time and GPU usage from multiplication config
GPUS=$(yq eval ".[\"$IMPL\"].gpus // 0" "$ROOT/config/multiply.yml")
TIME=$(yq eval ".[\"$IMPL\"].time // \"\"" "$ROOT/config/multiply.yml")
[[ "$GPUS" != 0 ]] && SBATCH_OPTS+=("--gres=gpu:$GPUS")
[[ -n "$TIME" ]] && SBATCH_OPTS+=("--time=$TIME")

sbatch "${SBATCH_OPTS[@]}" "$PROGRAM" "$CSV_SRC" "$IMPL" "${PARAMS[@]}"
