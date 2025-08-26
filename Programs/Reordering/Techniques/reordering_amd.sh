#!/usr/bin/env bash
# reordering_amd.sh <matrix> <out_perm> [key=value ...]
# Approximate Minimum Degree reordering using custom implementation
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

# parameters
symmetric="true"

python - << PY
import sys, scipy.io, scipy.sparse as sp, numpy as np
from collections import defaultdict

def amd_ordering(A, symmetric=True):
    """
    Approximate Minimum Degree (AMD) ordering algorithm.
    
    Args:
        A: scipy sparse matrix
        symmetric: whether to treat matrix as symmetric
    
    Returns:
        permutation vector (0-based indices)
    """
    # Convert to CSR format for efficiency
    if not sp.isspmatrix_csr(A):
        A = A.tocsr()
    
    n = A.shape[0]
    
    # For symmetric case, work with the pattern of A + A^T
    if symmetric and A.shape[0] == A.shape[1]:
        # Create symmetric pattern (combine A and A^T patterns)
        A_pattern = A.copy()
        A_pattern.data.fill(1)  # Only care about pattern
        A_sym = A_pattern + A_pattern.T
        A_sym.data.fill(1)  # Ensure all values are 1
        A_work = A_sym
    else:
        # For non-symmetric case, work with A^T * A pattern
        A_work = A.T @ A
        A_work.data.fill(1)
    
    # Convert to adjacency representation
    # Each node maintains its adjacent nodes
    adj = defaultdict(set)
    for i in range(n):
        start_idx = A_work.indptr[i]
        end_idx = A_work.indptr[i + 1]
        for j_idx in range(start_idx, end_idx):
            j = A_work.indices[j_idx]
            if i != j:  # Exclude diagonal
                adj[i].add(j)
                adj[j].add(i)
    
    # AMD algorithm
    eliminated = set()
    ordering = []
    
    for step in range(n):
        # Find node with minimum degree among remaining nodes
        min_degree = float('inf')
        min_node = -1
        
        for node in range(n):
            if node not in eliminated:
                # Count current degree (connections to non-eliminated nodes)
                current_degree = len([neighbor for neighbor in adj[node] 
                                    if neighbor not in eliminated])
                
                if current_degree < min_degree:
                    min_degree = current_degree
                    min_node = node
        
        if min_node == -1:
            # Shouldn't happen, but handle gracefully
            remaining = [i for i in range(n) if i not in eliminated]
            if remaining:
                min_node = remaining[0]
            else:
                break
        
        # Eliminate the minimum degree node
        eliminated.add(min_node)
        ordering.append(min_node)
        
        # Update adjacency for remaining nodes (absorption)
        # When we eliminate min_node, its neighbors become connected to each other
        neighbors = [neighbor for neighbor in adj[min_node] 
                    if neighbor not in eliminated]
        
        # Connect all pairs of neighbors (clique formation)
        for i, node1 in enumerate(neighbors):
            for node2 in neighbors[i+1:]:
                adj[node1].add(node2)
                adj[node2].add(node1)
        
        # Remove eliminated node from all adjacency lists
        for neighbor in adj[min_node]:
            adj[neighbor].discard(min_node)
        adj[min_node].clear()
    
    return np.array(ordering, dtype=int)

# Read arguments
mtx_file = "$1"
out_perm = "$2"
symmetric = "$symmetric"

# Load matrix
A = scipy.io.mmread(mtx_file).tocsr()

# Apply AMD reordering
perm = amd_ordering(A, symmetric=(symmetric.lower() == "true"))

# Save permutation (1-based indices)
np.savetxt(out_perm, perm + 1, fmt='%d')
PY