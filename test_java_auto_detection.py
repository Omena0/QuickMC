#!/usr/bin/env python3
"""Test script for Java auto-detection in config."""

import sys
import os
import json
import tempfile
import shutil

# Add src directory to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import ConfigManager

def test_java_auto_detection():
    """Test Java auto-detection when executable path is None or 'auto'."""
    print("=== Java Auto-Detection Test ===")
    print()
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temporary config directory: {temp_dir}")
        
        # Test 1: No config file (should auto-detect)
        print("\n1. Testing with no config file (should auto-detect)...")
        config_manager = ConfigManager(temp_dir)
        config = config_manager.load_config()
        
        java_path = config["java"]["executable_path"]
        print(f"   Auto-detected Java: {java_path}")
        print(f"   Is auto: {java_path == 'auto'}")
        
        # Test 2: Config file with null executable_path
        print("\n2. Testing with null executable_path in config...")
        test_config = {
            "java": {
                "executable_path": None,
                "memory": {"min": "2G", "max": "4G"}
            }
        }
        
        config_path = os.path.join(temp_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(test_config, f, indent=2)
        
        # Create new config manager and load
        config_manager2 = ConfigManager(temp_dir)
        config2 = config_manager2.load_config()
        
        java_path2 = config2["java"]["executable_path"]
        print(f"   Auto-detected Java: {java_path2}")
        print(f"   Is not None: {java_path2 is not None}")
        
        # Test 3: Config file with "auto" executable_path
        print("\n3. Testing with 'auto' executable_path in config...")
        test_config3 = {
            "java": {
                "executable_path": "auto",
                "memory": {"min": "2G", "max": "4G"}
            }
        }
        
        with open(config_path, "w") as f:
            json.dump(test_config3, f, indent=2)
        
        # Create new config manager and load
        config_manager3 = ConfigManager(temp_dir)
        config3 = config_manager3.load_config()
        
        java_path3 = config3["java"]["executable_path"]
        print(f"   Auto-detected Java: {java_path3}")
        print(f"   Is not 'auto': {java_path3 != 'auto'}")
        
        # Test 4: Config file with empty string executable_path
        print("\n4. Testing with empty string executable_path in config...")
        test_config4 = {
            "java": {
                "executable_path": "",
                "memory": {"min": "2G", "max": "4G"}
            }
        }
        
        with open(config_path, "w") as f:
            json.dump(test_config4, f, indent=2)
        
        # Create new config manager and load
        config_manager4 = ConfigManager(temp_dir)
        config4 = config_manager4.load_config()
        
        java_path4 = config4["java"]["executable_path"]
        print(f"   Auto-detected Java: {java_path4}")
        print(f"   Is not empty: {java_path4 != ''}")
        
        print("\n=== Test Complete ===")
        print("\nSummary:")
        print(f"- Default config: {'✅' if java_path == 'auto' else '❌'} Uses 'auto' as default")
        print(f"- Null detection: {'✅' if java_path2 and java_path2 != 'auto' else '❌'} Auto-detected from null")
        print(f"- Auto detection: {'✅' if java_path3 and java_path3 != 'auto' else '❌'} Auto-detected from 'auto'")
        print(f"- Empty detection: {'✅' if java_path4 and java_path4 != '' else '❌'} Auto-detected from empty")

if __name__ == "__main__":
    test_java_auto_detection()