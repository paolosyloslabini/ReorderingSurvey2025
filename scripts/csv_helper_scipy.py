"""Merge structural metrics into reordering results using SciPy.

This utility consumes a matrix that has already been permuted by a
reordering technique along with the CSV row emitted by the wrapper
script. This is the SciPy-based implementation for compatibility when
GraphBLAS is not available.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

# Try to import GraphBLAS for better performance, fall back to scipy
try:
    from graphblas import Matrix, io as graphblas_io
    HAS_GRAPHBLAS = True
except ImportError:
    HAS_GRAPHBLAS = False
    import scipy.io
    import scipy.sparse

block_sizes = (4, 8, 16, 32, 64)

def read_mm(path: Path):
    """Load a Matrix Market file, preferring GraphBLAS for performance."""
    if HAS_GRAPHBLAS:
        return graphblas_io.mmread(str(path))
    else:
        return scipy.io.mmread(str(path))


def compute_bandwidth(a) -> int:
    """Return the half-bandwidth of ``a``."""
    if HAS_GRAPHBLAS and hasattr(a, 'to_coo'):
        # GraphBLAS Matrix
        if a.nvals == 0:
            return 0
        rows, cols, _ = a.to_coo()
        if len(rows) == 0:
            return 0
        rows = rows.astype(np.int64)
        cols = cols.astype(np.int64)
        return int(np.abs(rows - cols).max())
    else:
        # SciPy sparse matrix
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
    """Return density of non-empty ``block``×``block`` tiles.
    
    Block density is defined as: total number of nonzero entries in nonzero blocks
    divided by the total area of nonzero blocks.
    """
    if HAS_GRAPHBLAS and hasattr(a, 'to_coo'):
        # GraphBLAS Matrix
        if a.nvals == 0:
            return 0.0
        rows, cols, _ = a.to_coo()
        if len(rows) == 0:
            return 0.0
        rows = rows.astype(np.int64)
        cols = cols.astype(np.int64)
        nnz = a.nvals
    else:
        # SciPy sparse matrix
        if hasattr(a, 'tocoo'):
            coo = a.tocoo()
        else:
            coo = a
        
        if coo.nnz == 0:
            return 0.0
        
        rows = coo.row.astype(np.int64)
        cols = coo.col.astype(np.int64)
        nnz = coo.nnz
    
    # Common block calculation logic
    br = rows // block
    bc = cols // block
    pairs = np.stack([br, bc], axis=1)
    num_nonzero_blocks = np.unique(pairs, axis=0).shape[0]
    
    # Calculate block density: total nonzeros / total area of nonzero blocks
    total_area_nonzero_blocks = num_nonzero_blocks * (block * block)
    return nnz / total_area_nonzero_blocks if total_area_nonzero_blocks > 0 else 0.0


def main(matrix: Path, csv: Path) -> None:
    A = read_mm(matrix)
    df = pd.read_csv(csv)

    # Use the optimal backend for the given matrix type
    backend = "GraphBLAS" if HAS_GRAPHBLAS and hasattr(A, 'to_coo') else "SciPy"
    print(f"Using {backend} backend for matrix operations")

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
