import os
import subprocess
from pathlib import Path

import pandas as pd


def test_identity_reorder(tmp_path):
    # Create a larger 4x4 diagonal matrix in Matrix Market format
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    mtx = dataset / "matrix.mtx"
    mtx.write_text(
        """%%MatrixMarket matrix coordinate real general
4 4 4
1 1 1
2 2 1
3 3 1
4 4 1
"""
    )

    # Run the reordering driver with our identity wrapper
    env = os.environ.copy()
    results_dir = tmp_path / "results"
    env["RESULTS_DIR"] = str(results_dir)
    subprocess.run(
        ["bash", "Programs/Reorder.sbatch", str(mtx), "identity"],
        check=True,
        env=env,
    )

    # Verify that the permutation and results CSV were produced
    out_dir = results_dir / "Reordering" / "matrix" / "identity_default"
    perm = (out_dir / "permutation.g").read_text().split()
    assert perm == ["1", "2", "3", "4"]

    csv = out_dir / "results.csv"
    assert csv.is_file()

    # Print the raw CSV contents for debugging
    print(csv.read_text())

    df = pd.read_csv(csv)
    assert df.loc[0, "matrix_name"] == "matrix"
    assert df.loc[0, "dataset"] == "dataset"
    assert df.loc[0, "n_rows"] == 4
    assert df.loc[0, "n_cols"] == 4
    assert df.loc[0, "nnz"] == 4
    assert df.loc[0, "reorder_type"] == "1D"
    assert df.loc[0, "reorder_tech"] == "identity"
    assert pd.isna(df.loc[0, "reord_param_set"])
    assert df.loc[0, "exit_code"] == 0
