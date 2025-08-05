"""Merge structural metrics into reordering results.

This utility consumes a matrix that has already been permuted by a
reordering technique along with the CSV row emitted by the wrapper
script. Using SuiteSparse:GraphBLAS it calculates the half-bandwidth and
block-level densities (4x4, 8x8, 16x16). The metrics are written back
into the same CSV file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io
import scipy.sparse

block_sizes = (4, 8, 16, 32, 64)

def read_mm(path: Path):
    """Load a Matrix Market file."""
    return scipy.io.mmread(str(path))


def compute_bandwidth(a) -> int:
    """Return the half-bandwidth of ``a``."""
    if hasattr(a, 'tocoo'):
        coo = a.tocoo()
    else:
        coo = a
    
    if coo.nnz == 0:
        return 0
    
    rows = coo.row.astype(np.int64)
    cols = coo.col.astype(np.int64)
    return int(np.abs(rows - cols).max())


def block_metrics(a, block: int) -> float:
    """Return density of non-empty ``block``×``block`` tiles."""
    if hasattr(a, 'tocoo'):
        coo = a.tocoo()
    else:
        coo = a
    
    if coo.nnz == 0:
        return 0.0
    
    rows = coo.row.astype(np.int64)
    cols = coo.col.astype(np.int64)
    br = rows // block
    bc = cols // block
    pairs = np.stack([br, bc], axis=1)
    unique = np.unique(pairs, axis=0).shape[0]
    total = ((coo.shape[0] + block - 1) // block) * ((coo.shape[1] + block - 1) // block)
    return unique / total if total else 0.0


def main(matrix: Path, csv: Path) -> None:
    A = read_mm(matrix)
    df = pd.read_csv(csv)

    bw = compute_bandwidth(A)
    densities = {b: block_metrics(A, b) for b in block_sizes}

    if "bandwidth" not in df.columns:
        df["bandwidth"] = np.nan
    if "block_density" not in df.columns:
        df["block_density"] = ""
    df.loc[0, "bandwidth"] = bw
    df["block_density"] = df["block_density"].astype(str)  # Ensure string type
    df.loc[0, "block_density"] = json.dumps(densities)
    df.to_csv(csv, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add structural metrics to CSV")
    parser.add_argument("matrix", type=Path, help="Path to reordered .mtx matrix file")
    parser.add_argument("csv", type=Path, help="CSV file to update")
    args = parser.parse_args()
    main(args.matrix, args.csv)
