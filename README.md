# VenvMan
Since some DCCs (e.g. Blender) do not come with built-in virtual environment management, many add-ons install pip packages to the global usersite using the `--user` flag. This is not optimal, since those packages might conflict with other applications and multiple versions cannot co-exist.

VenvMan provides a straight forward way to create and manage virtual environments for any host software's Python binary and install all required modules in a location of the developer's choice. Installed packages are dynamically added to the `PYTHONPATH`/usersite `(sys.path)` on runtime.

# Requirements
`venv` and module has to be available to the host Python interpreter (`venv` has been included as a standard library since Python `3.3`).
Although this module should work on Windows, it has only been tested in Linux environments.

# Installation
Add VenvMan as a submodule to your repository:
```bash
git submodule add https://github.com/plyrolith/venvman
```
... or simply download `venvman.py` and include it directly in your add-on.

# Example Usage
This is a simplified example for managing a virtual environment from within a Blender add-on.

```python
from pathlib import Path

from .venvman import Venv

# Define the path to the virtual environment
venv_path = Path.home() / ".virtualenvs" / "my_env"

# Optionally add the path to the requirements.txt
requirements_path = Path("/path/to/requirements.txt")

# Create a venv manager instance
venv = Venv(venv_path, requirements_path, verbose=True)

# Ensure the environment is valid, create if necessary and add to path
venv.initialize()

# Install all missing packages from requirements.txt
venv.install_requirements()

# Install a single package if the module is not found
try:
    import numpy
except ImportError:
    venv.install_package("numpy")
    import numpy

# Install a specific package version
venv.install_package("opencv-python", "4.9.0.80")

# For development:
# Update all packages in requirements.txt to the current version
venv.update_requirements()

# Freeze the current version back to requirements.txt
venv.freeze_requirements()
```