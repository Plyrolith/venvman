from __future__ import annotations

import shutil
import subprocess
import sys
import venv
from logging import Logger
from pathlib import Path

class Venv:
    """
    Manage a virtual environment for the current Python interpreter.
    """

    logger: Logger | None = None
    pip_path: Path
    python_path: Path
    venv_path: Path
    requirements_path: Path | None = None

    def __init__(
        self,
        venv_path: str | Path,
        requirements_path: str | Path | None,
        logger: Logger | None = None,
    ):
        """
        Create a virtual environment manager.

        Parameters:
            - venv_path (str | Path): Path to the virtual environment
            - requirements_path (str | Path | None): Path to the requirements file
            - logger (Logger | None): Logger instance for alternative message output
        """
        self.venv_path = Path(venv_path)
        self.pip_path = Path(venv_path / "bin" / "pip")
        self.python_path = Path(venv_path / "bin" / "python")
        self.requirements_path = requirements_path
        self.logger = logger

    def _exception(self, message: str, exception: Exception | None = None):
        """
        Log an exception message if a logger is available,
        otherwise print the message and raise the exception if given.

        Parameters:
            - message (str): Exception message
            - exception (Exception | None): Exception instance
        """
        message = f"VenvMan: {message}"
        if self.logger:
            self.logger.exception(message)
            return
        print(message)
        if exception:
            raise exception

    def _info(self, message: str):
        """
        Log an info message if a logger is available, otherwise print it.

        Parameters:
            - message (str): Info message
        """
        message = f"VenvMan: {message}"
        if self.logger:
            self.logger.info(message)
        else:
            print(message)

    def initialize(self) -> Path:
        """
        Check the virtual environment. (Re-)reate it if necessary.
        Add the virtual environment's site-packages to the path.

        Returns:
            - Path: Path to the virtual environment
        """
        self._info(f"Checking virtual environment at {self.venv_path}")

        # Check if the virtual environment exists and is complete
        python_path = self.python_path
        if (
            python_path.exists()
            and python_path.resolve() == Path(sys.executable)
            and self.pip_path.exists()
        ):
            self._info("Virtual environment verified")

        else:
            # If the virtual environment exists but is incomplete, delete it
            if self.venv_path.exists():
                self._info("Virtual environment exists, but is incomplete")
                self._info("Deleting virtual environment")
                shutil.rmtree(self.venv_path)

            # Create the virtual environment
            self._info("Creating virtual environment")
            self.venv_path.parent.mkdir(parents=True, exist_ok=True)
            venv.create(self.venv_path, with_pip=True)

        # Ensure the virtual environment's site-packages is in the path
        version = f"{sys.version_info.major}.{sys.version_info.minor}"
        usersite_path = self.venv_path / "lib" / f"python{version}" / "site-packages"
        usersite_path.mkdir(parents=True, exist_ok=True)
        usersite_str = str(usersite_path)
        if usersite_str not in sys.path:

            self._info(f"Setting up user site path at {usersite_path}")
            sys.path.append(usersite_str)

        return self.venv_path

    def install_package(self, package: str, version: str | None = None):
        """
        Install a package in the virtual environment.

        Parameters:
            - package (str): Package name
            - version (str | None): Package version
        """
        self._info(f"Installing {package} using pip")
        if version:
            package = f"{package}=={version}"
        subprocess.check_call((self.pip_path, "install", package))

    def install_requirements(self) -> list[str] | None:
        """
        Install add-on requirements.

        Returns:
            - list[str] | None: List of installed packages if successful
        """
        if not self.requirements_path:
            self._info("No requirements file specified")
            return

        self._info("Checking/installing dependencies using pip")

        # Use pip freeze in a sub process to extract all installed modules
        try:
            freeze = subprocess.run(
                (self.pip_path, "freeze"),
                capture_output=True,
                text=True,
            ).stdout

        except subprocess.CalledProcessError as e:
            self._exception("Error calling pip freeze", e)
            return

        # Compare requirements with list of installed packages
        installed_packages = []
        with open(self.requirements_path) as req_file:
            packages = req_file.readlines()
            for line in packages:
                package = line.replace("\n", "")
                if package in freeze:
                    self._info(f"Dependency {package} satisfied.")
                    continue
                try:

                    # If requirement not found in installed packages, install it
                    self._info(f"Installing {package}")
                    subprocess.check_call((self.pip_path, "install", package))
                    installed_packages.append(package)

                except subprocess.CalledProcessError as e:
                    self._exception(f"Could not install {package}", e)

        return installed_packages

    def update_requirements(self) -> dict[str] | None:
        """
        Update packages listed in requirements.txt to the newest version.

        Returns:
            - list[str] | None: List of updated packages if successful
        """
        if not self.requirements_path:
            self._info("No requirements file specified")
            return

        self._info("Updating dependencies using pip")

        # Read requirements file line by line
        updated_packages = []
        with open(self.requirements_path) as req_file:
            req_lines = req_file.readlines()
            for line in req_lines:

                # Remove version number to enforce latest release
                package = line.split("==")[0]

                # Skip empty lines
                if not package or package == "\n":
                    continue

                # Install latest release
                try:
                    subprocess.check_call(
                        (self.pip_path, "install", package, "--upgrade")
                    )
                    updated_packages.append(package)

                except subprocess.CalledProcessError:
                    self._info(
                        "Subprocess usually generates an error. \
                        Don't worry about that. Check version below."
                    )

                # Display/print package information to indicate success
                try:
                    subprocess.check_call((self.pip_path, "show", package))

                except subprocess.CalledProcessError as e:
                    self._exception("Error calling pip", e)

        return updated_packages

    def freeze_requirements(self) -> Path | None:
        """
        Create or update requirements.txt with all packages in the current version.

        Returns:
            - Path | None: Path to the updated requirements.txt if successful
        """
        if not self.requirements_path:
            self._info("No requirements file specified")
            return

        self._info("Freezing current dependencies versions to requirements.txt")

        # Use pip freeze in a sub process to extract all installed modules
        self._info("Fetching complete pip freeze output")
        try:
            freeze = subprocess.run(
                (self.pip_path, "freeze"),
                capture_output=True,
                text=True,
            ).stdout
            freeze_packages = freeze.split("\n")

        except subprocess.CalledProcessError as e:
            self._exception("Error calling pip", e)
            return

        # Read the current requirements and build a list of version-less package names
        self._info("Reading current requirements.txt")
        requirements_path = self.requirements_path
        with open(requirements_path, "r") as req_file:
            req_lines = req_file.readlines()
            packages = [line.split("==")[0] for line in req_lines if line]

        # Write all frozen packages that were already mentioned back into requirements
        self._info("Re-write only relevant package versions")
        with open(requirements_path, "w") as req_file:
            for freeze_package in freeze_packages:
                package = freeze_package.split("==")[0]

                # Skip empty lines
                if not package or package == "\n" or package not in packages:
                    continue

                # Write the frozen package with version into requirements file
                self._info(f"Writing {package}")
                req_file.write(freeze_package + "\n")

        return requirements_path
