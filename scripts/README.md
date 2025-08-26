Helper utilities and setup scripts. `bootstrap.sh` installs third-party
reorderers by delegating to `bootstrap_ro.sh`, which attempts a module-based
Rabbit Order build before falling back to source tarballs. `reorder_matrix.py`
applies permutations to Matrix Market files, and `csv_helper.py` merges structural metrics into the results using
SuiteSparse:GraphBLAS (default). SciPy versions are available as `*_scipy.py`
for compatibility. `launch_reordering.sh` submits a single reordering
job, while `launch_multiply.sh` submits a single multiplication job given a
reordered results CSV. Install the Python packages listed in
`requirements.txt` before invoking these scripts:

```bash
pip install -r requirements.txt
```
