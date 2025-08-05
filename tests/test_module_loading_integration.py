import os
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import pytest


def test_module_loading_integration(tmp_path):
    """Test that reordering works with module loading enabled"""
    # Create a test matrix
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

    # Run the reordering driver for identity (which should use basic modules)
    env = os.environ.copy()
    results_dir = tmp_path / "results"
    env["RESULTS_DIR"] = str(results_dir)
    
    # Capture both stdout and stderr to verify module loading messages
    result = subprocess.run(
        ["bash", "Programs/Reorder.sbatch", str(mtx), "identity"],
        capture_output=True,
        text=True,
        env=env,
    )
    
    # Check that the command succeeded
    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
    
    # Verify module loading messages in stderr
    assert "Loading module set: basic for technique identity" in result.stderr
    assert "Module loading completed for reorder/identity" in result.stderr
    
    # Verify output files were created
    out_dir = results_dir / "Reordering" / "matrix" / "identity_default"
    perm = (out_dir / "permutation.g").read_text().split()
    assert perm == ["1", "2", "3", "4"]
    
    csv = out_dir / "results.csv"
    assert csv.is_file()
    
    df = pd.read_csv(csv)
    assert df.loc[0, "matrix_name"] == "matrix"
    assert df.loc[0, "reorder_tech"] == "identity"
    assert df.loc[0, "exit_code"] == 0


def test_module_loading_rcm_technique(tmp_path):
    """Test that RCM reordering works with python_scipy modules"""
    # Create a test matrix  
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

    # Run the reordering driver for RCM (which should use python_scipy modules)
    env = os.environ.copy()
    results_dir = tmp_path / "results"
    env["RESULTS_DIR"] = str(results_dir)
    
    result = subprocess.run(
        ["bash", "Programs/Reorder.sbatch", str(mtx), "rcm"],
        capture_output=True,
        text=True,
        env=env,
    )
    
    # Check that the command succeeded
    assert result.returncode == 0, f"Command failed with stderr: {result.stderr}"
    
    # Verify module loading messages
    assert "Loading module set: python_scipy for technique rcm" in result.stderr
    assert "SciPy" in result.stderr and "NumPy" in result.stderr  # From post_load verification
    
    # Verify output files were created
    out_dir = results_dir / "Reordering" / "matrix" / "rcm_default"
    assert (out_dir / "permutation.g").exists()
    assert (out_dir / "results.csv").exists()
    
    df = pd.read_csv(out_dir / "results.csv")
    assert df.loc[0, "reorder_tech"] == "rcm"
    assert df.loc[0, "exit_code"] == 0


def test_module_configuration_parsing():
    """Test that module configurations are parsed correctly"""
    import yaml
    
    # Test reorder.yml parsing
    with open("config/reorder.yml") as f:
        reorder_config = yaml.safe_load(f)
    
    # Verify each technique has a modules field
    assert "modules" in reorder_config["rcm"]
    assert "modules" in reorder_config["identity"]
    assert "modules" in reorder_config["ro"]
    
    assert reorder_config["rcm"]["modules"] == "python_scipy"
    assert reorder_config["identity"]["modules"] == "basic"
    assert reorder_config["ro"]["modules"] == "basic"
    
    # Test multiply.yml parsing
    with open("config/multiply.yml") as f:
        multiply_config = yaml.safe_load(f)
    
    assert "modules" in multiply_config["cucsrspmm"]
    assert "modules" in multiply_config["mock"]
    
    assert multiply_config["cucsrspmm"]["modules"] == "cuda_cusparse"
    assert multiply_config["mock"]["modules"] == "basic"


def test_module_definition_files():
    """Test that all referenced module definition files exist and are valid"""
    import yaml
    
    module_files = [
        "config/modules/basic.yml",
        "config/modules/python_scipy.yml", 
        "config/modules/cuda_cusparse.yml",
        "config/modules/metis.yml"
    ]
    
    for module_file in module_files:
        assert Path(module_file).exists(), f"Module file {module_file} does not exist"
        
        with open(module_file) as f:
            config = yaml.safe_load(f)
        
        # Verify required fields
        assert "name" in config
        assert "description" in config
        assert "modules" in config
        assert "environment" in config
        assert "post_load" in config
        
        # Verify modules is a list
        assert isinstance(config["modules"], list)
        # Verify environment is a dict  
        assert isinstance(config["environment"], dict)
        # Verify post_load is a list
        assert isinstance(config["post_load"], list)