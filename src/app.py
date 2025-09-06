"""Main QuickMC application."""

import os
import sys
from typing import Dict, Any

from config import ConfigManager
from auth import AuthManager
from installation import InstallationManager
from launcher import MinecraftLauncher
from exceptions import QuickMCError


class QuickMCApp:
    """Main QuickMC application class."""

    def __init__(self, install_dir: str = None, debug_oauth: bool = False):
        # Set up directories
        self.install_dir = install_dir or os.path.join(os.path.expanduser("~"), "QuickMC")
        self.minecraft_dir = os.path.join(self.install_dir, ".minecraft")
        self.data_dir = os.path.join(self.install_dir, "data")

        # Ensure directories exist
        os.makedirs(self.minecraft_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

        # Initialize managers
        self.config_manager = ConfigManager(self.data_dir)
        self.auth_manager = AuthManager(self.data_dir, debug_oauth)

        # Load configuration
        self.config = self.config_manager.load_config()

        # Initialize other managers with config
        self.installation_manager = InstallationManager(self.minecraft_dir, self.config)
        self.launcher = MinecraftLauncher(self.minecraft_dir, self.config)

    def run(self) -> None:
        # sourcery skip: extract-duplicate-method, extract-method
        """Run the complete QuickMC launch process."""
        try:
            print("Starting QuickMC launcher...")

            # Step 1: Authenticate user
            print("Authenticating...")
            login_data = self.auth_manager.authenticate()
            print(f"Authenticated as: {login_data['name']}")

            # Step 2: Install Minecraft version
            minecraft_version = self.config["minecraft_version"]
            print(f"Preparing Minecraft {minecraft_version}...")
            actual_version = self.installation_manager.install_minecraft_version(minecraft_version)

            # Step 3: Launch Minecraft
            print(f"Launching {actual_version}...")
            self.launcher.launch(actual_version, login_data)

            print("Launch completed successfully!")

        except KeyboardInterrupt:
            print("\nLauncher interrupted by user.")
            sys.exit(1)
        except QuickMCError as e:
            print(f"\nQuickMC Error: {e}")
            if sys.stdout.isatty():
                input("Press Enter to exit...")
            sys.exit(1)
        except Exception as e:
            print(f"\nUnexpected Error: {e}")
            if sys.stdout.isatty():
                input("Press Enter to exit...")
            sys.exit(1)

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update configuration."""
        self.config = new_config
        self.config_manager.save_config(new_config)

        # Recreate managers with new config
        self.installation_manager = InstallationManager(self.minecraft_dir, self.config)
        self.launcher = MinecraftLauncher(self.minecraft_dir, self.config)
