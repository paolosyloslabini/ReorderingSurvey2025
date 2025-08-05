#!/bin/bash

# Driver for a single multiplication experiment.
# Usage: sbatch Programs/Multiply.sbatch <reorder_csv> <mult_impl> [key=value ...]

set -euo pipefail

source "$(dirname "$0")/exp_config.sh"

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <reorder_csv> <mult_impl> [key=value ...]" >&2
    exit 1
fi

CSV_SRC="$1"
IMPL="$2"
shift 2
PARAMS=("$@")

# Load modules for the multiplication technique
source "$(dirname "$0")/load_modules.sh" "multiply" "$IMPL"
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

csv_get() {
    local file="$1" col="$2"
    local idx
    idx=$(awk -F, -v c="$col" 'NR==1{for(i=1;i<=NF;i++) if($i==c){print i; exit}}' "$file")
    awk -F, -v i="$idx" 'NR==2{print $i}' "$file"
}

DATASET=$(csv_get "$CSV_SRC" "dataset")
REORDER_TYPE=$(csv_get "$CSV_SRC" "reorder_type" | tr -d '[:space:]' | tr '[:lower:]' '[:upper:]')

MTX_PATH="$PROJECT_ROOT/Raw_Matrices/$DATASET/$MATRIX_NAME.mtx"

OUTDIR="$RESULTS_DIR/Multiplication/$MATRIX_NAME/$TECH_PARAM/$IMPL"
mkdir -p "$OUTDIR"
CSV="$OUTDIR/results.csv"
REORDERED="$OUTDIR/reordered.mtx"
trap 'rm -f "$REORDERED"' EXIT
python "$PROJECT_ROOT/scripts/reorder_matrix.py" "$MTX_PATH" "$PERM" "$REORDER_TYPE" "$REORDERED"

WRAPPER="$PROJECT_ROOT/Programs/Multiplication/Techniques/operation_${IMPL}.sh"
if [[ ! -x "$WRAPPER" ]]; then
    echo "Wrapper $WRAPPER not found" >&2
    exit 1
fi

if (( ${#PARAMS[@]} )); then
    PARAM_SET=$(IFS=';'; echo "${PARAMS[*]}")
else
    PARAM_SET=""
fi

cp "$CSV_SRC" "$CSV"

start=$(date +%s%N)
set +e
"$WRAPPER" "$OUTDIR" "${PARAMS[@]}"
STATUS=$?
set -e
end=$(date +%s%N)
TIME_MS=$(( (end - start) / 1000000 ))
TIMESTAMP=$(date --iso-8601=seconds)

python "$PROJECT_ROOT/scripts/update_csv.py" "$CSV" "$IMPL" "$PARAM_SET" "$TIME_MS" "$STATUS" "$TIMESTAMP"

# ------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------
if [[ -f "$REORDERED" ]]; then
    rm -f "$REORDERED"
fi


exit $STATUS
