from . import Text, Div, Animate
from flx.lib.utils import clean

from time import sleep



class LoadingText(Div):
  def __init__(self, text: str):
    super().__init__(f"""
      <div class="h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-gray-300 border-t-blue-500/60"></div>
      <span class="text-sm">{clean(text)}</span>
    """)
    self.add_class("bg-white/10 h-8 flex items-center gap-2 p-2")
    
  def success(self):
    self.replace_class("bg-white/10", "bg-blue-400/60")
    self.replace("Success")

  def error(self):
    self.replace_class("bg-white/10", "bg-red-400/60")
    self.replace("Success")

  def done(self):
    self.replace("Done")


class TypingText(Div):
  def __init__(self, text: str = ""):
    super().__init__()

    self._text = clean(text)
    self._stop = False

  def set_text(self, text: str):
    self._text = clean(text)
    return self

  def stop(self, clear=True):
    self._stop = True
    if clear:
      self.clear()
    return self

  def play(self, text: str | None, delay: float | None = None):
    if text:
      self.set_text(text)
  
    self.clear()
    self._stop = False
  
    if delay is None:
      delay = max(0.01, 2.0 / len(self._text)) if self._text else 0
  
    for letter in self._text:
      if self._stop:
        break
  
      self.append(letter)
      sleep(delay)
  
    return self

  def wait(self, seconds: float = 1):
    sleep(seconds)
    return self
