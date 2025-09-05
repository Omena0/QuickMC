import os
import sys
import pprint
import minecraft_launcher_lib as mcl
import webview
import web

# Configuration (allow overrides via environment variables)
client_id = os.environ.get("AZURE_CLIENT_ID", "35292a04-c714-4fac-92e0-82c3ea360278")
redirect_uri = os.environ.get("AZURE_REDIRECT_URI", "http://localhost:8000/completeLogin")
# When set to a truthy value (e.g. 1), the script will print intermediate HTTP responses
DEBUG_OAUTH = bool(os.environ.get("DEBUG_OAUTH", "0"))

"""
{
    "id" : "The uuid",
    "name" : "The username",
    "access_token": "The access token",
    "refresh_token": "The refresh token",
    "skins" : [{
        "id" : "6a6e65e5-76dd-4c3c-a625-162924514568",
        "state" : "ACTIVE",
        "url" : "http://textures.minecraft.net/texture/1a4af718455d4aab528e7a61f86fa25e6a369d1768dcb13f7df319a713eb810b",
        "variant" : "CLASSIC",
        "alias" : "STEVE"
    } ],
    "capes" : []
}
"""
login_data = None

def complete_login():
    global state, login_data
    url, state, verifier = mcl.microsoft_account.get_secure_login_data(client_id, redirect_uri)

    webview.create_window("Log in with Microsoft", url, width=800, height=600)
    webview.start(private_mode=False, func=web.start)

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
        return complete_login()
    else:
        return refresh_login()

login_data = login()

print(login_data)


# To be implemented
