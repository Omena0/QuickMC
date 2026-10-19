import importlib
import os
import sys
import traceback
import types


class FakeMicrosoftAccount:
    def __init__(self):
        self.call_counts = {
            'get_authorization_token': 0,
            'authenticate_with_xbl': 0,
            'authenticate_with_xsts': 0,
            'authenticate_with_minecraft': 0,
            'get_profile': 0,
        }

    def get_authorization_token(self, *args, **kwargs):
        self.call_counts['get_authorization_token'] += 1
        # Fail first two times, then succeed
        if self.call_counts['get_authorization_token'] < 3:
            raise ConnectionResetError('simulated connection reset')
        return {'access_token': 'atk', 'refresh_token': 'rtk'}

    def authenticate_with_xbl(self, access_token):
        self.call_counts['authenticate_with_xbl'] += 1
        if self.call_counts['authenticate_with_xbl'] < 2:
            raise ConnectionResetError('simulated xbl reset')
        return {'Token': 'xbltoken', 'DisplayClaims': {'xui': [{'uhs': 'userhash'}]}}

    def authenticate_with_xsts(self, xbl_token):
        self.call_counts['authenticate_with_xsts'] += 1
        # succeed immediately
        return {'Token': 'xststoken'}

    def authenticate_with_minecraft(self, userhash, xsts_token):
        self.call_counts['authenticate_with_minecraft'] += 1
        return {'access_token': 'mc_access_token'}

    def get_profile(self, access_token):
        self.call_counts['get_profile'] += 1
        return {'id': '1234', 'name': 'tester'}


class FakeMCL(types.SimpleNamespace):
    def __init__(self):
        super().__init__()
        self.microsoft_account = FakeMicrosoftAccount()
        class Exc:
            class AzureAppNotPermitted(Exception):
                pass
            class AccountNotOwnMinecraft(Exception):
                pass
        self.exceptions = Exc


def test_auth_process_with_retries():
    # Insert fake minecraft_launcher_lib before importing src.auth
    fake = FakeMCL()
    sys.modules['minecraft_launcher_lib'] = fake

    # Ensure project root and src/ are on sys.path so `import src.auth` and its
    # absolute imports (`from exceptions import ...`) resolve when running the
    # test directly from tests/.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    src_dir = os.path.join(project_root, 'src')
    for path_entry in (project_root, src_dir):
        if path_entry not in sys.path:
            sys.path.insert(0, path_entry)

    # Now import the module under test
    try:
        import src.auth as auth_mod
        importlib.reload(auth_mod)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        assert False, 'Failed to import src.auth'

    am = auth_mod.AuthManager(data_dir='/tmp/quickmc_test', debug_oauth=True)

    # Call process_auth_code which should exercise retries on get_authorization_token
    profile = am._process_auth_code('dummy_code', 'dummy_verifier')

    assert profile.get('access_token') == 'mc_access_token'
    assert profile.get('id') == '1234'


if __name__ == '__main__':
    test_auth_process_with_retries()
    print('test passed')
