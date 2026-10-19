"""Minecraft installation management."""

from collections.abc import Callable
from typing import Any

import minecraft_launcher_lib as mcl
from tqdm import tqdm

from .exceptions import InstallationError


class InstallationManager:
    """Manages Minecraft and Fabric installation."""
    
    def __init__(self, minecraft_dir: str, config: dict[str, Any]):
        self.minecraft_dir = minecraft_dir
        self.config = config
        self._progress_bar: tqdm | None = None
    
    def install_minecraft_version(self, version: str) -> str:
        """Install Minecraft version and return the actual version string to use."""
        if self.config["fabric"]["auto_install"]:
            return self._install_fabric_version(version)
        # Use vanilla Minecraft - just ensure it's installed
        self._ensure_minecraft_installed(version)
        return version
    
    def _install_fabric_version(self, minecraft_version: str) -> str:
        """Install Fabric loader for the specified Minecraft version."""
        try:
            # Get fabric loader version
            fabric_versions = mcl.fabric.get_all_loader_versions()
            if not fabric_versions:
                raise InstallationError("No Fabric loader versions available")

            fabric_version = self._get_fabric_version(fabric_versions)
            version_id = f"fabric-loader-{fabric_version}-{minecraft_version}"

            # Check if already installed
            if self._is_version_installed(version_id):
                print(f"Fabric {version_id} is already installed")
                return version_id

            # Install Fabric
            print(f"Installing Fabric {fabric_version} for Minecraft {minecraft_version}...")
            self._install_fabric(minecraft_version, fabric_version)

            return version_id

        except Exception as e:
            raise InstallationError(f"Failed to install Fabric: {e}") from e
    
    def _get_fabric_version(self, fabric_versions: list) -> str:
        """Get the Fabric version to install based on configuration."""
        config_version = self.config["fabric"]["loader_version"]
        
        if config_version == "latest":
            return fabric_versions[0]["version"]
        
        # Find specific version
        for version_info in fabric_versions:
            if version_info["version"] == config_version:
                return config_version
        
        # Version not found, use latest
        print(f"Warning: Fabric version {config_version} not found, using latest")
        return fabric_versions[0]["version"]
    
    def _is_version_installed(self, version_id: str) -> bool:
        """Check if a Minecraft version is already installed."""
        installed_versions = mcl.utils.get_installed_versions(self.minecraft_dir)
        return any(v["id"] == version_id for v in installed_versions)
    
    def _ensure_minecraft_installed(self, version: str) -> None:
        """Ensure vanilla Minecraft version is installed."""
        if not self._is_version_installed(version):
            print(f"Installing Minecraft {version}...")
            # The installation will happen automatically when launching
            # This is a placeholder for potential future vanilla installation logic
    
    def _install_fabric(self, minecraft_version: str, fabric_version: str) -> None:
        """Install Fabric with progress tracking."""
        callback = self._create_progress_callback()

        try:
            mcl.fabric.install_fabric(
                minecraft_version,
                self.minecraft_dir,
                loader_version=fabric_version,
                callback=callback,
            )

            if self._progress_bar:
                self._progress_bar.close()
                self._progress_bar = None

        except Exception as e:
            if self._progress_bar:
                self._progress_bar.close()
                self._progress_bar = None
            raise InstallationError(f"Fabric installation failed: {e}") from e
    
    def _create_progress_callback(self) -> dict[str, Callable]:
        """Create progress callback for installation."""
        def set_status(status: str) -> None:
            print(f"Status: {status}")
        
        def set_progress(progress: int) -> None:
            if self._progress_bar:
                self._progress_bar.n = progress
                self._progress_bar.refresh()
        
        def set_max(maximum: int) -> None:
            if self.config["install"]["enable_progress_bar"]:
                self._progress_bar = tqdm(
                    total=maximum, 
                    desc="Installing Fabric", 
                    unit="%"
                )
        
        return {
            "setStatus": set_status,
            "setProgress": set_progress,
            "setMax": set_max
        }
