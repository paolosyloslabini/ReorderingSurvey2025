#!/usr/bin/env python3
"""Apply a permutation to a Matrix Market file using SuiteSparse GraphBLAS.

This is a drop‑in replacement for the earlier SciPy version but avoids the
costly CSR → COO → CSR round‑trips by keeping everything inside the GraphBLAS
runtime.

The permutation file is expected to contain **1‑based** indices, one per line.
Depending on ``rtype``:
- ``1D``: Permute **rows only**.
- ``2D``: Permute **both rows and columns** with the same permutation.

The reordered matrix is written back to Matrix‑Market **with 1‑based
coordinates**, preserving compatibility with MATLAB, SciPy, etc.

Requirements
------------
Install one of the official bindings and NumPy, e.g.::

    pip install graphblas‑suitesparse numpy   # preferred
    # or, for older environments
    pip install pygraphblas numpy
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Tuple
import numpy as np
from graphblas import Matrix  # type: ignore

# ---------------------------------------------------------------------------
# I/O helpers – GraphBLAS reads 0‑based indices, Matrix Market wants 1‑based.
# ---------------------------------------------------------------------------

def load_mm(path: Path) -> Matrix:
    """Load a Matrix Market file into a GraphBLAS ``Matrix`` (0‑based)."""
    return Matrix.from_mmio(str(path))


def _dtype_token(mat: Matrix) -> str:
    """Return the Matrix‑Market dtype keyword for *mat*."""
    if mat.is_iso and mat.nvals == 0:
        return "pattern"
    # GraphBLAS type names map well enough to MM tokens.
    name = mat.type.__name__.lower()
    if "int" in name:
        return "integer"
    if "bool" in name:
        # 0/1 pattern-like matrix – there is no dedicated token, use integer.
        return "integer"
    if "float" in name:
        return "real"
    if "complex" in name:
        return "complex"
    # Fallback – MM readers usually accept 'real'.
    return "real"


def save_mm(path: Path, mat: Matrix) -> None:
    """Write *mat* to *path* using **1‑based** coordinates.

    GraphBLAS' built‑in ``Matrix.to_mmio`` emits 0‑based indices, so we roll our
    own. This is fast because we stream out the coordinate lists produced by
    ``Matrix.to_lists`` which are already sorted by row.
    """

    rows, cols, vals = mat.to_lists()
    is_pattern = vals is None
    if is_pattern:
        vals = [1] * len(rows)  # placeholder, never written for pattern

    nrows = mat.nrows
    ncols = mat.ncols
    nnz = len(rows)
    token = _dtype_token(mat) if not is_pattern else "pattern"

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"%%MatrixMarket matrix coordinate {token} general\n")
        f.write(f"{nrows} {ncols} {nnz}\n")
        if is_pattern:
            for r, c in zip(rows, cols):
                f.write(f"{r + 1} {c + 1}\n")
        else:
            for r, c, v in zip(rows, cols, vals):
                f.write(f"{r + 1} {c + 1} {v}\n")

# ---------------------------------------------------------------------------
# Core routine – permutation application.
# ---------------------------------------------------------------------------

def apply_permutation(
    matrix: Path, perm: Path, rtype: str, out_path: Path
) -> None:
    """Reorder *matrix* according to *perm* and write the result to *out_path*."""

    A = load_mm(matrix)

    # Permutation vector: file stores 1‑based indices → convert to 0‑based.
    p = np.loadtxt(perm, dtype=np.int64) - 1
    idx = p.tolist()

    # Apply the permutation. GraphBLAS supports Pythonic slicing.
    if rtype.upper() == "2D":
        A = A[idx, :][:, idx]  # reorder rows then columns
    else:  # "1D"
        A = A[idx, :]          # reorder rows only

    save_mm(out_path, A)

# ---------------------------------------------------------------------------
# CLI wrapper
# ---------------------------------------------------------------------------

def _parse_args() -> Tuple[Path, Path, str, Path]:
    parser = argparse.ArgumentParser(
        description="Reorder a Matrix Market matrix using GraphBLAS",
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
