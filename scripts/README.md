Helper utilities and setup scripts. `bootstrap.sh` installs third-party
reorderers. `reorder_matrix.py` applies permutations to Matrix Market
files, and `csv_helper.py` merges structural metrics into the results using
SuiteSparse:GraphBLAS. `launch_reordering.sh` submits a single reordering
job, while `launch_multiply.sh` submits a single multiplication job given a
reordered matrix directory. Install the Python packages listed in
`requirements.txt` before invoking these scripts:

```bash
pip install -r requirements.txt
```
