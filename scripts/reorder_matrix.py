#!/usr/bin/env python3
"""Apply a permutation to a Matrix Market file.

The permutation file is expected to contain 1-based indices, one per line.
Depending on ``rtype``:
- ``1D``: Permutes only the rows of the matrix.
- ``2D``: Applies the permutation to both rows and columns.

The reordered matrix is written to ``out_path``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from scipy.io import mmread, mmwrite


def apply_permutation(matrix: Path, perm: Path, rtype: str, out_path: Path) -> None:
    A = mmread(matrix).tocsr()
    p = np.loadtxt(perm, dtype=np.int64) - 1
    if rtype.upper() == "2D":
        A = A[p, :][:, p]
    else:
        A = A[p, :]
    mmwrite(out_path, A)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reorder a matrix with a permutation")
    parser.add_argument("matrix", type=Path, help="Path to input .mtx matrix")
    parser.add_argument("permutation", type=Path, help="Path to permutation file")
    parser.add_argument("rtype", choices=["1D", "2D"], help="Reordering type")
    parser.add_argument("out", type=Path, help="Output path for reordered matrix")
    args = parser.parse_args()
    apply_permutation(args.matrix, args.permutation, args.rtype, args.out)


if __name__ == "__main__":
    main()
