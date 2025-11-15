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
    """Detects Java executable across different platforms, prioritizing Java 22+."""

    @staticmethod
    def detect_java_executable() -> str:
        """Detect Java executable path across platforms, preferring Java 22+ and GraalVM."""
        system = PlatformUtils.get_system()
        java_candidates = JavaDetector._get_java_candidates_for_platform(system)
        
        # Find all valid Java installations with their versions and implementation info
        valid_javas = []
        for java_path in java_candidates:
            if JavaDetector._is_valid_java(java_path):
                version = JavaDetector._get_java_version(java_path)
                is_graalvm = JavaDetector._is_graalvm(java_path)
                if version > 0:  # Only include if we could detect version
                    valid_javas.append((java_path, version, is_graalvm))
        
        if not valid_javas:
            # Fallback: try 'java' in PATH even if version detection failed
            if JavaDetector._is_valid_java("java"):
                return "java"
            else:
                print("Warning: No valid Java installation found")
                return "java"  # Return anyway, might work at runtime
        
        # Sort by priority: GraalVM first, then version preference (Java 22+ first, then descending)
        valid_javas.sort(key=lambda x: JavaDetector._get_java_priority(x[1], x[2]), reverse=True)
        
        best_java = valid_javas[0][0]
        best_version = valid_javas[0][1]
        is_graalvm = valid_javas[0][2]
        
        implementation = "GraalVM" if is_graalvm else "OpenJDK/HotSpot"
        
        if is_graalvm and best_version >= 22:
            print(f"🚀 Using {implementation} Java {best_version}: {best_java}")
        elif best_version >= 22:
            print(f"✅ Using {implementation} Java {best_version}: {best_java}")
        elif best_version >= 17:
            graal_rec = " (consider GraalVM for better performance)" if not is_graalvm else ""
            print(f"⚠️  Using {implementation} Java {best_version} (Java 22+ recommended){graal_rec}: {best_java}")
        else:
            print(f"❌ Using {implementation} Java {best_version} (upgrade to GraalVM Java 25+ strongly recommended): {best_java}")
        
        return best_java
    
    @staticmethod
    def _get_java_candidates_for_platform(system: str) -> List[str]:
        """Get platform-specific Java paths to check, prioritizing newer versions."""
        java_home_path = os.path.join(os.environ.get("JAVA_HOME", ""), "bin", "java")

        if system == "windows":
            # Check for Java installations in order of preference
            candidates = [
                "java",  # Try PATH first (might be Java 22+)
            ]
            
            # Prioritize GraalVM installations first (highest performance)
            candidates.extend([
                "C:\\Program Files\\Oracle\\graalvm-jdk-25+13.1\\bin\\java.exe",
                "C:\\Program Files\\Oracle\\graalvm-jdk-*\\bin\\java.exe",  # Wildcard for other versions
                "C:\\Program Files\\GraalVM\\*\\bin\\java.exe",
            ])
            
            # Add GraalVM for different versions
            for version in range(30, 17, -1):  # GraalVM 17+ only
                candidates.extend([
                    f"C:\\Program Files\\Oracle\\graalvm-jdk-{version}\\bin\\java.exe",
                    f"C:\\Program Files\\Oracle\\graalvm-jdk-{version}+*\\bin\\java.exe",
                    f"C:\\Program Files\\GraalVM\\graalvm-ce-java{version}\\bin\\java.exe",
                    f"C:\\Program Files\\GraalVM\\graalvm-jdk-{version}\\bin\\java.exe",
                ])

            # Check Program Files for specific versions (Java 22+ first)
            for version in range(30, 7, -1):  # Check Java 30 down to Java 8
                candidates.extend([
                    f"C:\\Program Files\\Java\\jdk-{version}\\bin\\java.exe",
                    f"C:\\Program Files\\Eclipse Adoptium\\jdk-{version}.0.0.0-hotspot\\bin\\java.exe",
                    f"C:\\Program Files\\Eclipse Adoptium\\jdk-{version}.*-hotspot\\bin\\java.exe",  # Wildcard pattern
                    f"C:\\Program Files\\Eclipse Foundation\\jdk-{version}\\bin\\java.exe",
                    f"C:\\Program Files\\Microsoft\\jdk-{version}\\bin\\java.exe",
                    f"C:\\Program Files\\Amazon Corretto\\jdk{version}\\bin\\java.exe",
                    f"C:\\Program Files\\OpenJDK\\jdk-{version}\\bin\\java.exe",
                ])

            # Add specific Eclipse Adoptium patterns found on this system
            candidates.extend([
                "C:\\Program Files\\Eclipse Adoptium\\jdk-17.0.15.6-hotspot\\bin\\java.exe",
                "C:\\Program Files\\Eclipse Adoptium\\jdk*hotspot\\bin\\java.exe",
            ])

            # Legacy paths
            candidates.extend([
                "C:\\Program Files\\Java\\jre\\bin\\java.exe",
                "C:\\Program Files\\Java\\jdk\\bin\\java.exe",
                "C:\\Program Files (x86)\\Java\\jre\\bin\\java.exe",
                "C:\\Program Files (x86)\\Java\\jdk\\bin\\java.exe",
                java_home_path + ".exe"
            ])

            return candidates

        elif system == "darwin":  # macOS
            candidates = [
                "java",  # Try PATH first
                "/usr/bin/java",
            ]
            
            # Prioritize GraalVM installations first
            candidates.extend([
                "/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home/bin/java",
                "/Library/Java/JavaVirtualMachines/graalvm-*/Contents/Home/bin/java",
                "/opt/homebrew/opt/graalvm-jdk*/bin/java",
                "/usr/local/opt/graalvm-jdk*/bin/java",
            ])
            
            # Add GraalVM for different versions
            for version in range(30, 17, -1):  # GraalVM 17+ only
                candidates.extend([
                    f"/Library/Java/JavaVirtualMachines/graalvm-jdk-{version}/Contents/Home/bin/java",
                    f"/opt/homebrew/opt/graalvm-jdk{version}/bin/java",
                    f"/usr/local/opt/graalvm-jdk{version}/bin/java",
                ])

            # Check for Homebrew and other installations
            for version in range(30, 7, -1):
                candidates.extend([
                    f"/opt/homebrew/opt/openjdk@{version}/bin/java",
                    f"/usr/local/opt/openjdk@{version}/bin/java",
                    f"/Library/Java/JavaVirtualMachines/jdk-{version}.jdk/Contents/Home/bin/java",
                    f"/Library/Java/JavaVirtualMachines/adoptopenjdk-{version}.jdk/Contents/Home/bin/java",
                    f"/Library/Java/JavaVirtualMachines/temurin-{version}.jdk/Contents/Home/bin/java",
                ])

            # Legacy paths
            candidates.extend([
                "/System/Library/Frameworks/JavaVM.framework/Versions/Current/Commands/java",
                java_home_path
            ])

            return candidates

        else:  # Linux and other Unix-like systems
            candidates = [
                "java",  # Try PATH first
                "/usr/bin/java",
            ]
            
            # Prioritize GraalVM installations first
            candidates.extend([
                "/opt/graalvm-jdk-25/bin/java",
                "/opt/graalvm-*/bin/java",
                "/usr/local/graalvm-*/bin/java",
                "/opt/oracle/graalvm-*/bin/java",
            ])
            
            # Add GraalVM for different versions
            for version in range(30, 17, -1):  # GraalVM 17+ only
                candidates.extend([
                    f"/opt/graalvm-jdk-{version}/bin/java",
                    f"/usr/local/graalvm-jdk-{version}/bin/java",
                    f"/opt/oracle/graalvm-jdk-{version}/bin/java",
                    f"/usr/lib/jvm/graalvm-jdk-{version}/bin/java",
                ])

            # Check for distribution-specific paths
            for version in range(30, 7, -1):
                candidates.extend([
                    f"/usr/lib/jvm/java-{version}-openjdk/bin/java",
                    f"/usr/lib/jvm/java-{version}-openjdk-amd64/bin/java",
                    f"/usr/lib/jvm/adoptopenjdk-{version}-hotspot/bin/java",
                    f"/usr/lib/jvm/temurin-{version}-jdk/bin/java",
                    f"/opt/java/openjdk-{version}/bin/java",
                    f"/usr/java/jdk-{version}/bin/java",
                ])

            # Legacy paths
            candidates.extend([
                "/usr/lib/jvm/default-java/bin/java",
                java_home_path
            ])

            return candidates

    @staticmethod
    def _is_valid_java(java_path: str) -> bool:
        """Check if a Java path is valid and working."""
        if not java_path:
            return False
        
        # Handle glob patterns (expand them)
        if '*' in java_path:
            import glob
            matching_paths = glob.glob(java_path)
            if matching_paths:
                java_path = matching_paths[0]  # Use the first match
            else:
                return False
        
        # Check if executable exists
        # For relative paths like "java", use shutil.which to find in PATH
        # For absolute paths, check if file exists
        if os.path.isabs(java_path):
            if not os.path.isfile(java_path):
                return False
        else:
            # For commands like "java", check if they exist in PATH
            resolved_path = shutil.which(java_path)
            if not resolved_path:
                return False
            # Use the resolved path for testing
            java_path = resolved_path
        
        # Test if Java actually works
        try:
            result = subprocess.run(
                [java_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def _get_java_version(java_path: str) -> int:
        """Get the major version number of a Java installation."""
        try:
            result = subprocess.run(
                [java_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return 0

            # Parse version from output - Java writes version to stderr
            # Examples:
            # "java version "1.8.0_281"" -> 8
            # "openjdk version "11.0.11" -> 11
            # "openjdk version "17.0.15" -> 17
            # "openjdk version "22.0.1" -> 22

            import re
            # Combine stdout and stderr since different Java implementations may use either
            full_output = (result.stdout + "\n" + result.stderr).strip()

            # Look for version patterns
            version_patterns = [
                r'version "([^"]+)"',           # Standard pattern
                r'version ([0-9]+\.[0-9]+)',    # Alternative pattern
                r'openjdk ([0-9]+\.[0-9]+)',    # OpenJDK specific
                r'java ([0-9]+\.[0-9]+)',       # Java specific
            ]

            version_str = None
            for pattern in version_patterns:
                match = re.search(pattern, full_output, re.IGNORECASE)
                if match:
                    version_str = match.group(1)
                    break

            if not version_str:
                return 0

            # Handle different version formats
            if version_str.startswith("1."):
                # Java 8 format: "1.8.0_281"
                return int(version_str.split(".")[1])
            else:
                # Java 9+ format: "11.0.11", "17.0.15", "22.0.1"
                return int(version_str.split(".")[0])

        except Exception:
            return 0
    
    @staticmethod
    def _is_graalvm(java_path: str) -> bool:
        """Check if a Java installation is GraalVM."""
        try:
            # Resolve the path if it's a command name
            if not os.path.isabs(java_path):
                resolved_path = shutil.which(java_path)
                if resolved_path:
                    java_path = resolved_path
            
            # Check if path contains GraalVM indicators
            java_path_lower = java_path.lower()
            if any(indicator in java_path_lower for indicator in ['graalvm', 'graal']):
                return True
            
            # Check version output for GraalVM indicators
            result = subprocess.run(
                [java_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return False
            
            # Look for GraalVM in version output
            full_output = (result.stdout + "\n" + result.stderr).lower()
            return any(indicator in full_output for indicator in ['graalvm', 'graal'])
            
        except Exception:
            return False
    
    @staticmethod
    def _get_java_priority(version: int, is_graalvm: bool) -> int:
        """Get priority score for a Java installation (higher is better)."""
        base_priority = JavaDetector._get_version_priority(version)
        
        # GraalVM gets significant bonus
        if is_graalvm:
            return base_priority + 10000  # GraalVM always wins over regular JDK
        
        return base_priority

    @staticmethod
    def _get_version_priority(version: int) -> int:
        """Get priority score for a Java version (higher is better)."""
        if version >= 25:
            return 2000 + version  # Prioritize Java 25+ (latest)
        elif version >= 22:
            return 1000 + version  # Prioritize Java 22+
        elif version >= 17:
            return 500 + version   # Java 17-21 is acceptable
        elif version >= 11:
            return 200 + version   # Java 11-16 is less preferred
        else:
            return version         # Java 8-10 is lowest priority


class PlatformConfig:
    """Platform-specific configuration provider."""

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get platform-specific default configuration."""
        base_config = PlatformConfig._get_base_config()
        system = PlatformUtils.get_system()

        # Optimize JVM arguments for detected Java version
        java_path = base_config["java"]["executable_path"]
        java_version = JavaDetector._get_java_version(java_path)
        PlatformConfig._optimize_jvm_args_for_version(base_config, java_version)

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
                "executable_path": "auto",  # Auto-detect Java on first use
                "memory": {
                    "min": "4G",
                    "max": "6G"
                },
                "jvm_arguments": [
                    # Modern GC optimizations for Java 17+
                    "-XX:+UseG1GC",
                    "-XX:+UnlockExperimentalVMOptions",
                    "-XX:G1NewSizePercent=20",
                    "-XX:G1ReservePercent=20",
                    "-XX:MaxGCPauseMillis=50",
                    "-XX:G1HeapRegionSize=32M",

                    # Performance optimizations for Java 11+
                    "-XX:+UseStringDeduplication",
                    "-XX:+TieredCompilation",
                    "-XX:+OptimizeStringConcat",

                    # Java 22+ optimizations
                    "-XX:+UseZGC",  # ZGC for better latency (Java 15+, production ready in 17+)
                    "-XX:+UnlockExperimentalVMOptions",
                    "-XX:+UseTransparentHugePages",

                    # Network and system optimizations
                    "-Djava.net.preferIPv4Stack=true",
                    "-Dfile.encoding=UTF-8",

                    # Security optimizations for modern Java
                    "-Djava.security.manager=allow"  # Required for Java 18+
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
    def _optimize_jvm_args_for_version(config: Dict[str, Any], java_version: int) -> None:
        """Optimize JVM arguments based on detected Java version."""
        jvm_args = config["java"]["jvm_arguments"]

        # Remove version-specific flags that aren't compatible
        if java_version < 15:
            # Remove ZGC for Java < 15
            jvm_args = [arg for arg in jvm_args if arg != "-XX:+UseZGC"]

        if java_version < 18:
            # Remove security manager flag for Java < 18
            jvm_args = [arg for arg in jvm_args if not arg.startswith("-Djava.security.manager")]

        if java_version < 11:
            # Remove modern optimizations for Java < 11
            jvm_args = [arg for arg in jvm_args if arg not in [
                "-XX:+UseStringDeduplication",
                "-XX:+OptimizeStringConcat"
            ]]

        # Add version-specific optimizations
        if java_version >= 22:
            # Java 22+ specific optimizations
            jvm_args.extend([
                "-XX:+EnableDynamicAgentLoading",
                "-XX:+UnlockDiagnosticVMOptions",
                "-XX:+DebugNonSafepoints"
            ])
        elif java_version >= 17:
            # Java 17+ optimizations
            jvm_args.extend([
                "-XX:+AlwaysActAsServerClassMachine"
            ])

        config["java"]["jvm_arguments"] = jvm_args

    @staticmethod
    def _apply_windows_config(config: Dict[str, Any]) -> None:
        """Apply Windows-specific configuration."""
        java_path = config["java"]["executable_path"]
        java_version = JavaDetector._get_java_version(java_path)

        windows_args = []

        # Large pages support (Java 11+)
        if java_version >= 11:
            windows_args.append("-XX:+UseLargePages")

        # RMI GC tuning
        windows_args.extend([
            "-Dsun.rmi.dgc.server.gcInterval=2147483646",
            "-Dsun.rmi.dgc.client.gcInterval=2147483646"
        ])

        # Windows-specific optimizations for Java 17+
        if java_version >= 17:
            windows_args.extend([
                "-XX:+UseTransparentHugePages",
                "-XX:+UseBiasedLocking"
            ])

        config["java"]["jvm_arguments"].extend(windows_args)
        config["install"]["download_threads"] = 8

    @staticmethod
    def _apply_macos_config(config: Dict[str, Any]) -> None:
        """Apply macOS-specific configuration."""
        java_path = config["java"]["executable_path"]
        java_version = JavaDetector._get_java_version(java_path)

        macos_args = [
            "-XstartOnFirstThread",
            "-Djava.awt.headless=false"
        ]

        # macOS-specific optimizations for Java 17+
        if java_version >= 17:
            macos_args.extend([
                "-XX:+UseCompressedOops",
                "-XX:+UseCompressedClassPointers"
            ])

        config["java"]["jvm_arguments"].extend(macos_args)

    @staticmethod
    def _apply_linux_config(config: Dict[str, Any]) -> None:
        """Apply Linux-specific configuration."""
        java_path = config["java"]["executable_path"]
        java_version = JavaDetector._get_java_version(java_path)

        linux_args = []

        # Linux-specific optimizations
        if java_version >= 11:
            linux_args.append("-XX:+AlwaysPreTouch")

        # Performance tuning for Linux
        if java_version >= 17:
            linux_args.extend([
                "-XX:+UseTransparentHugePages",
                "-XX:+UseBiasedLocking"
            ])
        else:
            # Fallback for older Java versions
            linux_args.append("-XX:TieredStopAtLevel=1")

        config["java"]["jvm_arguments"].extend(linux_args)
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
