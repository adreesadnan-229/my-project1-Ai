import json
import os
import sys

import webview

# When launched via pythonw with no console, keep a log file so errors aren't lost.
if sys.stdout is None or not getattr(sys.stdout, "writable", lambda: True)():
    log_path = os.path.join(os.path.dirname(__file__), "agent.log")
    log_file = open(log_path, "a", encoding="utf-8")
    sys.stdout = log_file
    sys.stderr = log_file

import config
import core

HTML_PATH = os.path.join(os.path.dirname(__file__), "web_ui", "index.html")

window = None
stopped = False


class Api:
    def get_config(self):
        return config.load_config()

    def save_figma(self, token, file_key):
        config.save_config({"figma_token": token, "figma_file_key": file_key})
        return True

    def submit_command(self, text):
        core.submit_text_command(text)
        return True


def _run_js(script):
    if window is None:
        return
    try:
        window.evaluate_js(script)
    except Exception as e:
        print(f"JS call failed: {e}")


def on_status(text):
    print(text, flush=True)
    _run_js(f"updateStatus({json.dumps(text)})")
    lowered = text.lower()
    if "listening" in lowered or "waiting for 'jarvis'" in lowered:
        _run_js("setState('listening')")
    elif "thinking" in lowered or "intent:" in lowered:
        _run_js("setState('thinking')")


def on_speak_start():
    _run_js("setState('speaking')")


def on_speak_end():
    _run_js("setState('idle')")


def run_agent():
    callbacks = {
        "on_status": on_status,
        "on_speak_start": on_speak_start,
        "on_speak_end": on_speak_end,
    }
    core.load_models(on_status=on_status)
    core.run_forever(callbacks, should_stop=lambda: stopped)


def on_closed():
    global stopped
    stopped = True


def main():
    global window
    api = Api()
    window = webview.create_window(
        "Jarvis", HTML_PATH, width=480, height=820, resizable=False, js_api=api,
    )
    window.events.closed += on_closed
    webview.start(func=run_agent)


if __name__ == "__main__":
    main()
