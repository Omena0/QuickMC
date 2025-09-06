"""Minecraft launcher functionality."""

import os
import subprocess
import sys
from typing import Dict, Any, List
import minecraft_launcher_lib as mcl

from exceptions import LaunchError, JavaNotFoundError
from platform_utils import PlatformUtils


class MinecraftLauncher:
    """Handles launching Minecraft with the specified configuration."""

    def __init__(self, minecraft_dir: str, config: Dict[str, Any]):
        self.minecraft_dir = minecraft_dir
        self.config = config

    def launch(self, version: str, login_data: Dict[str, Any]) -> None:
        """Launch Minecraft with the specified version and login data."""
        try:
            # Build launch options
            options = self._build_launch_options(version, login_data)

            # Get launch command
            command = mcl.command.get_minecraft_command(version, self.minecraft_dir, options)

            # Change to Minecraft directory
            os.chdir(self.minecraft_dir)

            print("Launching Minecraft...")

            # Launch based on configuration
            if self.config["launch"].get("close_launcher", False):
                self._launch_detached(command)
            else:
                self._launch_blocking(command)

        except FileNotFoundError as e:
            java_path = self.config["java"]["executable_path"]
            raise JavaNotFoundError(
                f"Java executable not found: {java_path}. "
                "Please check your Java installation or update the executable_path in config.json"
            ) from e
        except Exception as e:
            raise LaunchError(f"Failed to launch Minecraft: {e}") from e

    def _build_launch_options(self, version: str, login_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build launch options from configuration and login data."""
        java_config = self.config["java"]
        launch_config = self.config.get("launch", {})

        # Build JVM arguments
        jvm_args = self._build_jvm_arguments(version, java_config, launch_config)

        options = {
            "username": login_data["name"],
            "uuid": login_data["id"],
            "token": login_data["access_token"],
            "executablePath": java_config["executable_path"],
            "defaultExecutablePath": java_config["executable_path"],
            "jvmArguments": jvm_args,
            "launcherName": "QuickMC",
            "launcherVersion": "1.4",
            "gameDirectory": self.minecraft_dir
        }

        # Add optional settings
        if launch_config.get("skip_asset_verification", False):
            options["skipAssetVerification"] = True

        return options

    def _build_jvm_arguments(self, version: str, java_config: Dict[str, Any], launch_config: Dict[str, Any]) -> List[str]:
        """Build JVM arguments from configuration."""
        jvm_args = [
            f"-Xms{java_config['memory']['min']}",
            f"-Xmx{java_config['memory']['max']}"
        ]

        # Add configured JVM arguments
        jvm_args.extend(java_config["jvm_arguments"])

        # Add startup optimizations
        if launch_config.get("preload_natives", True):
            natives_path = os.path.join(self.minecraft_dir, "versions", version, "natives")
            jvm_args.extend([
                f"-Djava.library.path={natives_path}",
                "-Dfile.encoding=UTF-8"
            ])

        return jvm_args

    def _launch_detached(self, command: List[str]) -> None:
        """Launch Minecraft in background and exit launcher immediately."""
        system = PlatformUtils.get_system()

        if system == "windows":
            # Windows: detach properly
            subprocess.Popen(
                command,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # Unix-like systems: standard backgrounding
            subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

        print("Minecraft launched in background. Launcher exiting...")

    def _launch_blocking(self, command: List[str]) -> None:
        """Launch Minecraft and wait for it to complete."""
        system = PlatformUtils.get_system()

        if system == "windows":
            # Windows: handle console properly
            creation_flags = subprocess.CREATE_NEW_CONSOLE if sys.stdout.isatty() else 0
            subprocess.run(command, creationflags=creation_flags)
        else:
            # Unix-like systems: standard launch
            subprocess.run(command)
