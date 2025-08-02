import os
import subprocess
from pathlib import Path

import pandas as pd


def test_identity_reorder(tmp_path):
    # Create a tiny 2x2 diagonal matrix in Matrix Market format
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    mtx = dataset / "matrix.mtx"
    mtx.write_text("""%%MatrixMarket matrix coordinate real general\n2 2 2\n1 1 1\n2 2 1\n""")

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
    assert perm == ["1", "2"]

    csv = out_dir / "results.csv"
    assert csv.is_file()
    df = pd.read_csv(csv)
    assert df.loc[0, "reorder_tech"] == "identity"
    assert df.loc[0, "exit_code"] == 0
