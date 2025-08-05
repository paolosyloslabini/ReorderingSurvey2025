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

MTX_PATH="$MATRIX_DIR/$DATASET/$MATRIX_NAME.mtx"

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

set +e
WRAPPER_OUTPUT=$("$WRAPPER" "$OUTDIR" "${PARAMS[@]}" 2>&1)
STATUS=$?
set -e

# Extract timing from wrapper output (should be the last line that's a number)
if [[ $STATUS -eq 0 ]]; then
    # Get the timing from wrapper's stdout (should be echoed as the last numeric line)
    TIME_MS=$(echo "$WRAPPER_OUTPUT" | grep -E '^[0-9]+\.?[0-9]*$' | tail -n 1)
    if [[ -z "$TIME_MS" ]]; then
        echo "Warning: No timing output from wrapper, using fallback measurement" >&2
        # Fallback: use a minimal time estimate
        TIME_MS="0"
    fi
else
    TIME_MS="0"
fi

TIMESTAMP=$(date --iso-8601=seconds)

python "$PROJECT_ROOT/scripts/update_csv.py" "$CSV" "$IMPL" "$PARAM_SET" "$TIME_MS" "$STATUS" "$TIMESTAMP"

# For cuSPARSE, also pass the results file for detailed metrics
if [[ "$IMPL" == "cucsrspmm" ]]; then
    CUSPARSE_RESULTS="$OUTDIR/cusparse_results.txt"
    if [[ -f "$CUSPARSE_RESULTS" ]]; then
        python "$PROJECT_ROOT/scripts/update_csv_multiply.py" "$CSV" "$IMPL" "$PARAM_SET" "$TIME_MS" "$STATUS" "$TIMESTAMP" "$CUSPARSE_RESULTS"
    fi
fi

# ------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------
if [[ -f "$REORDERED" ]]; then
    rm -f "$REORDERED"
fi


exit $STATUS
