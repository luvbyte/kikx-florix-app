import flx.loading.hearts

import json

from flx.js import set_config
from flx.console import Console
from flx.ui.elements import IFrame



console = Console()


frame = IFrame(attrs={
  "sandbox": "allow-scripts",
  "src": "templates/anyx/index.html",
  "onload": "sendInput('__loaded__')"
}, class_list=["flex-1", "overflow-hidden"])


set_config("send-message-events", True)


def send_message(event, payload):
  frame._js.call_func("contentWindow.postMessage",
    {
      "event": event,
      "payload": payload
    },
    "*"
  )


def on_message(event, payload = None):
  if event == "exit":
    exit()


def start(path, args):
  with open(path, "r") as file:
    code = file.read()
  
  is_raw_html = path.suffix == ".html" and code.startswith("<!doctype html>")

  console.append(frame)

  while True:
    content = input().strip()

    if content == "__loaded__":
      event = "RUN_CODE" if path.suffix == ".js" else "HTML_CODE" if not is_raw_html else "RAW_HTML_CODE"
      send_message(event, code)
    elif content.startswith("!!__message__!!"):
      on_message(*json.loads(content[15:]).values())