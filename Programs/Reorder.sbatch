#!/bin/bash
#SBATCH -A hpc
#SBATCH -t 02:00:00
#SBATCH -N 1
#SBATCH --cpus-per-task=32
# SBATCH --gpus-per-task=1   # enable for GPU-aware reorderers
# General driver for reordering experiments. Each task reads a line from
# $TASK_FILE containing: <matrix_path> <reorder_tech> <param_json>

set -euo pipefail

# Ensure PROJECT_ROOT, MATRIX_DIR, RESULTS_DIR
source "$(dirname "$0")/exp_config.sh"

if [[ -z "${TASK_FILE:-}" ]]; then
    echo "TASK_FILE not specified" >&2
    exit 1
fi

# Extract arguments for this array task
IFS=' ' read -r MATRIX TECH PARAM_JSON < <(sed -n "$((SLURM_ARRAY_TASK_ID+1))p" "$TASK_FILE")

if [[ -z "$MATRIX" || -z "$TECH" || -z "$PARAM_JSON" ]]; then
    echo "Invalid task specification at index $SLURM_ARRAY_TASK_ID" >&2
    exit 1
fi

MATRIX_NAME=$(basename "$MATRIX" .mtx)
DATASET=$(basename "$(dirname "$MATRIX")")
PARAM_ID=$(basename "$PARAM_JSON" .json)

OUTDIR="$RESULTS_DIR/Reordering/$MATRIX_NAME/${TECH}_${PARAM_ID}"
mkdir -p "$OUTDIR"
PERM="$OUTDIR/permutation.g"
CSV="$OUTDIR/results.csv"

WRAPPER="$PROJECT_ROOT/Programs/Reordering/Techniques/reordering_${TECH}.sh"
if [[ ! -x "$WRAPPER" ]]; then
    echo "Wrapper $WRAPPER not found" >&2
    exit 1
fi

# Determine reordering type (1D vs 2D)
REORDER_TYPE=$(python - <<'PY'
import sys, yaml
tech, cfg_path = sys.argv[1], sys.argv[2]
with open(cfg_path) as f:
    cfg = yaml.safe_load(f)
print(cfg.get(tech, {}).get('type', '1D'))
PY
"$TECH" "$PROJECT_ROOT/config/reorder.yml")

# Convert param JSON to semicolon-separated key=value
PARAM_SET=$(python - <<'PY'
import json,sys
with open(sys.argv[1]) as f:
    cfg=json.load(f)
print(';'.join(f"{k}={v}" for k,v in sorted(cfg.items())))
PY
"$PARAM_JSON")

start=$(date +%s%N)
set +e
"$WRAPPER" "$MATRIX" "$PERM" "$PARAM_JSON"
STATUS=$?
set -e
default=0
end=$(date +%s%N)
TIME_MS=$(( (end - start) / 1000000 ))
TIMESTAMP=$(date --iso-8601=seconds)

# Extract basic matrix info
read N_ROWS N_COLS NNZ < <(python - <<'PY'
import sys
with open(sys.argv[1]) as f:
    header=f.readline()
    for line in f:
        if line.startswith('%'):
            continue
        print(*line.split())
        break
PY
"$MATRIX")

# Write initial CSV row
cat > "$CSV" <<CSV
matrix_name,dataset,n_rows,n_cols,nnz,reorder_type,reorder_tech,reord_param_set,reorder_time_ms,bandwidth,block_density,exit_code,timestamp
$MATRIX_NAME,$DATASET,$N_ROWS,$N_COLS,$NNZ,$REORDER_TYPE,$TECH,"$PARAM_SET",$TIME_MS,,,$STATUS,$TIMESTAMP
CSV

# Post-process structural metrics
python "$PROJECT_ROOT/scripts/csv_helper.py" "$MATRIX" "$PERM" "$CSV" || true

exit $STATUS
