#!/usr/bin/env bash
# reordering_rcm_graphblas.sh <matrix> <out_perm> [key=value ...]
# Reverse Cuthill-McKee reordering using GraphBLAS for better performance
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

# parameters
symmetric="true"

python - << PY
import sys, numpy as np

# Try to use GraphBLAS, fall back to SciPy if needed
try:
    from graphblas import io as graphblas_io
    USE_GRAPHBLAS = True
except ImportError:
    import scipy.io
    USE_GRAPHBLAS = False

# Read arguments
mtx_file = "$1"
out_perm = "$2"
symmetric = "$symmetric"

if USE_GRAPHBLAS:
    # Load matrix using GraphBLAS
    A = graphblas_io.mmread(mtx_file)
    # Convert to SciPy for RCM (scipy.sparse.csgraph functions need scipy matrices)
    from graphblas.io import to_scipy_sparse
    A_scipy = to_scipy_sparse(A, format='csr')
else:
    # Load matrix using SciPy directly
    import scipy.io
    A_scipy = scipy.io.mmread(mtx_file).tocsr()

# Apply RCM reordering using SciPy (algorithm itself)
from scipy.sparse.csgraph import reverse_cuthill_mckee
perm = reverse_cuthill_mckee(A_scipy, symmetric_mode=(symmetric.lower() == "true"))

# Save permutation (1-based indices)
np.savetxt(out_perm, perm + 1, fmt='%d')
PY