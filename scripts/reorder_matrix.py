#!/usr/bin/env python3
"""Apply a permutation to a Matrix Market file using SciPy.

This script applies a permutation to a matrix for reordering purposes.
The permutation file is expected to contain **1‑based** indices, one per line.
Depending on ``rtype``:
- ``1D``: Permute **rows only**.
- ``2D``: Permute **both rows and columns** with the same permutation.

The reordered matrix is written back to Matrix‑Market **with 1‑based coordinates**
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Tuple
import numpy as np
import scipy.io
import scipy.sparse

# ---------------------------------------------------------------------------
# Core routine – permutation application using scipy.
# ---------------------------------------------------------------------------

def apply_permutation(
    matrix: Path, perm: Path, rtype: str, out_path: Path
) -> None:
    """Reorder *matrix* according to *perm* and write the result to *out_path*."""

    # Load matrix using scipy
    A = scipy.io.mmread(str(matrix))
    if hasattr(A, 'tocsr'):
        A = A.tocsr()
    
    # Permutation vector: file stores 1‑based indices → convert to 0‑based.
    p = np.loadtxt(perm, dtype=np.int64) - 1
    
    # Apply the permutation
    if rtype.upper() == "2D":
        A = A[p, :][:, p]  # reorder rows then columns
    else:  # "1D"
        A = A[p, :]        # reorder rows only

    # Save the result
    scipy.io.mmwrite(str(out_path), A)

# ---------------------------------------------------------------------------
# CLI wrapper
# ---------------------------------------------------------------------------

def _parse_args() -> Tuple[Path, Path, str, Path]:
    parser = argparse.ArgumentParser(
        description="Reorder a Matrix Market matrix using SciPy",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("matrix", type=Path, help="Path to input .mtx matrix")
    parser.add_argument("permutation", type=Path, help="Path to permutation file")
    parser.add_argument("rtype", choices=["1D", "2D"], help="Reordering type")
    parser.add_argument("out", type=Path, help="Output path for reordered matrix")
    args = parser.parse_args()
    return args.matrix, args.permutation, args.rtype, args.out


def main() -> None:
    matrix, permutation, rtype, out = _parse_args()
    apply_permutation(matrix, permutation, rtype, out)


if __name__ == "__main__":
    main()