"""Authentication management for QuickMC launcher."""

import json
import os
import time
import pprint
import webbrowser
from typing import Dict, Any, Optional
import minecraft_launcher_lib as mcl
import webview

from exceptions import AuthenticationError
from platform_utils import WebViewManager


class AuthManager:
    """Manages Minecraft authentication and token caching."""

    CLIENT_ID = "35292a04-c714-4fac-92e0-82c3ea360278"
    REDIRECT_URI = "http://localhost:8000/completeLogin"
    TOKEN_EXPIRY_BUFFER = 300  # 5 minutes buffer before token expiry

    def __init__(self, data_dir: str, debug_oauth: bool = False):
        self.data_dir = data_dir
        self.debug_oauth = debug_oauth
        self.login_data_path = os.path.join(data_dir, "login_data.json")
        self._login_data: Optional[Dict[str, Any]] = None

    def authenticate(self) -> Dict[str, Any]:
        """Authenticate user and return login data."""
        # Try to use cached/refreshed token first
        if self._try_cached_authentication():
            return self._login_data

        # Perform complete login
        return self._complete_login()

    def _try_cached_authentication(self) -> bool:
        """Try to authenticate using cached or refreshed tokens."""
        cached_data = self._load_cached_login_data()
        if not cached_data:
            return False

        current_time = time.time()
        cache_timestamp = cached_data.get("cache_timestamp", 0)
        time_since_cache = current_time - cache_timestamp

        # If token is fresh (< 45 minutes), use without validation
        if time_since_cache < 2700:  # 45 minutes
            print("Using fresh cached login data")
            self._login_data = cached_data
            return True

        # If token is still valid (< 50 minutes), validate it
        # sourcery skip: merge-nested-ifs
        if time_since_cache < 3000:  # 50 minutes
            if self._validate_cached_token(cached_data, current_time):
                return True

        # Try to refresh the token
        if "refresh_token" in cached_data:
            return self._try_refresh_token(cached_data)

        return False

    def _load_cached_login_data(self) -> Optional[Dict[str, Any]]:
        """Load cached login data from file."""
        if not os.path.exists(self.login_data_path):
            return None

        try:
            with open(self.login_data_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load cached login data: {e}")
            return None

    def _validate_cached_token(self, cached_data: Dict[str, Any], current_time: float) -> bool:
        """Validate cached token and update timestamp if valid."""
        try:
            mcl.microsoft_account.validate_token(cached_data["access_token"])
            print("Cached token is still valid")

            # Update timestamp and save
            cached_data["cache_timestamp"] = current_time
            self._save_login_data(cached_data)
            self._login_data = cached_data
            return True
        except Exception as e:
            print(f"Cached token validation failed: {e}")
            return False

    def _try_refresh_token(self, cached_data: Dict[str, Any]) -> bool:
        """Try to refresh the authentication token."""
        try:
            print("Refreshing login token...")
            refreshed_data = mcl.microsoft_account.complete_refresh(
                self.CLIENT_ID,
                None,
                self.REDIRECT_URI,
                cached_data["refresh_token"]
            )

            # Preserve additional data from original login
            for key in ["name", "id"]:
                if key in cached_data and key not in refreshed_data:
                    refreshed_data[key] = cached_data[key]

            # Add timestamp
            refreshed_data["cache_timestamp"] = time.time()

            self._save_login_data(refreshed_data)
            self._login_data = refreshed_data
            print("Token refresh successful")
            return True

        except Exception as e:
            print(f"Token refresh failed: {e}")
            return False

    def _complete_login(self) -> Dict[str, Any]:
        """Perform complete OAuth login flow."""
        import web_server  # Import here to avoid circular imports

        print("Performing complete login...")
        url, state, verifier = mcl.microsoft_account.get_secure_login_data(
            self.CLIENT_ID,
            self.REDIRECT_URI
        )

        # Try to open login in webview, fallback to browser
        code = self._get_auth_code(url)

        # Complete the authentication flow
        login_data = self._process_auth_code(code, verifier)

        # Save login data
        login_data["cache_timestamp"] = time.time()
        self._save_login_data(login_data)
        self._login_data = login_data

        return login_data

    def _get_auth_code(self, url: str) -> str:
        """Get authorization code through webview or browser."""
        import web_server

        print("Opening login page...")

        # Try webview first
        if self._try_webview_login(url):
            return web_server.get_code()

        # Fallback to browser
        print("WebView failed, opening in default browser...")
        webbrowser.open(url)
        return web_server.get_code()

    def _try_webview_login(self, url: str) -> bool:
        """Try to open login in webview."""
        import web_server

        try:
            webview.create_window("Log in with Microsoft", url, width=800, height=600)

            # Try different backends based on platform
            backends = WebViewManager.get_backends()
            for backend in backends:
                try:
                    print(f"Trying webview backend: {backend}")
                    webview.start(private_mode=False, func=web_server.start, gui=backend, debug=False)
                    print(f"Successfully started webview with {backend}")
                    return True
                except Exception as e:
                    print(f"Failed to start webview with {backend}: {e}")
            raise Exception("All webview backends failed") # sourcery skip: raise-specific-error

        except Exception as e:
            print(f"Webview initialization failed: {e}")
            return False

    def _process_auth_code(self, code: str, verifier: str) -> Dict[str, Any]:
        # sourcery skip: extract-method
        """Process authorization code to get final login data."""
        try:
            # Get access token
            token_request = mcl.microsoft_account.get_authorization_token(
                self.CLIENT_ID, None, self.REDIRECT_URI, code, verifier
            )

            if self.debug_oauth:
                print("token_request:")
                pprint.pprint(token_request)

            if "access_token" not in token_request:
                print("Failed to get access token from token endpoint:")
                pprint.pprint(token_request)
                raise AuthenticationError(f"Failed to get access token: {token_request}")

            # Authenticate with Xbox Live
            xbl_request = mcl.microsoft_account.authenticate_with_xbl(token_request["access_token"])
            if self.debug_oauth:
                print("xbl_request:")
                pprint.pprint(xbl_request)

            xbl_token = xbl_request.get("Token")
            userhash = xbl_request.get("DisplayClaims", {}).get("xui", [])[0].get("uhs") if xbl_request.get("DisplayClaims") else None

            # Authenticate with Xbox Live Secure Token Service
            xsts_request = mcl.microsoft_account.authenticate_with_xsts(xbl_token)
            if self.debug_oauth:
                print("xsts_request:")
                pprint.pprint(xsts_request)

            xsts_token = xsts_request.get("Token")

            # Authenticate with Minecraft
            account_request = mcl.microsoft_account.authenticate_with_minecraft(userhash, xsts_token)
            if self.debug_oauth:
                print("account_request:")
                pprint.pprint(account_request)

            if "access_token" not in account_request:
                print("Minecraft service did not return an access_token. Full response:")
                pprint.pprint(account_request)
                raise mcl.exceptions.AzureAppNotPermitted()

            # Get profile information
            access_token = account_request["access_token"]
            profile = mcl.microsoft_account.get_profile(access_token)

            if self.debug_oauth:
                print("profile:")
                pprint.pprint(profile)

            if "error" in profile and profile["error"] == "NOT_FOUND":
                raise mcl.exceptions.AccountNotOwnMinecraft()

            # Combine all authentication data
            profile["access_token"] = access_token
            profile["refresh_token"] = token_request.get("refresh_token")

            return profile

        except mcl.exceptions.AzureAppNotPermitted as e:
            print("Azure app permission error. Ensure your Azure App has permission to use the Minecraft API.")
            print("Common steps: register the redirect URI, ensure scope XboxLive.signin is allowed.")
            raise AuthenticationError("Azure app not permitted") from e
        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {e}") from e

    def _save_login_data(self, login_data: Dict[str, Any]) -> None:
        """Save login data to file."""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.login_data_path, "w") as f:
                json.dump(login_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save login data: {e}")

    @property
    def login_data(self) -> Optional[Dict[str, Any]]:
        """Get current login data."""
        return self._login_data
