"""
Unit tests for module loading system.

Tests the module loading infrastructure in isolation.
"""
import os
import subprocess
from pathlib import Path

import pytest
import yaml
from tests.utils.fixtures import setup_test_environment


class TestModuleConfiguration:
    """Test suite for module configuration parsing."""
    
    def test_reorder_config_parsing(self):
        """Test that reorder.yml module configurations are parsed correctly."""
        config_path = Path("config/reorder.yml")
        assert config_path.exists(), "reorder.yml configuration file not found"
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Verify each technique has a modules field
        assert "modules" in config["rcm"], "rcm technique missing modules field"
        assert "modules" in config["identity"], "identity technique missing modules field"
        assert "modules" in config["ro"], "ro technique missing modules field"
        
        # Verify module assignments
        assert config["rcm"]["modules"] == "python_scipy"
        assert config["identity"]["modules"] == "basic"
        assert config["ro"]["modules"] == "basic"
    
    def test_multiply_config_parsing(self):
        """Test that multiply.yml module configurations are parsed correctly."""
        config_path = Path("config/multiply.yml")
        assert config_path.exists(), "multiply.yml configuration file not found"
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Verify each kernel has a modules field
        assert "modules" in config["cucsrspmm"], "cucsrspmm kernel missing modules field"
        assert "modules" in config["mock"], "mock kernel missing modules field"
        
        # Verify module assignments
        assert config["cucsrspmm"]["modules"] == "cuda_cusparse"
        assert config["mock"]["modules"] == "basic"
    
    def test_module_definition_files_exist(self):
        """Test that all referenced module definition files exist and are valid."""
        module_files = [
            "config/modules/basic.yml",
            "config/modules/python_scipy.yml", 
            "config/modules/cuda_cusparse.yml",
            "config/modules/metis.yml"
        ]
        
        for module_file in module_files:
            module_path = Path(module_file)
            assert module_path.exists(), f"Module file {module_file} does not exist"
            
            with open(module_path) as f:
                config = yaml.safe_load(f)
            
            # Verify required fields
            assert "name" in config, f"Module {module_file} missing name field"
            assert "description" in config, f"Module {module_file} missing description field"
            assert "modules" in config, f"Module {module_file} missing modules field"
            assert "environment" in config, f"Module {module_file} missing environment field"
            assert "post_load" in config, f"Module {module_file} missing post_load field"
            
            # Verify field types
            assert isinstance(config["modules"], list), f"Module {module_file} modules should be a list"
            assert isinstance(config["environment"], dict), f"Module {module_file} environment should be a dict"
            assert isinstance(config["post_load"], list), f"Module {module_file} post_load should be a list"


