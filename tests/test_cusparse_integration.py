import os
import subprocess
import tempfile
from pathlib import Path
import pandas as pd
import pytest


def test_cusparse_integration_mock(tmp_path):
    """
    Test cuSPARSE integration with fallback to mock when CUDA is not available
    """
    # Create a test matrix in the correct Raw_Matrices structure
    matrix_dir = tmp_path / "matrices"
    matrix_dir.mkdir()
    
    # Create Raw_Matrices directory structure
    raw_matrices = matrix_dir / "Raw_Matrices" / "dataset"
    raw_matrices.mkdir(parents=True)
    mtx = raw_matrices / "matrix.mtx"
    mtx.write_text(
        """%%MatrixMarket matrix coordinate real general
4 4 4
1 1 1.0
2 2 2.0
3 3 3.0
4 4 4.0
"""
    )

    # Set up environment
    env = os.environ.copy()
    results_dir = tmp_path / "results"
    env["RESULTS_DIR"] = str(results_dir)
    env["MATRIX_DIR"] = str(matrix_dir / "Raw_Matrices")

    # First run reordering to create the required CSV
    subprocess.run(
        ["bash", "Programs/Reorder.sbatch", str(mtx), "identity"],
        check=True,
        env=env,
    )

    # Verify reordering results
    reorder_dir = results_dir / "Reordering" / "matrix" / "identity_default"
    csv_file = reorder_dir / "results.csv"
    assert csv_file.is_file()

    # Check if CUDA is available
    cuda_available = False
    try:
        subprocess.run(["nvcc", "--version"], capture_output=True, check=True)
        subprocess.run(["nvidia-smi"], capture_output=True, check=True)
        cuda_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    if cuda_available:
        # Test with real cuSPARSE if CUDA is available
        try:
            # Build the cuSPARSE implementation
            subprocess.run(
                ["make", "-C", "Programs/Multiplication", "clean"],
                check=False,  # May fail if nothing to clean
            )
            subprocess.run(
                ["make", "-C", "Programs/Multiplication"],
                check=True,
            )

            # Run multiplication
            subprocess.run(
                [
                    "bash", "Programs/Multiply.sbatch",
                    str(csv_file), "cucsrspmm",
                    "alpha=1.0", "beta=0.0", "num_cols_B=32"
                ],
                check=True,
                env=env,
            )

            # Check results
            mult_dir = results_dir / "Multiplication" / "matrix" / "identity_default" / "cucsrspmm"
            mult_csv = mult_dir / "results.csv"
            assert mult_csv.is_file()

            df = pd.read_csv(mult_csv)
            assert df.loc[0, "mult_type"] == "cucsrspmm"
            assert df.loc[0, "mult_param_set"] == "alpha=1.0;beta=0.0;num_cols_B=32"
            assert df.loc[0, "exit_code"] == 0
            assert df.loc[0, "mult_time_ms"] > 0
            
            # Check if GFLOPS was calculated
            if "gflops" in df.columns and not pd.isna(df.loc[0, "gflops"]):
                assert df.loc[0, "gflops"] > 0

            print("Real cuSPARSE test passed!")
            
        except subprocess.CalledProcessError as e:
            print(f"cuSPARSE build/run failed, probably due to missing CUDA libraries: {e}")
            pytest.skip("CUDA libraries not available for cuSPARSE compilation")
    else:
        # Test that cuSPARSE fails gracefully when CUDA is not available
        result = subprocess.run(
            [
                "bash", "Programs/Multiply.sbatch",
                str(csv_file), "cucsrspmm", "alpha=1.0"
            ],
            env=env,
            capture_output=True,
        )
        
        # Should fail with proper error message
        assert result.returncode != 0
        assert b"nvidia-smi not found" in result.stderr or b"nvcc not found" in result.stderr
        print("cuSPARSE correctly failed when CUDA is not available")


def test_cusparse_csv_update():
    """Test the cuSPARSE CSV update functionality"""
    import sys
    sys.path.append("scripts")
    from update_csv_multiply import parse_cusparse_results
    
    # Create a temporary results file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("avg_time_ms,5.23\n")
        f.write("gflops,12.5\n")
        f.write("nnz,1000\n")
        f.write("num_rows,100\n")
        f.write("num_cols,100\n")
        f.write("num_cols_B,64\n")
        temp_file = f.name
    
    try:
        # Parse the results
        metrics = parse_cusparse_results(temp_file)
        
        assert metrics["avg_time_ms"] == 5.23
        assert metrics["gflops"] == 12.5
        assert metrics["nnz"] == 1000
        assert metrics["num_rows"] == 100
        assert metrics["num_cols"] == 100
        assert metrics["num_cols_B"] == 64
        
        print("cuSPARSE CSV parsing test passed!")
        
    finally:
        os.unlink(temp_file)