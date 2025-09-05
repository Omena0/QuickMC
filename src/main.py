import minecraft_launcher_lib as mcl
from tqdm import tqdm
import subprocess
import webview
import pprint
import json
import time
import web
import sys
import os

# Configuration
client_id = "35292a04-c714-4fac-92e0-82c3ea360278"
redirect_uri = "http://localhost:8000/completeLogin"

install_dir = os.path.join(os.path.expanduser("~"), "QuickMC")
minecraft_dir = os.path.join(install_dir, ".minecraft")
data_dir = os.path.join(install_dir, "data")

os.makedirs(minecraft_dir, exist_ok=True)

# When set to a truthy value (e.g. 1), the script will print intermediate HTTP responses
DEBUG_OAUTH = False

login_data = None

# Load configuration
def load_config():
    """Load configuration from config.json with fallback defaults"""
    default_config = {
        "minecraft_version": "1.21.4",
        "java": {
            "executable_path": "/usr/bin/java",
            "memory": {
                "min": "8G",
                "max": "8G"
            },
            "jvm_arguments": [
                # Performance optimizations for faster startup
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:+UseG1GC",
                "-XX:+UseStringDeduplication",
                "-XX:G1NewSizePercent=20",
                "-XX:G1ReservePercent=20",
                "-XX:MaxGCPauseMillis=50",
                "-XX:G1HeapRegionSize=32M",
                # Fast startup optimizations
                "-XX:+TieredCompilation",
                "-XX:TieredStopAtLevel=1",  # Faster startup, less optimization
                "-XX:+UseFastUnorderedTimeStamps",
                "-XX:+UseLargePages",
                "-XX:+AlwaysPreTouch",  # Allocate memory upfront
                # Reduce verification overhead
                "-Xverify:none",
                # Disable JIT compiler warmup for faster startup
                "-XX:CompileThreshold=1500",
                # Parallel class loading
                "-XX:+UnlockDiagnosticVMOptions",
                "-XX:+UseParallelGC",  # Faster for startup
                # Aggressive optimization for startup
                "-Dsun.rmi.dgc.server.gcInterval=2147483646",
                "-Dsun.rmi.dgc.client.gcInterval=2147483646",
                "-Djava.net.preferIPv4Stack=true"
            ]
        },
        "fabric": {
            "auto_install": True,
            "loader_version": "latest"
        },
        "install": {
            "download_threads": 8,  # Increased from 4 for faster downloads
            "enable_progress_bar": True,
            "skip_hash_validation": False,  # Set to true for faster installs (less secure)
            "parallel_downloads": True
        },
        "launch": {
            "skip_asset_verification": False,  # Set to true for faster launches
            "preload_natives": True,  # Preload native libraries
            "close_launcher": False  # Launch Minecraft without waiting
        }
    }

    # Define install_dir and ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)

    config_path = os.path.join(data_dir, "config.json")
    try:
        with open(config_path, "r") as f:
            user_config = json.load(f)
        # Merge user config with defaults
        def merge_config(default, user):
            if isinstance(default, dict) and isinstance(user, dict):
                merged = default.copy()
                for key, value in user.items():
                    if key in merged and isinstance(merged[key], dict):
                        merged[key] = merge_config(merged[key], value)
                    else:
                        merged[key] = value
                return merged
            return user
        
        return merge_config(default_config, user_config)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load config.json from {config_path} ({e}), using defaults")
        return default_config

# Load config
config = load_config()

