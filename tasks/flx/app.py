import json

from typing import Any

from .ui import Text
from .lib.utils import clean
from .lib.crypto import text_to_base62, base62_to_text



def ref(text: str) -> Text:
  return Text(clean(str(text)))

class JApp:
  def __init__(self, *args: Any, **kwargs: Any) -> None:
    self.init(*args, **kwargs)

  def init(self, *args: Any, **kwargs: Any) -> Any:
    pass
  
  def create_event(self, prefix, *args, js_args=[]) -> str:
    serialized_args = json.dumps([str(arg) for arg in args])
    hash_value = text_to_base62(serialized_args)  # Should return a string
    js_args_str = f", {', '.join(js_args)}" if js_args else ""
    return f"sendArgsJSON('{prefix}:{hash_value}'{js_args_str})"
  
  def bind(self, name: str, *args, extra=[]) -> str:
    return self.create_event(name, *args, js_args=extra)
  
  def send(self, text, raw: bool = False) -> str:
    return f"sendInput({text})" if raw else f"sendInput('{text}')"

  def on(self, name, *args, event="click", ev: bool = False) -> str:
    return f'on{event}="{self.bind("on_" + name, *args, extra=["utils.getEventObject(event)"] if ev else [])}"'

  def _on_event_data(self, event_hash, *args) -> Any:
    # may raise error
    event, _hash_text = event_hash.split(":")
    return getattr(self, event)(*json.loads(base62_to_text(_hash_text)), *args)

  def default(self, text):
    pass

  def clean(self, text):
    return clean(str(text))

  def startloop(self) -> None:
    while True:
      text: str = input().strip()
      try:
        # [on:hash, ...] - python list
        if self._on_event_data(*json.loads(text)):
          break
      except json.JSONDecodeError:
        if self.default(text):
          break
