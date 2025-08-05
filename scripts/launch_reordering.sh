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
mapfile -t CFG_OPTS < <(python - "$SBATCH_CFG" <<'PY'
import sys, yaml
with open(sys.argv[1]) as f:
    cfg = yaml.safe_load(f) or {}
for k, v in cfg.items():
    if v in (None, ""):
        continue
    print(f"--{k.replace('_','-')}={v}")
PY
)

SBATCH_OPTS=("--job-name=$EXP_NAME" "--output=$OUT_DIR/${EXP_NAME}_%j.out" "--error=$OUT_DIR/${EXP_NAME}_%j.err" "${CFG_OPTS[@]}")

# Time and GPU usage from reordering config
read GPUS TIME < <(python - "$TECH" "$ROOT/config/reorder.yml" <<'PY'
import sys, yaml
tech, path = sys.argv[1], sys.argv[2]
with open(path) as f:
    cfg = yaml.safe_load(f) or {}
info = cfg.get(tech, {})
print(info.get('gpus', 0) or 0, info.get('time', ''))
PY
)
[[ "$GPUS" != 0 ]] && SBATCH_OPTS+=("--gres=gpu:$GPUS")
[[ -n "$TIME" ]] && SBATCH_OPTS+=("--time=$TIME")

sbatch "${SBATCH_OPTS[@]}" "$PROGRAM" "$MATRIX" "$TECH" "${PARAMS[@]}"
