# Experimental System Design Document

*Revision 0 • July 28 2025*

## 1 Objectives

* **Primary goal:** quantify how classical reordering schemes (e.g. RCM) influence block structure (bandwidth, block‑count/density) and downstream performance of sparse multiplication kernels (e.g. cusparse SpMM) on the SuiteSparse Matrix Collection.
* **Secondary goal:** deliver a fully automated, Slurm‑driven workflow that can be rerun with new techniques or hardware by changing a single YAML/JSON config file.

## 2 High‑Level Pipeline

```text
┌──────────────┐   ┌──────────────────────┐   ┌───────────────────┐
│  Bootstrap   │→ │   Reorder + Metrics   │→ │  Blocked Multiply │
└──────────────┘   └──────────────────────┘   └───────────────────┘
      │                     │                          │
      └── installs repos    └── produces .g & CSV      └── writes CSV
```

Each stage is launched through an **sbatch driver** and may itself spawn job arrays for scalability.

### 2.1 Bootstrap (once per cluster)

| Task          | Details                                                          |
| ------------- | ---------------------------------------------------------------- |
| Load modules  | GCC/14, CUDA/12, Python/3.11, METIS, MKL, cuSPARSE               |
| Clone & build | `Programs/Reordering/<tech>/`, `Programs/Multiplication/<impl>/` |
| Cache dataset | `Raw_Matrices/` downloaded via SuiteSparseDB script              |

### 2.2 Reordering Phase

* **Driver:** `Programs/Reorder.sbatch` (job array on matrices × techniques × param‑sets).
* **Per‑task input**
  `matrix_path reorder_tech param_set_id`
* **Wrapper contract**
  `reordering_<tech>.sh  <mtx>  <permutation.g>  <param_json>`
* **Outputs**

```
Results/Reordering/<MATRIX>/<TECH>_<PARAMSET>/
  ├─ permutation.g              # 1‑based CSR index order
  └─ results.csv                # single‑row, see §4
```

* **Immediate post‑processing**: `scripts/csv_helper.py` merges timing with structural metrics (bandwidth, B4/B8/B16 block‑count, block‑density).

### 2.3 Multiplication Phase

* **Driver:** `Programs/Multiply.sbatch` (job array over reordered matrices × kernels × params).
* **Per‑task input**
  `matrix_dir mult_impl param_set_id`
* **Wrapper contract**
  `operation_<impl>.sh  <matrix_dir>  <param_json>`
* **Outputs**

```
Results/Multiplication/<MATRIX>/<TECH>_<PARAMSET>/<MULT_IMPL>/results.csv
```

Each row encodes a single (matrix, reordering, multiply‑kernel, parameter‑set) trial.

## 3 Directory Layout

```text
project_root/
├── Raw_Matrices/              # static after first sync
├── Programs/
│   ├── exp_config.sh          # cluster‑wide env & paths
│   ├── Reordering/Techniques/reordering_<tech>.sh
│   └── Multiplication/Techniques/operation_<impl>.sh
├── Results/
│   ├── Reordering/
│   └── Multiplication/
└── logs/                      # Slurm stdout/err & JSON summaries
```

## 4 Results CSV Schema (both phases)

| Column                    | Description                           |
| ------------------------- | ------------------------------------- |
| `matrix_name`             | basename of `.mtx` file               |
| `dataset`                 | parent folder in SuiteSparseDB        |
| `n_rows`, `n_cols`, `nnz` | raw matrix stats                      |
| `reorder_type`            | 1D / 2D / None                        |
| `reorder_tech`            | saad, rcm, amd, …                     |
| `reord_param_set`         | semicolon‑sep `key=val`               |
| `reorder_time_ms`         | exclusive wall‑time                   |
| `bandwidth`               | half‑bandwidth after reorder          |
| `block_density`           | dict `{4:δ4;8:δ8;16:δ16}`             |
| `mult_type`               | cusparse, mkl\_spmm, magicube, …      |
| `mult_param_set`          | semicolon‑sep config                  |
| `mult_time_ms`            | average wall‑time                     |
| `gflops`                  | derived from nnz & flop‑model         |
| `mult_metrics`            | cache misses, DRAM BW                 |
| `exit_code`               | 0=success                             |
| `tag`                     | freeform label (git commit, exp‑name) |
| `timestamp`               | ISO‑8601 end‑time                     |

## 5 Slurm Integration

* **Heterogeneous nodes:** GPU kernels request `--gpus-per-task=1`; CPU paths omit GPU flag.
* **Job arrays:**

  ```bash
  # reorder  ➜ M×T×P tasks (≤100k)
  sbatch --array=0-$((N-1)) Reorder.sbatch
  # multiply ➜ #perm × K×P tasks
  sbatch --array=0-$((M-1)) Multiply.sbatch
  ```
* **Dependencies:** multiplication array holds `--dependency=afterok:<reorder-jobid>` to guarantee permutations exist.
* **Resources template:**

  ```bash
  #!/bin/bash
  #SBATCH -A hpc
  #SBATCH -t 02:00:00
  #SBATCH -N 1
  #SBATCH --cpus-per-task=32
  #SBATCH --gpus-per-task=1   # optional
  module source $PROJECT_ROOT/Programs/exp_config.sh
  srun $@
  ```

## 6 Installation & Environment Setup

```bash
# 1. clone repos (pinned commits for reproducibility)
./scripts/bootstrap.sh   # wraps git clone & cmake
# 2. create Python venv + requirements.txt
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt  # numpy, pandas, scipy, suitesparsegraphblas, py-metis
# 3. verify GPU toolkits
nvcc --version  # expect ≥12.2
nvidia-smi      # driver ≥550.XX
```

All compile‑time artefacts are written to `$PROJECT_ROOT/build/` to keep the repo clean.

## 7 Extending the Framework

1. **New reordering technique** → drop a `reordering_<new>.sh` wrapper that obeys the three‑argument contract; add entry in `config/reorder.yml`.
2. **New multiplication kernel** → analogous `operation_<impl>.sh`; register in `config/multiply.yml`.
3. **Additional metrics** → extend `csv_helper.py` with extra columns; no pipeline changes needed.

## 8 Quality & Reproducibility Controls

* All randomised algorithms receive a 64‑bit `seed` passed via param‑set.
* SBATCH scripts emit YAML sidecars with the full module list and environment variables.
* Results CSVs are version‑controlled with DVC for large‑file safety.

## 9 Failure Handling

| Failure             | Detection            | Action                                         |
| ------------------- | -------------------- | ---------------------------------------------- |
| Non‑zero exit code  | wrapper returns ≠0   | mark row with `exit_code`; Slurm retries ×2    |
| Timeout             | Slurm signal         | write `exit_code=124`; escalate to dev channel |
| Corrupt permutation | post‑check in Python | row dropped; matrix flagged for manual review  |

## 10 Appendix A – Minimal Wrapper Prototype

```bash
#!/usr/bin/env bash
# reordering_rcm.sh  <matrix>  <out_perm>  <params_json>
set -euo pipefail
module load suitesparse
python - << 'PY'
import sys, json, scipy.io, scipy.sparse as sp, numpy as np
mtx, out_g, params = sys.argv[1:]
A = scipy.io.mmread(mtx).tocsr()
from scipy.sparse.csgraph import reverse_cuthill_mckee
perm = reverse_cuthill_mckee(A, symmetric_mode=True)
np.savetxt(out_g, perm+1, fmt='%d')
PY
```

---

*End of document*