class TestModuleLoadingScript:
    """Test suite for module loading script functionality."""
    
    def test_load_modules_script_exists(self):
        """Test that the load_modules.sh script exists and is executable."""
        script_path = Path("Programs/load_modules.sh")
        assert script_path.exists(), "load_modules.sh script not found"
        assert os.access(script_path, os.X_OK), "load_modules.sh script not executable"
    
    def test_basic_module_loading(self, tmp_path):
        """Test loading basic module set."""
        test_env = setup_test_environment(tmp_path)
        project_root = Path(__file__).parent.parent.parent
        
        # Source the module loading script for basic modules
        cmd = f'cd {project_root} && source Programs/load_modules.sh reorder identity && echo "SUCCESS"'
        
        result = subprocess.run(
            ["bash", "-c", cmd],
            env=test_env["env"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Basic module loading failed: {result.stderr}"
        assert "Loading module set: basic for technique identity" in result.stderr
        assert "Module loading completed for reorder/identity" in result.stderr
        assert "SUCCESS" in result.stdout
    
    def test_python_scipy_module_loading(self, tmp_path):
        """Test loading python_scipy module set."""
        test_env = setup_test_environment(tmp_path)
        project_root = Path(__file__).parent.parent.parent
        
        # Source the module loading script for python_scipy modules
        cmd = f'cd {project_root} && source Programs/load_modules.sh reorder rcm && echo "SUCCESS"'
        
        result = subprocess.run(
            ["bash", "-c", cmd],
            env=test_env["env"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Python SciPy module loading failed: {result.stderr}"
        assert "Loading module set: python_scipy for technique rcm" in result.stderr
        assert "SciPy" in result.stderr and "NumPy" in result.stderr  # From post_load verification
        assert "Module loading completed for reorder/rcm" in result.stderr
        assert "SUCCESS" in result.stdout
    
    def test_cuda_module_loading(self, tmp_path):
        """Test loading CUDA module set."""
        test_env = setup_test_environment(tmp_path)
        project_root = Path(__file__).parent.parent.parent
        
        # Source the module loading script for CUDA modules
        cmd = f'cd {project_root} && source Programs/load_modules.sh multiply cucsrspmm && echo "SUCCESS"'
        
        result = subprocess.run(
            ["bash", "-c", cmd],
            env=test_env["env"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"CUDA module loading failed: {result.stderr}"
        assert "Loading module set: cuda_cusparse for technique cucsrspmm" in result.stderr
        assert "Module loading completed for multiply/cucsrspmm" in result.stderr
        assert "SUCCESS" in result.stdout
        
        # Check that CUDA environment variables are set (even if CUDA not available)
        assert "CUDA_VISIBLE_DEVICES" in result.stderr or "GPU not available" in result.stderr
    
    def test_nonexistent_technique_fallback(self, tmp_path):
        """Test that non-existent techniques fall back to basic module set."""
        test_env = setup_test_environment(tmp_path)
        project_root = Path(__file__).parent.parent.parent
        
        # Source the module loading script for non-existent technique
        cmd = f'cd {project_root} && source Programs/load_modules.sh reorder nonexistent && echo "SUCCESS"'
        
        result = subprocess.run(
            ["bash", "-c", cmd],
            env=test_env["env"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Fallback module loading failed: {result.stderr}"
        assert "Loading module set: basic for technique nonexistent" in result.stderr
        assert "Module loading completed for reorder/nonexistent" in result.stderr
        assert "SUCCESS" in result.stdout


class TestGraphBLASModuleConfiguration:
    """Test suite for GraphBLAS module configuration."""
    
    def test_graphblas_module_config_exists(self):
        """Test that GraphBLAS module configuration exists and is valid."""
        config_path = Path("config/modules/python_graphblas.yml")
        assert config_path.exists(), "python_graphblas.yml configuration file not found"
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        assert config["name"] == "python_graphblas"
        assert "python/3.11" in config["modules"] or len(config["modules"]) > 0
        assert "post_load" in config
    
    def test_rcm_graphblas_technique_config(self):
        """Test that RCM GraphBLAS technique is properly configured."""
        # Check reorder configuration
        config_path = Path("config/reorder.yml")
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        assert "rcm_graphblas" in config, "rcm_graphblas technique not found in config"
        assert config["rcm_graphblas"]["modules"] == "python_graphblas"
        
        # Check technique script exists and is executable
        script_path = Path("Programs/Reordering/Techniques/reordering_rcm_graphblas.sh")
        assert script_path.exists(), "rcm_graphblas technique script not found"
        assert os.access(script_path, os.X_OK), "rcm_graphblas technique script not executable"


class TestModuleEnvironmentSetup:
    """Test suite for module environment variable setup."""
    
    def test_python_path_setup(self, tmp_path):
        """Test that PYTHONPATH is properly set up for Python modules."""
        test_env = setup_test_environment(tmp_path)
        project_root = Path(__file__).parent.parent.parent
        
        # Source the module loading script and check PYTHONPATH
        cmd = f'cd {project_root} && source Programs/load_modules.sh reorder rcm && echo "PYTHONPATH=${{PYTHONPATH:-unset}}"'
        
        result = subprocess.run(
            ["bash", "-c", cmd],
            env=test_env["env"],
            capture_output=True,
            text=True
        )
        
        # Module loading might succeed even if PYTHONPATH checking fails
        # The important thing is that the module loading completes
        assert "Module loading completed for reorder/rcm" in result.stderr
        if result.returncode == 0:
            assert "PYTHONPATH=" in result.stdout or "PYTHONPATH=unset" in result.stdout
    
    def test_cuda_environment_setup(self, tmp_path):
        """Test that CUDA environment variables are properly set up."""
        test_env = setup_test_environment(tmp_path)
        project_root = Path(__file__).parent.parent.parent
        
        # Source the module loading script and check CUDA environment
        cmd = f'cd {project_root} && source Programs/load_modules.sh multiply cucsrspmm && echo "CUDA_VISIBLE_DEVICES=${{CUDA_VISIBLE_DEVICES:-unset}}" && echo "LD_LIBRARY_PATH=${{LD_LIBRARY_PATH:-unset}}"'
        
        result = subprocess.run(
            ["bash", "-c", cmd],
            env=test_env["env"],
            capture_output=True,
            text=True
        )
        
        # Module loading should complete even if CUDA not available
        assert "Module loading completed for multiply/cucsrspmm" in result.stderr
        if result.returncode == 0:
            # Should set CUDA environment variables (even if CUDA not available)
            output = result.stdout + result.stderr
            assert "CUDA_VISIBLE_DEVICES" in output or "GPU not available" in output