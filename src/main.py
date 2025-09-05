import minecraft_launcher_lib as mcl
from tqdm import tqdm
import subprocess
import webview
import pprint
import json
import web
import os
import sys

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
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:+UseG1GC",
                "-XX:G1NewSizePercent=20",
                "-XX:G1ReservePercent=20",
                "-XX:MaxGCPauseMillis=50",
                "-XX:G1HeapRegionSize=32M"
            ]
        },
        "fabric": {
            "auto_install": True,
            "loader_version": "latest"
        },
        "install": {
            "download_threads": 4,
            "enable_progress_bar": True
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

    return login_data

def login():
    global login_data
    if login_data is None:
        # Check if login data is saved
        if os.path.exists(os.path.join(install_dir, "data", "login_data.json")):
            with open(os.path.join(install_dir, "data", "login_data.json"), "r") as f:
                login_data = json.load(f)

            # Validate that its still valid, otherwise refresh

            try:
                mcl.microsoft_account.validate_token(login_data["access_token"])
                return login_data
            except:
                return refresh_login()

        return complete_login()
    else:
        return refresh_login()

def main():
    # Login
    login_data = login()

    os.makedirs(os.path.join(install_dir, "data"), exist_ok=True)

    # Save login data
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

            # Install
            mcl.fabric.install_fabric(minecraft_version, minecraft_dir, callback=callback)

            if pbar:
                pbar.close()
    else:
        # Use vanilla Minecraft
        version = minecraft_version

    # Build launch command using config values
    java_config = config["java"]
    jvm_args = [f"-Xms{java_config['memory']['min']}", f"-Xmx{java_config['memory']['max']}"]
    jvm_args.extend(java_config["jvm_arguments"])
    
    command = mcl.command.get_minecraft_command(
        version,
        minecraft_dir,
        {
            "username": login_data["name"],
            "uuid": login_data["id"],
            "token": login_data["access_token"],
            "executablePath": java_config["executable_path"],
            "defaultExecutablePath": java_config["executable_path"],
            "jvmArguments": jvm_args,
            "launcherName": "QuickMC",
            "launcherVersion": "1.0",
            "gameDirectory": minecraft_dir
        }
    )

    os.chdir(minecraft_dir)

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
