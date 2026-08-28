import json

def send_event(event, payload=None):
  print("!flx-event:" + json.dumps({
    "event": event,
    "payload": payload
  }), flush=True)

def func(name, *args):
  send_event("func", {
    "name": name,
    "args": args
  })

def update_element(selector, content, tp):
  func("updateElement", selector, content, tp)

def append(selector, content):
  update_element(selector, content, "append")

def html(selector, content):
  update_element(selector, content, "html")

def text(selector, content):
  update_element(selector, content, "text")

# Run Code
def run_code(code: str | list[str]):
  if isinstance(code, list):
    code = ";".join(code)
  func("codeEval", code)

def eval(code):
  run_code(f"sendInput({code})")
  return input()

# ----- setting config
def set_config(name: str, value: bool):
  config_map = {
    # Blocks user input
    "block-user-input": "blockUserInput",
    # Blocks user clear option
    "block-user-clear": "blockUserClear",

    # Parse ansi code
    "parse-ansi": "setParseAnsi",
    "dom-purify": "setDomPurify",
    "script-stdout": "setRawOutput",

    # Block task stopping
    "block-kill-task": "blockUserKillTask",
    # Render script output html
    "script-stdout-parse": "setRawOutputHTML",
    # Auto scroll on append
    "auto-append-scroll": "setAutoAppendScroll",
  }

  if name not in config_map:
    raise ValueError(f"Error: Invalid '{name}'")

  func("setConfig", config_map[name], value)

# -------- Input
def _check_error(text):
  try:
    data = json.loads(text)
    if data.get("event") == "error":
      raise Exception(str(data.get("payload")))
  except (KeyError, json.decoder.JSONDecodeError, TypeError, AttributeError):
    return str(text)

# use this method only for input text form user
def ask_input(label: str = "", autohide=True, focus=False, effect=None):
  effect = None if effect is None or focus or not autohide else effect

  func("askInput", label, focus, effect)

  text = input()

  if autohide:
    hide_input_panel()

  return _check_error(text)

# -------- JS Exposed functions
def invoke(event, payload = {}):
  func("invoke", event, payload)

def copy_text(text):
  func("copyText", text)

def notify(message, type = "info", priority = "normal"):
  func("notify", message, type, priority)

# 
def hide_input_panel():
  func("hideInputPanel")

def set_raw_output_panel(selector):
  func("setRawOutputPanel", selector)

def set_default_config():
  func("setAppDefaultConfig")

def scroll_to_bottom(selector):
  func("scrollToBottom", selector)

def scroll_to_top(selector):
  func("scrollToTop", selector)

def clear_panel(force=False):
  func("clearPanel", force)

