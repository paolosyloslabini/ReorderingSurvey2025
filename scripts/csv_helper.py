"""Merge structural metrics into reordering results.

This utility reads the original matrix, the permutation produced by a
reordering technique, and the CSV row emitted by the wrapper script.
Using SuiteSparse:GraphBLAS it calculates the half-bandwidth and
block-level densities (4x4, 8x8, 16x16).  The metrics are written back
into the same CSV file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import graphblas as gb


def read_mm(path: Path) -> gb.Matrix:
    """Load a Matrix Market file into a GraphBLAS matrix."""
    with open(path) as f:
        header = f.readline().strip().split()
        if len(header) < 5 or header[0] != "%%MatrixMarket":
            raise ValueError("invalid Matrix Market file")
        symmetry = header[4].lower()
        for line in f:
            if line.startswith("%"):
                continue
            nrows, ncols, _ = map(int, line.split())
            break
        data = np.loadtxt(f)
    if data.ndim == 1:
        data = np.array([data])
    row = data[:, 0].astype(np.int64) - 1
    col = data[:, 1].astype(np.int64) - 1
    val = data[:, 2] if data.shape[1] > 2 else np.ones(len(row))
    if symmetry != "general":
        mask = row != col
        row = np.concatenate([row, col[mask]])
        col = np.concatenate([col, row[mask]])
        val = np.concatenate([val, val[mask]])
    return gb.Matrix.from_coo(row, col, val, nrows=nrows, ncols=ncols)


def compute_bandwidth(a: gb.Matrix) -> int:
    """Return the half-bandwidth of ``a``."""
    if a.nvals == 0:
        return 0
    rows, cols, _ = a.to_coo()
    rows = rows.astype(np.int64)
    cols = cols.astype(np.int64)
    return int(np.abs(rows - cols).max())


def block_metrics(a: gb.Matrix, block: int) -> float:
    """Return density of non-empty ``block``×``block`` tiles."""
    rows, cols, _ = a.to_coo()
    if rows.size == 0:
        return 0.0
    rows = rows.astype(np.int64)
    cols = cols.astype(np.int64)
    br = rows // block
    bc = cols // block
    pairs = np.stack([br, bc], axis=1)
    unique = np.unique(pairs, axis=0).shape[0]
    total = ((a.nrows + block - 1) // block) * ((a.ncols + block - 1) // block)
    return unique / total if total else 0.0


def main(matrix: Path, perm: Path, csv: Path) -> None:
    A = read_mm(matrix)
    p = np.loadtxt(perm, dtype=np.int64) - 1

    df = pd.read_csv(csv)
    rtype = str(df.loc[0, "reorder_type"]).strip().upper() if "reorder_type" in df.columns else "1D"

    if rtype == "2D":
        A = A[p, :][:, p].new()
    else:
        A = A[p, :].new()

    bw = compute_bandwidth(A)
    densities = {b: block_metrics(A, b) for b in (4, 8, 16)}

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
