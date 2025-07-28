# TOOLS.md – Algorithms Under Test

*Revision 0 • July 28 2025*

This file defines **canonical handles**, human‑readable names, and short descriptions of every algorithm that will be executed by the experimental pipeline (see `Experiment Design`).  Handles are the **exact** strings that appear in `config/reorder.yml` and `config/multiply.yml` as well as in the results CSVs.

## 1 Reordering Techniques

| Handle  | Full name                                         | Class                     | Rationale / survey reference                                              |
| ------- | ------------------------------------------------- | ------------------------- | ------------------------------------------------------------------------- |
| `amd`   | Approximate Minimum Degree                        | Fill‑in / bandwidth       | |
| `rcm`   | Reverse Cuthill‑McKee                             | Bandwidth                 | |
| `nd`    | Nested Dissection                                 | Fill‑in / partition‑based | |
| `mgp`   | Multilevel Graph Partitioning (METIS)             | Partitioning              | |
| `mhgp`  | Multilevel Hypergraph Partitioning (PaToH/hMETIS) | Partitioning              | |
| `ro`    | Rabbit Order                                      | Block‑oriented            | |
| `gco`   | Gray Code Ordering                                | Locality / blocking       | |
| `ssr`   | Saad’s Similarity‑based Reordering                | Row‑similarity clustering | |
| `groot` | Groot                                             | GPU / tensor‑core aware   | |

> **Implementation note** The `Programs/Reordering/Techniques/` directory must contain a `reordering_<handle>.sh` wrapper for each handle that honours the three‑argument contract defined in the design document.

## 2 Sparse Multiplication Kernels

| Handle     | Implementation             | Target HW             | Source / survey reference                            |
| ---------- | -------------------------- | --------------------- | ---------------------------------------------------- |
| `cucsrspmm` | NVIDIA cuSPARSE CSR SpMM       | GPU (CUDA)            | |
| `cucsrspmv` | NVIDIA cuSPARSE CSR SpMV       | GPU (CUDA)            | |
| `cucbrspmm` | NVIDIA cuSPARSE BSR SpMM       | GPU (CUDA)            | |
| `cucbrspmv` | NVIDIA cuSPARSE BSR SpMV       | GPU (CUDA)            | |
| `aspt`     | ASpT (Adaptive SpMM GPU)   | GPU                   | |
| `magicube` | Magicube                   | GPU                   | |
| `dasp`     | DASP                       | GPU                   | |
| `smat`     | SMaT                       | CPU/GPU (OpenMP/CUDA) | |

> **Implementation note** Each kernel is wrapped by `operation_<handle>.sh` residing in `Programs/Multiplication/Techniques/`.

## 3 Adding New Tools

1. Choose a short lowercase **handle** that is unique.
2. Implement the wrapper script (`reordering_*.sh` or `operation_*.sh`).
3. Register the handle in `TOOLS.md`, `config/*.yml`, and update the CI matrix.

---

*End of TOOLS.md*
