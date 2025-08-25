"""Merge structural metrics into reordering results using GraphBLAS.

This is a drop-in replacement for the SciPy-based csv_helper.py but uses
SuiteSparse GraphBLAS for better performance with large matrices. It avoids
costly format conversions and leverages the efficient GraphBLAS operations.

Usage:
    python csv_helper_graphblas.py matrix.mtx results.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from graphblas import Matrix  # type: ignore

block_sizes = (4, 8, 16, 32, 64)

def read_mm(path: Path) -> Matrix:
    """Load a Matrix Market file using GraphBLAS."""
    from graphblas import io
    return io.mmread(str(path))


def compute_bandwidth_graphblas(mat: Matrix) -> int:
    """Return the half-bandwidth of the matrix using GraphBLAS operations."""
    if mat.nvals == 0:
        return 0
    
    # Get coordinates directly from GraphBLAS matrix
    rows, cols, _ = mat.to_coo()
    if len(rows) == 0:
        return 0
    
    rows = rows.astype(np.int64)
    cols = cols.astype(np.int64)
    return int(np.abs(rows - cols).max())


def block_metrics_graphblas(mat: Matrix, block: int) -> float:
    """Return density of non-empty ``block``×``block`` tiles using GraphBLAS."""
    if mat.nvals == 0:
        return 0.0
    
    # Get coordinates directly from GraphBLAS matrix
    rows, cols, _ = mat.to_coo()
    if len(rows) == 0:
        return 0.0
    
    rows = rows.astype(np.int64)
    cols = cols.astype(np.int64)
    
    # Calculate block coordinates
    br = rows // block
    bc = cols // block
    pairs = np.stack([br, bc], axis=1)
    unique = np.unique(pairs, axis=0).shape[0]
    
    # Calculate total possible blocks
    total = ((mat.nrows + block - 1) // block) * ((mat.ncols + block - 1) // block)
    return unique / total if total else 0.0


def main(matrix: Path, csv: Path) -> None:
    """Main function to add structural metrics to CSV using GraphBLAS."""
    A = read_mm(matrix)
    df = pd.read_csv(csv)

    bw = compute_bandwidth_graphblas(A)
    densities = {b: block_metrics_graphblas(A, b) for b in block_sizes}

    if "bandwidth" not in df.columns:
        df["bandwidth"] = np.nan
    if "block_density" not in df.columns:
        df["block_density"] = ""
    df.loc[0, "bandwidth"] = bw
    df["block_density"] = df["block_density"].astype(str)  # Ensure string type
    df.loc[0, "block_density"] = json.dumps(densities)
    df.to_csv(csv, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add structural metrics to CSV using GraphBLAS")
    parser.add_argument("matrix", type=Path, help="Path to reordered .mtx matrix file")
    parser.add_argument("csv", type=Path, help="CSV file to update")
    args = parser.parse_args()
    main(args.matrix, args.csv)