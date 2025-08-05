#!/usr/bin/env bash
# reordering_rcm.sh <matrix> <out_perm> [key=value ...]
# Reverse Cuthill-McKee reordering using SciPy
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

# Extract parameters
symmetric="true"
for kv in "${@:3}"; do
    case $kv in
        symmetric=*) symmetric="${kv#symmetric=}" ;;
    esac
done

python - << PY
import sys, scipy.io, scipy.sparse as sp, numpy as np

# Read arguments
mtx_file = "$1"
out_perm = "$2"
symmetric = "$symmetric"

# Load matrix
A = scipy.io.mmread(mtx_file).tocsr()

# Apply RCM reordering
from scipy.sparse.csgraph import reverse_cuthill_mckee
perm = reverse_cuthill_mckee(A, symmetric_mode=(symmetric.lower() == "true"))

# Save permutation (1-based indices)
np.savetxt(out_perm, perm + 1, fmt='%d')
PY