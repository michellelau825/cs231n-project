#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def get_env_python_path():
    """Get the Python path from the active environment"""
    # Try conda first
    conda_prefix = os.environ.get('CONDA_PREFIX')
    if conda_prefix:
        python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
        site_packages = Path(conda_prefix) / "lib" / python_version / "site-packages"
        if site_packages.exists():
            return str(site_packages)
    
    # Try venv next
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
        site_packages = Path(venv_path) / "lib" / python_version / "site-packages"
        if site_packages.exists():
            return str(site_packages)
    
    raise RuntimeError("Could not find site-packages directory. Please make sure you're in a conda or venv environment.")

def main():
    # Get the environment's site-packages path
    try:
        env_site_packages = get_env_python_path()
        print(f"Using site-packages from: {env_site_packages}")
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Get the path to the original script
    script_dir = Path(__file__).parent
    create_object_script = script_dir / "create_object.py"
    
    if not create_object_script.exists():
        print(f"Error: Could not find script at {create_object_script}")
        sys.exit(1)
    
    # Get the command line arguments (excluding the script name)
    args = sys.argv[1:]
    
    if not args:
        print("Error: Please provide a description of the object to create")
        print("Usage: python run_object_creation.py \"Your object description\"")
        sys.exit(1)
    
    # Join all arguments into a single string
    prompt = " ".join(args)
    
    # Construct the Blender command
    blender_cmd = [
        "blender",
        "--background",
        "--python",
        str(create_object_script),
        "--",
        prompt
    ]
    
    # Set up the environment
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{env_site_packages}:{env.get('PYTHONPATH', '')}"
    
    # Run Blender with the modified environment
    try:
        subprocess.run(blender_cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Blender: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: Blender not found. Please make sure Blender is installed and in your PATH.")
        sys.exit(1)

if __name__ == "__main__":
    main() 