def complete_login():
    global state, login_data
    url, state, verifier = mcl.microsoft_account.get_secure_login_data(client_id, redirect_uri)

    print(url)

    webview.create_window("Log in with Microsoft", url, width=800, height=600)
    try:
        # Try lightweight backends first, fallback to qt if needed
        backends = []
        if os.name == 'nt':  # Windows
            backends = ['edgechromium', 'edgehtml', 'mshtml', 'qt']
        elif os.name == 'posix':  # Linux/Mac
            backends = ['gtk', 'qt']
        else:
            backends = ['qt']

        # Try each backend until one works
        webview_started = False
        for backend in backends:
            try:
                webview.start(private_mode=False, func=web.start, gui=backend)
                webview_started = True
                break
            except Exception as e:
                print(f"Failed to start webview with {backend}: {e}")
                continue

        if not webview_started:
            raise Exception("All webview backends failed")

    except:
        import webbrowser
        print("WebView failed to start, opening in default browser...")
        webbrowser.open(url)

    try:
        code = web.get_code()
    except:
        exit('Failed to get code from web.py.')

    # Instead of calling the library's complete_login (which raises a generic error),
    # perform the steps manually so we can inspect intermediate responses and print them
    # for debugging. This will help diagnose AzureAppNotPermitted issues.
    try:
        token_request = mcl.microsoft_account.get_authorization_token(client_id, None, redirect_uri, code, verifier)
        if DEBUG_OAUTH:
            print("token_request:")
            pprint.pprint(token_request)

        if "access_token" not in token_request:
            print("Failed to get access token from token endpoint:")
            pprint.pprint(token_request)
            raise Exception(f'Failed to get access token. {token_request}')

        token = token_request["access_token"]

        xbl_request = mcl.microsoft_account.authenticate_with_xbl(token)
        if DEBUG_OAUTH:
            print("xbl_request:")
            pprint.pprint(xbl_request)

        xbl_token = xbl_request.get("Token")
        userhash = xbl_request.get("DisplayClaims", {}).get("xui", [])[0].get("uhs") if xbl_request.get("DisplayClaims") else None

        xsts_request = mcl.microsoft_account.authenticate_with_xsts(xbl_token)
        if DEBUG_OAUTH:
            print("xsts_request:")
            pprint.pprint(xsts_request)

        xsts_token = xsts_request.get("Token")

        account_request = mcl.microsoft_account.authenticate_with_minecraft(userhash, xsts_token)
        if DEBUG_OAUTH:
            print("account_request:")
            pprint.pprint(account_request)

        if "access_token" not in account_request:
            # This is the condition that the library maps to AzureAppNotPermitted.
            print("Minecraft service did not return an access_token. Full response below:")
            pprint.pprint(account_request)
            raise mcl.exceptions.AzureAppNotPermitted()

        access_token = account_request["access_token"]
        profile = mcl.microsoft_account.get_profile(access_token)

        if DEBUG_OAUTH:
            print("profile:")
            pprint.pprint(profile)

        if "error" in profile and profile["error"] == "NOT_FOUND":
            raise mcl.exceptions.AccountNotOwnMinecraft()

        profile["access_token"] = access_token
        profile["refresh_token"] = token_request.get("refresh_token")
        profile["cache_timestamp"] = time.time()

        login_data = profile
        return login_data

    except Exception:
        # Re-raise after printing helpful hint
        print("If you see AzureAppNotPermitted, ensure your Azure App has permission to use the Minecraft API.")
        print("Common steps: register the redirect URI as a native/mobile app, ensure scope XboxLive.signin is allowed, and consult the minecraft-launcher-lib docs.")
        raise

def refresh_login():
    global login_data
    login_data = mcl.microsoft_account.complete_refresh(
        client_id,
        None,
        redirect_uri,
        login_data["refresh_token"]
    )
    
    # Add timestamp to refreshed data
    login_data["cache_timestamp"] = time.time()
    
    return login_data

def login():
    global login_data
    if login_data is None:
        # Check if login data is saved
        login_data_path = os.path.join(install_dir, "data", "login_data.json")
        if os.path.exists(login_data_path):
            try:
                with open(login_data_path, "r") as f:
                    cached_data = json.load(f)
                
                # Check if we have a timestamp for smart caching
                cache_timestamp = cached_data.get("cache_timestamp", 0)
                current_time = time.time()
                
                # If token is less than 45 minutes old, use it without validation (tokens are valid for 1 hour)
                if current_time - cache_timestamp < 2700:  # 45 minutes in seconds
                    print("Using cached login data (skip validation)")
                    login_data = cached_data
                    return login_data
                
                # If token is less than 50 minutes old, try quick validation
                elif current_time - cache_timestamp < 3000:  # 50 minutes
                    print("Validating cached login data...")
                    try:
                        mcl.microsoft_account.validate_token(cached_data["access_token"])
                        print("Cached token is still valid")
                        # Update timestamp and save
                        cached_data["cache_timestamp"] = current_time
                        with open(login_data_path, "w") as f:
                            json.dump(cached_data, f)
                        login_data = cached_data
                        return login_data
                    except Exception as e:
                        print(f"Cached token validation failed: {e}")
                        # Fall through to refresh
                
                # Token is old or validation failed, try refresh
                if "refresh_token" in cached_data:
                    print("Refreshing login token...")
                    try:
                        login_data = mcl.microsoft_account.complete_refresh(
                            client_id,
                            None,
                            redirect_uri,
                            cached_data["refresh_token"]
                        )
                        # Add timestamp to refreshed data
                        login_data["cache_timestamp"] = current_time
                        return login_data
                    except Exception as e:
                        print(f"Token refresh failed: {e}")
                        # Fall through to complete login
                        
            except Exception as e:
                print(f"Failed to load cached login data: {e}")
                # Fall through to complete login

        # No valid cached data, do complete login
        print("Performing complete login...")
        return complete_login()
    else:
        # We already have login data in memory, try to refresh it
        return refresh_login()

