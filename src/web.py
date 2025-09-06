"""Web server for handling OAuth callbacks."""

from threading import Thread
from typing import Optional
import flask

app = flask.Flask(__name__)
_auth_code: Optional[str] = None


def shutdown():
    """Shutdown the Flask server."""
    # Use the proper way to shutdown Flask
    func = flask.request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.route('/completeLogin')
def complete_login():
    """Handle the OAuth callback and capture the authorization code."""
    global _auth_code
    _auth_code = flask.request.args.get('code')

    # Shutdown server after capturing code
    Thread(target=shutdown, daemon=True).start()

    return """
    <html>
        <head><title>QuickMC - Login Complete</title></head>
        <body>
            <h1>✅ Login Successful!</h1>
            <p>You can now close this window and return to QuickMC.</p>
            <script>setTimeout(() => window.close(), 2000);</script>
        </body>
    </html>
    """


def start():
    """Start the web server to handle OAuth callbacks."""
    app.run(port=8000, host='127.0.0.1', debug=False, use_reloader=False)


def get_code() -> Optional[str]:
    """Get the captured authorization code."""
    return _auth_code


def reset():
    """Reset the captured authorization code."""
    global _auth_code
    _auth_code = None
