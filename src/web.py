from threading import Thread
import flask

app = flask.Flask(__name__)

def shutdown():
    raise RuntimeError("Shutting down...")

@app.route('/completeLogin')
def completeLogin():
    global code
    code = flask.request.args.get('code')
    Thread(target=shutdown,daemon=True).start()
    return "<h1>Logged in! You can close this window now."

func = None
def start():
    app.run(port=8000)

def get_code():
    global code
    return code
