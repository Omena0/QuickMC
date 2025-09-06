"""Configuration management for QuickMC launcher."""

import json
import os
from typing import Dict, Any, Optional
from exceptions import ConfigurationError
from platform_utils import PlatformConfig


class ConfigManager:
    """Manages configuration loading, merging, and saving."""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.config_path = os.path.join(data_dir, "config.json")
        self._config: Optional[Dict[str, Any]] = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file with platform-aware fallback defaults."""
        if self._config is not None:
            return self._config
        
        default_config = PlatformConfig.get_default_config()
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        try:
            user_config = self._load_user_config()
            if user_config:
                self._config = self._merge_configs(default_config, user_config)
            else:
                self._config = default_config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load config.json from {self.config_path} ({e}), using platform defaults")
            self._config = default_config
        
        return self._config
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
            self._config = config
        except Exception as e:
            raise ConfigurationError(f"Failed to save config: {e}") from e
    
    def _load_user_config(self) -> Optional[Dict[str, Any]]:
        """Load user configuration from file."""
        if not os.path.exists(self.config_path):
            return None
        
        with open(self.config_path, "r") as f:
            return json.load(f)
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge user config with defaults."""
        if not isinstance(default, dict) or not isinstance(user, dict):
            return user
        
        merged = default.copy()
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return self.load_config() if self._config is None else self._config
