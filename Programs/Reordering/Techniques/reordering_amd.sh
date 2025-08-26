#!/usr/bin/env bash
# reordering_amd.sh <matrix> <out_perm> [key=value ...]
# Approximate Minimum Degree (AMD) reordering using SuiteSparse
set -euo pipefail

# Load cluster environment
source "$(dirname "$0")/../../exp_config.sh"

# Parse parameters (none for basic AMD)
# Could add aggressive=true/false in the future

python3 - "$1" "$2" << 'PY'
import sys
import ctypes
import numpy as np
from scipy.io import mmread
from scipy.sparse import csc_matrix

# Read arguments from bash
mtx_file = sys.argv[1]
out_perm = sys.argv[2]

# Load matrix in coordinate format and convert to CSC
A_mm = mmread(mtx_file)
if hasattr(A_mm, 'tocsc'):
    A_csc = A_mm.tocsc()
else:
    A_csc = csc_matrix(A_mm)

n = A_csc.shape[0]
if n != A_csc.shape[1]:
    raise ValueError(f"Matrix must be square, got {A_csc.shape}")

# Ensure 32-bit indices for AMD (SuiteSparse AMD expects int32)
Ap = A_csc.indptr.astype(np.int32)
Ai = A_csc.indices.astype(np.int32)

# Load AMD library
try:
    libamd = ctypes.CDLL("libamd.so.3")
except OSError:
    try:
        libamd = ctypes.CDLL("libamd.so")
    except OSError:
        raise RuntimeError("AMD library not found. Install libsuitesparse-dev")

# Define AMD function signature
# int amd_order(int32_t n, const int32_t Ap[], const int32_t Ai[], 
#               int32_t P[], double Control[], double Info[])
libamd.amd_order.argtypes = [
    ctypes.c_int32,                    # n
    ctypes.POINTER(ctypes.c_int32),    # Ap
    ctypes.POINTER(ctypes.c_int32),    # Ai  
    ctypes.POINTER(ctypes.c_int32),    # P
    ctypes.POINTER(ctypes.c_double),   # Control
    ctypes.POINTER(ctypes.c_double)    # Info
]
libamd.amd_order.restype = ctypes.c_int

# Define AMD constants
AMD_CONTROL = 5
AMD_INFO = 20
AMD_OK = 0
AMD_OK_BUT_JUMBLED = 1

# Prepare arrays
P = np.zeros(n, dtype=np.int32)
Control = np.zeros(AMD_CONTROL, dtype=np.float64)
Info = np.zeros(AMD_INFO, dtype=np.float64)

# Set default control parameters (as per AMD documentation)
# Control[0] = dense row control (default 10.0)
# Control[1] = dense column control (default 10.0) 
# Control[2] = aggressive absorption (default 1.0 = yes)
Control[0] = 10.0
Control[1] = 10.0  
Control[2] = 1.0

# Call AMD ordering
result = libamd.amd_order(
    ctypes.c_int32(n),
    Ap.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
    Ai.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
    P.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
    Control.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
    Info.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
)

# Check result
if result == AMD_OK:
    print("AMD ordering completed successfully", file=sys.stderr)
elif result == AMD_OK_BUT_JUMBLED:
    print("AMD ordering completed (matrix was jumbled)", file=sys.stderr)
else:
    raise RuntimeError(f"AMD ordering failed with code {result}")

# Save permutation (convert to 1-based indices as per repository convention)
np.savetxt(out_perm, P + 1, fmt='%d')
PY