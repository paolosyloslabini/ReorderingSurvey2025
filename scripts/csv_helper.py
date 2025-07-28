"""Merge structural metrics into reordering results.

This utility reads the original matrix, the permutation produced by a
reordering technique, and the CSV row emitted by the wrapper script.
Using SciPy's sparse matrix routines it calculates the half-bandwidth
and block-level densities (4x4, 8x8, 16x16).  The metrics are written
back into the same CSV file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import io, sparse


def compute_bandwidth(a: sparse.spmatrix) -> int:
    """Return the half-bandwidth of ``a``."""
    if a.nnz == 0:
        return 0
    rows, cols = a.nonzero()
    return int(np.abs(rows - cols).max())


def block_metrics(a: sparse.spmatrix, block: int) -> float:
    """Return density of non-empty ``block``×``block`` tiles."""
    rows, cols = a.nonzero()
    br = rows // block
    bc = cols // block
    unique = len({(r, c) for r, c in zip(br, bc)})
    total = ((a.shape[0] + block - 1) // block) * ((a.shape[1] + block - 1) // block)
    return unique / total if total else 0.0


def main(matrix: Path, perm: Path, csv: Path) -> None:
    A = io.mmread(matrix).tocsr()
    p = np.loadtxt(perm, dtype=np.int64) - 1
    A = A[p, :][:, p]

    bw = compute_bandwidth(A)
    densities = {b: block_metrics(A, b) for b in (4, 8, 16)}

    df = pd.read_csv(csv)
    if "bandwidth" not in df.columns:
        df["bandwidth"] = np.nan
    if "block_density" not in df.columns:
        df["block_density"] = ""
    df.loc[0, "bandwidth"] = bw
    df.loc[0, "block_density"] = json.dumps(densities)
    df.to_csv(csv, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add structural metrics to CSV")
    parser.add_argument("matrix", type=Path, help="Path to .mtx matrix file")
    parser.add_argument("permutation", type=Path, help="Path to permutation .g")
    parser.add_argument("csv", type=Path, help="CSV file to update")
    args = parser.parse_args()
    main(args.matrix, args.permutation, args.csv)
