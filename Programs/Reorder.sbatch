#!/bin/bash

# General driver for a single reordering experiment.
# Usage: sbatch Programs/Reorder.sbatch <matrix_path> <reorder_tech> [key=value ...]

set -euo pipefail

# Ensure PROJECT_ROOT, MATRIX_DIR, RESULTS_DIR
source "$(dirname "$0")/exp_config.sh"

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <matrix_path> <reorder_tech> [key=value ...]" >&2
    exit 1
fi

MATRIX="$1"
TECH="$2"
shift 2
PARAMS=("$@")

MATRIX_NAME=$(basename "$MATRIX" .mtx)
DATASET=$(basename "$(dirname "$MATRIX")")

if (( ${#PARAMS[@]} )); then
    PARAM_SET=$(IFS=';'; echo "${PARAMS[*]}")
    PARAM_ID=$(echo "$PARAM_SET" | tr ';' '_' | tr '=' '-')
else
    PARAM_SET=""
    PARAM_ID="default"
fi

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

start=$(date +%s%N)
set +e
"$WRAPPER" "$MATRIX" "$PERM" "${PARAMS[@]}"
STATUS=$?
set -e
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

# Generate reordered matrix for downstream use and metrics
REORDERED="$OUTDIR/reordered.mtx"
python "$PROJECT_ROOT/scripts/reorder_matrix.py" "$MATRIX" "$PERM" "$REORDER_TYPE" "$REORDERED"

# Post-process structural metrics
python "$PROJECT_ROOT/scripts/csv_helper.py" "$REORDERED" "$CSV" || true

exit $STATUS
