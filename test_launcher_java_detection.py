#!/usr/bin/env python3
"""Test script for launcher Java auto-detection."""

import sys
import os
import json
import tempfile

# Add src directory to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from launcher import MinecraftLauncher

def test_launcher_java_auto_detection():
    """Test launcher Java auto-detection when executable path is invalid."""
    print("=== Launcher Java Auto-Detection Test ===")
    print()
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        minecraft_dir = os.path.join(temp_dir, ".minecraft")
        os.makedirs(minecraft_dir, exist_ok=True)
        
        # Test 1: Config with invalid Java path
        print("1. Testing launcher with invalid Java path...")
        config_with_invalid_java = {
            "java": {
                "executable_path": "/invalid/path/to/java",
                "memory": {"min": "2G", "max": "4G"},
                "jvm_arguments": []
            },
            "launch": {
                "close_launcher": False,
                "skip_asset_verification": False,
                "preload_natives": True
            }
        }
        
        launcher = MinecraftLauncher(minecraft_dir, config_with_invalid_java)
        
        # Test the _ensure_java_executable method
        print(f"   Before: {config_with_invalid_java['java']['executable_path']}")
        launcher._ensure_java_executable()
        print(f"   After: {config_with_invalid_java['java']['executable_path']}")
        
        # Test 2: Config with "auto" Java path
        print("\n2. Testing launcher with 'auto' Java path...")
        config_with_auto_java = {
            "java": {
                "executable_path": "auto",
                "memory": {"min": "2G", "max": "4G"},
                "jvm_arguments": []
            },
            "launch": {
                "close_launcher": False,
                "skip_asset_verification": False,
                "preload_natives": True
            }
        }
        
        launcher2 = MinecraftLauncher(minecraft_dir, config_with_auto_java)
        
        print(f"   Before: {config_with_auto_java['java']['executable_path']}")
        launcher2._ensure_java_executable()
        print(f"   After: {config_with_auto_java['java']['executable_path']}")
        
        # Test 3: Config with None Java path
        print("\n3. Testing launcher with None Java path...")
        config_with_none_java = {
            "java": {
                "executable_path": None,
                "memory": {"min": "2G", "max": "4G"},
                "jvm_arguments": []
            },
            "launch": {
                "close_launcher": False,
                "skip_asset_verification": False,
                "preload_natives": True
            }
        }
        
        launcher3 = MinecraftLauncher(minecraft_dir, config_with_none_java)
        
        print(f"   Before: {config_with_none_java['java']['executable_path']}")
        launcher3._ensure_java_executable()
        print(f"   After: {config_with_none_java['java']['executable_path']}")
        
        print("\n=== Test Complete ===")
        
        # Verify all paths are now valid
        path1 = config_with_invalid_java['java']['executable_path']
        path2 = config_with_auto_java['java']['executable_path']
        path3 = config_with_none_java['java']['executable_path']
        
        print(f"\nResults:")
        print(f"- Invalid path fix: {'✅' if path1 != '/invalid/path/to/java' and path1 else '❌'}")
        print(f"- Auto path fix: {'✅' if path2 != 'auto' and path2 else '❌'}")
        print(f"- None path fix: {'✅' if path3 is not None and path3 else '❌'}")

if __name__ == "__main__":
    test_launcher_java_auto_detection()