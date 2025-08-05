import os
import subprocess
import pandas as pd


def test_mock_multiplication(tmp_path):
    """Test that the mock multiplication works correctly"""
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

    # Run mock multiplication
    subprocess.run(
        [
            "bash", "Programs/Multiply.sbatch",
            str(csv_file), "mock", "alpha=1.0"
        ],
        check=True,
        env=env,
    )

    # Check mock multiplication results
    mult_dir = results_dir / "Multiplication" / "matrix" / "identity_default" / "mock"
    mult_csv = mult_dir / "results.csv"
    assert mult_csv.is_file()

    df = pd.read_csv(mult_csv)
    assert df.loc[0, "mult_type"] == "mock"
    assert df.loc[0, "mult_param_set"] == "alpha=1.0"
    assert df.loc[0, "exit_code"] == 0
    assert df.loc[0, "mult_time_ms"] > 0  # Should have some timing
    
    print("Mock multiplication test passed!")


def test_multiply_config_loading():
    """Test that the multiply.yml config can be loaded correctly"""
    import yaml
    
    with open("config/multiply.yml", 'r') as f:
        config = yaml.safe_load(f)
    
    # Check cucsrspmm configuration
    assert "cucsrspmm" in config
    assert config["cucsrspmm"]["gpus"] == 1
    assert "params" in config["cucsrspmm"]
    assert len(config["cucsrspmm"]["params"]) >= 3  # Should have multiple parameter sets
    
    # Check that we have the new num_cols_B parameter
    params_with_cols_B = [p for p in config["cucsrspmm"]["params"] if "num_cols_B" in p]
    assert len(params_with_cols_B) >= 3  # Should have multiple settings
    
    # Check mock configuration
    assert "mock" in config
    assert config["mock"]["gpus"] == 0
    
    print("Multiply config test passed!")