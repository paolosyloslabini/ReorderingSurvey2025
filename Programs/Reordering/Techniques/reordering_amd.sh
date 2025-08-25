#!/usr/bin/env bash
# reordering_amd.sh <matrix> <out_perm> [key=value ...]
# Approximate Minimum Degree reordering using SciPy
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

# parameters
symmetric="true"

python - << PY
import sys, scipy.io, scipy.sparse as sp, numpy as np
from scipy.sparse.csgraph import connected_components

# Read arguments
mtx_file = "$1"
out_perm = "$2"
symmetric = "$symmetric"

def amd_ordering(A, symmetric_mode=True):
    """
    Approximate Minimum Degree ordering implementation.
    
    This is a simplified AMD algorithm that greedily eliminates vertices
    with minimum degree to reduce fill-in during sparse factorization.
    """
    # Convert to CSR format and ensure it's symmetric if needed
    if not sp.isspmatrix_csr(A):
        A = A.tocsr()
    
    n = A.shape[0]
    if n != A.shape[1]:
        raise ValueError("Matrix must be square for AMD ordering")
    
    # If symmetric mode, ensure the matrix is symmetric
    if symmetric_mode:
        A = A + A.T
        A.data = np.ones_like(A.data)  # Make it unweighted
    
    # Convert to adjacency matrix (remove diagonal, make binary)
    A.setdiag(0)
    A.eliminate_zeros()
    A.data = np.ones_like(A.data)
    
    # Handle disconnected components
    n_components, labels = connected_components(A, directed=not symmetric_mode)
    
    ordering = []
    
    # Process each component separately
    for comp in range(n_components):
        comp_nodes = np.where(labels == comp)[0]
        if len(comp_nodes) == 1:
            ordering.extend(comp_nodes)
            continue
            
        # Extract submatrix for this component
        comp_A = A[np.ix_(comp_nodes, comp_nodes)]
        
        # AMD algorithm for this component
        comp_ordering = _amd_component(comp_A)
        
        # Map back to original indices
        ordering.extend(comp_nodes[comp_ordering])
    
    return np.array(ordering)

def _amd_component(A):
    """AMD algorithm for a single connected component."""
    n = A.shape[0]
    if n <= 1:
        return np.arange(n)
    
    # Keep track of eliminated nodes
    eliminated = np.zeros(n, dtype=bool)
    ordering = []
    
    # Create a copy to modify
    graph = A.copy().tolil()
    
    for step in range(n):
        # Find remaining nodes
        remaining = np.where(~eliminated)[0]
        if len(remaining) == 0:
            break
            
        if len(remaining) == 1:
            ordering.append(remaining[0])
            break
        
        # Compute current degrees for remaining nodes
        degrees = np.array([len(graph.rows[i]) for i in remaining])
        
        # Find node with minimum degree (break ties by smallest index)
        min_degree_idx = np.argmin(degrees)
        node = remaining[min_degree_idx]
        
        # Add to ordering
        ordering.append(node)
        eliminated[node] = True
        
        # Update graph: connect all neighbors of eliminated node
        neighbors = list(graph.rows[node])
        
        # Remove eliminated node from all neighbor lists
        for neighbor in neighbors:
            if not eliminated[neighbor]:
                if node in graph.rows[neighbor]:
                    graph.rows[neighbor].remove(node)
                    graph.data[neighbor].remove(1)
        
        # Connect all pairs of neighbors (clique completion)
        for i, n1 in enumerate(neighbors):
            if eliminated[n1]:
                continue
            for n2 in neighbors[i+1:]:
                if eliminated[n2]:
                    continue
                if n1 != n2:
                    # Add edge n1-n2 if not present
                    if n2 not in graph.rows[n1]:
                        graph.rows[n1].append(n2)
                        graph.data[n1].append(1)
                    if n1 not in graph.rows[n2]:
                        graph.rows[n2].append(n1) 
                        graph.data[n2].append(1)
        
        # Clear eliminated node's adjacency
        graph.rows[node] = []
        graph.data[node] = []
    
    return np.array(ordering)

# Load matrix
A = scipy.io.mmread(mtx_file).tocsr()

# Apply AMD reordering
perm = amd_ordering(A, symmetric_mode=(symmetric.lower() == "true"))

# Save permutation (1-based indices)
np.savetxt(out_perm, perm + 1, fmt='%d')
PY