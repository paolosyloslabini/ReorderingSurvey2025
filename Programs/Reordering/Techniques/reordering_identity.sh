#!/usr/bin/env bash
# reordering_identity.sh <matrix> <out_perm> [key=value ...]
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

python - <<'PY' "$1" "$2"
import sys
mtx_path, out_path = sys.argv[1:3]
with open(mtx_path) as f:
    for line in f:
        if line.startswith('%'):
            continue
        nrows = int(line.split()[0])
        break
with open(out_path, 'w') as out:
    for i in range(1, nrows + 1):
        out.write(f"{i}\n")
PY
