# TOOLS.md – Algorithms Under Test

*Revision 0 • July 28 2025*

This file defines **canonical handles**, human-readable names, and short descriptions of every algorithm that will be executed by the experimental pipeline (see `Experiment Design`). Handles are the **exact** strings that appear in `config/reorder.yml` and `config/multiply.yml` as well as in the results CSVs.

## 1 Reordering Techniques

| Handle      | Full name                                         | Class                     | Status                    |
| ---------- | ------------------------------------------------- | ------------------------- | ------------------------- |
| `identity` | Identity (no reordering)                          | Testing                   | ✅ Implemented            |
| `rcm`      | Reverse Cuthill-McKee                             | Bandwidth                 | ✅ Implemented            |
| `rcm_graphblas` | Reverse Cuthill-McKee (GraphBLAS-optimized)     | Bandwidth                 | ✅ Implemented            |
| `ro`       | Rabbit Order                                      | Block-oriented            | ✅ Implemented            |
| `amd`      | Approximate Minimum Degree                        | Fill-in / bandwidth       | 🟡 Planned (High Priority) |
| `nd`       | Nested Dissection                                 | Fill-in / partition-based | 🟡 Planned (High Priority) |
| `mgp`      | Multilevel Graph Partitioning (METIS)             | Partitioning              | 🟡 Planned (Medium)        |
| `mhgp`     | Multilevel Hypergraph Partitioning (PaToH/hMETIS) | Partitioning              | 🟡 Planned (Medium)        |
| `gco`      | Gray Code Ordering                                | Locality / blocking       | 🟡 Planned (Low)           |
| `ssr`      | Saad's Similarity-based Reordering                | Row-similarity clustering | 🟡 Planned (Low)           |
| `groot`    | Groot                                             | GPU / tensor-core aware   | 🟡 Planned (Low)           |

> **Implementation note** The `Programs/Reordering/Techniques/` directory must contain a `reordering_<handle>.sh` wrapper for each handle that honours the three-argument contract defined in the design document.

## 2 Sparse Multiplication Kernels

| Handle      | Implementation                      | Target HW     | Status             |
| ----------- | ----------------------------------- | ------------- | ------------------ |
| `mock`      | Mock operation for testing          | CPU           | ✅ Implemented     |
| `cucsrspmm` | NVIDIA cuSPARSE CSR SpMM            | GPU (CUDA)    | ✅ Implemented     |
| `csrcusparse` | Direct CSR cuSPARSE multiplication | GPU (CUDA)    | ✅ Implemented     |
| `cucsrspmv` | NVIDIA cuSPARSE CSR SpMV            | GPU (CUDA)    | 🟡 Planned (High)  |
| `cucbrspmm` | NVIDIA cuSPARSE BSR SpMM            | GPU (CUDA)    | 🟡 Planned (High)  |
| `cucbrspmv` | NVIDIA cuSPARSE BSR SpMV            | GPU (CUDA)    | 🟡 Planned (Medium)|
| `aspt`      | ASpT (Adaptive SpMM GPU)            | GPU           | 🟡 Planned (Medium)|
| `magicube`  | Magicube                            | GPU           | 🟡 Planned (Medium)|
| `dasp`      | DASP                                | GPU           | 🟡 Planned (Low)   |
| `smat`      | SMaT                                | CPU/GPU       | 🟡 Planned (Low)   |

> **Implementation note** Each kernel is wrapped by `operation_<handle>.sh` residing in `Programs/Multiplication/Techniques/`.

## 3 Adding New Tools

1. Choose a short lowercase **handle** that is unique.
2. Implement the wrapper script (`reordering_*.sh` or `operation_*.sh`).
3. Register the handle in `TOOLS.md`, `config/*.yml`, and update the CI matrix.

---

*End of TOOLS.md*