def check_system_optimizations():
    """Check system for additional performance optimizations"""
    optimizations = []
    
    # Check if running on SSD
    try:
        with open('/proc/mounts', 'r') as f:
            mounts = f.read()
            if 'ssd' in mounts.lower() or 'nvme' in mounts.lower():
                optimizations.append("✓ SSD detected - good for fast loading")
            else:
                optimizations.append("⚠ Consider moving Minecraft to an SSD for faster loading")
    except:
        pass
    
    # Check available RAM
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
            for line in meminfo.split('\n'):
                if 'MemTotal:' in line:
                    total_ram_kb = int(line.split()[1])
                    total_ram_gb = total_ram_kb / 1024 / 1024
                    if total_ram_gb >= 16:
                        optimizations.append(f"✓ {total_ram_gb:.1f}GB RAM available - excellent for Minecraft")
                    elif total_ram_gb >= 8:
                        optimizations.append(f"✓ {total_ram_gb:.1f}GB RAM available - good for Minecraft")
                    else:
                        optimizations.append(f"⚠ {total_ram_gb:.1f}GB RAM - consider upgrading for better performance")
                    break
    except:
        pass
    
    # Check Java version
    try:
        result = subprocess.run([config["java"]["executable_path"], "-version"], 
                              capture_output=True, text=True, stderr=subprocess.STDOUT)
        if "17" in result.stdout or "21" in result.stdout:
            optimizations.append("✓ Modern Java version detected - optimal performance")
        else:
            optimizations.append("⚠ Consider upgrading to Java 17 or 21 for better performance")
    except:
        optimizations.append("⚠ Could not verify Java version")
    
    if optimizations:
        print("\nSystem Performance Check:")
        for opt in optimizations:
            print(f"  {opt}")
        print()

def main():
    # Quick system optimization check
    check_system_optimizations()
    
    # Login
    login_data = login()

    os.makedirs(os.path.join(install_dir, "data"), exist_ok=True)

    # Save login data with timestamp
    if "cache_timestamp" not in login_data:
        login_data["cache_timestamp"] = time.time()
    
    with open(os.path.join(install_dir, "data", "login_data.json"), "w") as f:
        json.dump(login_data, f)

    # Get Minecraft version from config
    minecraft_version = config["minecraft_version"]

    # Handle Fabric installation based on config
    if config["fabric"]["auto_install"]:
        # Get fabric loader version
        fabric_versions = mcl.fabric.get_all_loader_versions()
        if config["fabric"]["loader_version"] == "latest":
            fabric_version = fabric_versions[0]["version"] if fabric_versions else None
        else:
            # Find specific version or fall back to latest
            fabric_version = config["fabric"]["loader_version"]
            if not any(v["version"] == fabric_version for v in fabric_versions):
                print(f"Warning: Fabric version {fabric_version} not found, using latest")
                fabric_version = fabric_versions[0]["version"] if fabric_versions else None

        version = f"fabric-loader-{fabric_version}-{minecraft_version}"

        # Check if installed
        if not any([i for i in mcl.utils.get_installed_versions(minecraft_dir) if i["id"] == version]):
            # Initialize progress bar based on config
            pbar = None

            def set_status(status):
                print(f"Status: {status}")

            def set_progress(progress):
                if pbar:
                    pbar.n = progress
                    pbar.refresh()

            def set_max(maximum):
                nonlocal pbar
                if config["install"]["enable_progress_bar"]:
                    pbar = tqdm(total=maximum, desc="Installing Fabric", unit="%")

            callback = {
                "setStatus": set_status,
                "setProgress": set_progress,
                "setMax": set_max
            }

            # Enhanced installation with performance optimizations
            install_options = {}
            if config["install"].get("skip_hash_validation", False):
                install_options["skipHashValidation"] = True
                print("Warning: Hash validation disabled for faster installation")

            # Install with optimized settings
            mcl.fabric.install_fabric(
                minecraft_version, 
                minecraft_dir, 
                callback=callback,
                **install_options
            )

            if pbar:
                pbar.close()
    else:
        # Use vanilla Minecraft
        version = minecraft_version

    # Build launch command using config values
    java_config = config["java"]
    launch_config = config.get("launch", {})
    
    jvm_args = [f"-Xms{java_config['memory']['min']}", f"-Xmx{java_config['memory']['max']}"]
    jvm_args.extend(java_config["jvm_arguments"])
    
    # Add additional startup optimizations based on system
    if launch_config.get("preload_natives", True):
        jvm_args.extend([
            "-Djava.library.path=" + os.path.join(minecraft_dir, "versions", version, "natives"),
            "-Dfile.encoding=UTF-8"
        ])
    
    options = {
        "username": login_data["name"],
        "uuid": login_data["id"],
        "token": login_data["access_token"],
        "executablePath": java_config["executable_path"],
        "defaultExecutablePath": java_config["executable_path"],
        "jvmArguments": jvm_args,
        "launcherName": "QuickMC",
        "launcherVersion": "1.2",
        "gameDirectory": minecraft_dir
    }
    
    # Skip asset verification if configured for faster startup
    if launch_config.get("skip_asset_verification", False):
        options["skipAssetVerification"] = True
    
    command = mcl.command.get_minecraft_command(version, minecraft_dir, options)

    os.chdir(minecraft_dir)

    print("Launching Minecraft...")

    # Launch Minecraft asynchronously if configured
    if launch_config.get("close_launcher", False):
        # Start Minecraft in background and exit launcher immediately
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Minecraft launched in background. Launcher exiting...")
    else:
        # Traditional blocking launch
        subprocess.run(command)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nLauncher interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        if sys.stdout.isatty():
            input("Press Enter to exit...")
        sys.exit(1)
    
    if sys.stdout.isatty():
        print("\nLauncher completed successfully!")
        input("Press Enter to exit...")
