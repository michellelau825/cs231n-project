import sys
import os
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.parent

# Add project root to Python path
sys.path.append(str(project_root))

# Add conda environment site-packages
conda_env = os.getenv('CONDA_PREFIX')
if conda_env:
    site_packages = Path(conda_env) / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
    if site_packages.exists():
        sys.path.append(str(site_packages))

# Add user site-packages
user_site = Path.home() / '.local' / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
if user_site.exists():
    sys.path.append(str(user_site))

# Print current Python path for debugging
print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("Python path:", sys.path)

# Try importing required packages
try:
    import scipy
    print("Scipy version:", scipy.__version__)
    print("Scipy location:", scipy.__file__)
except ImportError as e:
    print("Error importing scipy:", str(e))

try:
    import numpy
    print("Numpy version:", numpy.__version__)
    print("Numpy location:", numpy.__file__)
except ImportError as e:
    print("Error importing numpy:", str(e)) 