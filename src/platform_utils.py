"""Platform-specific utilities and configurations."""

import os
import shutil
import subprocess
import platform
from typing import List, Dict, Any


class PlatformUtils:
    """Utility class for platform-specific operations."""
    
    @staticmethod
    def get_system() -> str:
        """Get the current system platform."""
        return platform.system().lower()
    
    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows."""
        return PlatformUtils.get_system() == "windows"
    
    @staticmethod
    def is_macos() -> bool:
        """Check if running on macOS."""
        return PlatformUtils.get_system() == "darwin"
    
    @staticmethod
    def is_linux() -> bool:
        """Check if running on Linux."""
        return PlatformUtils.get_system() == "linux"


class JavaDetector:
    """Detects Java executable across different platforms."""
    
    @staticmethod
    def detect_java_executable() -> str:
        """Detect Java executable path across platforms."""
        system = PlatformUtils.get_system()
        java_paths = JavaDetector._get_java_paths_for_platform(system)
        
        # Find the first working Java executable
        for java_path in java_paths:
            if JavaDetector._is_valid_java(java_path):
                return java_path
        
        # Fallback to 'java' if nothing else works
        return "java"
    
    @staticmethod
    def _get_java_paths_for_platform(system: str) -> List[str]:
        """Get platform-specific Java paths to check."""
        java_home_path = os.path.join(os.environ.get("JAVA_HOME", ""), "bin", "java")
        
        if system == "windows":
            return [
                "java",  # Try PATH first
                "C:\\Program Files\\Java\\jre\\bin\\java.exe",
                "C:\\Program Files\\Java\\jdk\\bin\\java.exe",
                "C:\\Program Files (x86)\\Java\\jre\\bin\\java.exe",
                "C:\\Program Files (x86)\\Java\\jdk\\bin\\java.exe",
                java_home_path + ".exe"
            ]
        elif system == "darwin":  # macOS
            return [
                "java",  # Try PATH first
                "/usr/bin/java",
                "/System/Library/Frameworks/JavaVM.framework/Versions/Current/Commands/java",
                "/Library/Java/JavaVirtualMachines/*/Contents/Home/bin/java",
                java_home_path
            ]
        else:  # Linux and other Unix-like systems
            return [
                "java",  # Try PATH first
                "/usr/bin/java",
                "/usr/lib/jvm/default-java/bin/java",
                "/usr/lib/jvm/java-11-openjdk/bin/java",
                "/usr/lib/jvm/java-17-openjdk/bin/java",
                "/usr/lib/jvm/java-21-openjdk/bin/java",
                java_home_path
            ]
    
    @staticmethod
    def _is_valid_java(java_path: str) -> bool:
        """Check if a Java path is valid and working."""
        if not java_path:
            return False
        
        # Check if executable exists
        if os.path.isabs(java_path):
            if not os.path.isfile(java_path):
                return False
        else:
            if not shutil.which(java_path):
                return False
        
        # Test if Java actually works
        try:
            result = subprocess.run(
                [java_path, "-version"],
                capture_output=True,
                text=True,
                stderr=subprocess.STDOUT,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False


class PlatformConfig:
    """Platform-specific configuration provider."""
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get platform-specific default configuration."""
        base_config = PlatformConfig._get_base_config()
        system = PlatformUtils.get_system()
        
        # Apply platform-specific optimizations
        if system == "windows":
            PlatformConfig._apply_windows_config(base_config)
        elif system == "darwin":
            PlatformConfig._apply_macos_config(base_config)
        else:  # Linux and other Unix
            PlatformConfig._apply_linux_config(base_config)
        
        return base_config
    
    @staticmethod
    def _get_base_config() -> Dict[str, Any]:
        """Get base configuration that works on all platforms."""
        return {
            "minecraft_version": "1.21.4",
            "java": {
                "executable_path": JavaDetector.detect_java_executable(),
                "memory": {
                    "min": "4G",
                    "max": "6G"
                },
                "jvm_arguments": [
                    "-XX:+UseG1GC",
                    "-XX:+UnlockExperimentalVMOptions",
                    "-XX:G1NewSizePercent=20",
                    "-XX:G1ReservePercent=20",
                    "-XX:MaxGCPauseMillis=50",
                    "-XX:G1HeapRegionSize=32M",
                    "-XX:+UseStringDeduplication",
                    "-XX:+TieredCompilation",
                    "-Djava.net.preferIPv4Stack=true"
                ]
            },
            "fabric": {
                "auto_install": True,
                "loader_version": "latest"
            },
            "install": {
                "download_threads": 4,
                "enable_progress_bar": True,
                "skip_hash_validation": False,
                "parallel_downloads": True
            },
            "launch": {
                "skip_asset_verification": False,
                "preload_natives": True,
                "close_launcher": False
            }
        }
    
    @staticmethod
    def _apply_windows_config(config: Dict[str, Any]) -> None:
        """Apply Windows-specific configuration."""
        config["java"]["jvm_arguments"].extend([
            "-XX:+UseLargePages",
            "-Dsun.rmi.dgc.server.gcInterval=2147483646",
            "-Dsun.rmi.dgc.client.gcInterval=2147483646"
        ])
        config["install"]["download_threads"] = 8
    
    @staticmethod
    def _apply_macos_config(config: Dict[str, Any]) -> None:
        """Apply macOS-specific configuration."""
        config["java"]["jvm_arguments"].extend([
            "-XstartOnFirstThread",
            "-Djava.awt.headless=false"
        ])
    
    @staticmethod
    def _apply_linux_config(config: Dict[str, Any]) -> None:
        """Apply Linux-specific configuration."""
        config["java"]["jvm_arguments"].extend([
            "-XX:+AlwaysPreTouch",
            "-XX:TieredStopAtLevel=1"
        ])
        config["install"]["download_threads"] = 8


class WebViewManager:
    """Manages platform-specific webview backend selection."""
    
    @staticmethod
    def get_backends() -> List[str]:
        """Get preferred webview backends for the current platform."""
        system = PlatformUtils.get_system()
        
        if system == "windows":
            return ['edgechromium', 'edgehtml', 'mshtml', 'qt', 'cef']
        elif system == "darwin":  # macOS
            return ['cocoa', 'qt', 'webkit']
        elif system == "linux":
            return ['gtk', 'qt', 'cef']
        else:
            return ['qt', 'gtk', 'cef']
