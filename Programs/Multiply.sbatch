#!/bin/bash

#SBATCH --job-name=<exp-name>
#SBATCH --output=<sout_path>/<hostname>/<exp-name>/<exp-name>_%j.out
#SBATCH --error=<sout_path>/<hostname>/<exp-name>/<exp-name>_%j.err

#SBATCH --partition=<partition>
#SBATCH --account=<account>
#SBATCH --time=<time>

#SBATCH --nodes=<nnodes>
#SBATCH --gres=gpu:<ngpus>
#SBATCH --tasks=<ntasks>
#SBATCH --cpus-per-task=<cpus-per-task>



# Driver for a single multiplication experiment.
# Usage: sbatch Programs/Multiply.sbatch <matrix_dir> <perm_path> <mult_impl> [key=value ...]

set -euo pipefail

source "$(dirname "$0")/exp_config.sh"

if [[ $# -lt 3 ]]; then
    echo "Usage: $0 <matrix_dir> <perm_path> <mult_impl> [key=value ...]" >&2
    exit 1
fi

MAT_DIR="$1"
PERM="$2"
IMPL="$3"
shift 3
PARAMS=("$@")

if [[ ! -f "$PERM" ]]; then
    echo "Permutation file $PERM not found" >&2
    exit 1
fi

MATRIX_NAME=$(basename "$(dirname "$MAT_DIR")")
TECH_PARAM=$(basename "$MAT_DIR")

OUTDIR="$RESULTS_DIR/Multiplication/$MATRIX_NAME/$TECH_PARAM/$IMPL"
mkdir -p "$OUTDIR"
CSV="$OUTDIR/results.csv"

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

cp "$MAT_DIR/results.csv" "$CSV"

start=$(date +%s%N)
set +e
"$WRAPPER" "$MAT_DIR" "${PARAMS[@]}"
STATUS=$?
set -e
end=$(date +%s%N)
TIME_MS=$(( (end - start) / 1000000 ))
TIMESTAMP=$(date --iso-8601=seconds)

python - <<'PY' "$CSV" "$IMPL" "$PARAM_SET" "$TIME_MS" "$STATUS" "$TIMESTAMP"
import sys,pandas as pd
csv,impl,param_set,time_ms,status,timestamp=sys.argv[1:7]
df=pd.read_csv(csv)
df['mult_type']=impl
df['mult_param_set']=param_set
df['mult_time_ms']=float(time_ms)
df['exit_code']=int(status)
df['timestamp']=timestamp
df.to_csv(csv,index=False)
PY

exit $STATUS
