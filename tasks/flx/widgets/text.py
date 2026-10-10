from flx.ui import Text, Div, Animate
from flx.lib.utils import clean, escape

from time import sleep



class LoadingText(Div):
  def __init__(self, text: str = ""):
    super().__init__(f"""
      <div class="h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-gray-300 border-t-blue-500/60"></div>
      <span class="text-sm">{clean(text)}</span>
    """)
    self.add_class("bg-white/10 h-8 flex items-center gap-2 p-2")

  def set_text(self, text: str):
    self.replace(clean(text))

  def success(self, message: str | None = None):
    self.replace_class("bg-white/10", "bg-blue-400/60")
    if message:
      self.set_text(message)

  def error(self, message: str | None = None):
    self.replace_class("bg-white/10", "bg-red-400/60")
    if message:
      self.set_text(message)

  def done(self, message: str = "OK"):
    self.set_text(message)

  def destroy(self):
    self._js.remove()

  def __enter__(self):
    pass

  def __exit__(self, *_):
    self.done()

  def __call__(self, message: str = "OK"):
    self.done(message)


class TypingText(Div):
  def __init__(self, text: str = ""):
    super().__init__()
    
    self.add_class("p-2")

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


class CopyText(Div):
  def __init__(
    self,
    preview: str,
    copy_text: str
  ):
    escaped_copy = escape(str(copy_text)).replace("'", "\\'")
    cleaned_preview = clean(preview)

    super().__init__(f'''
      <!-- Clickable Preview Title -->
      <div class="cursor-pointer flex items-center justify-between gap-2"
         onclick="
          const btn = this.querySelector('span');
          navigator.clipboard.writeText('{escaped_copy}').then(() => {{
            btn.innerText = 'Copied!';
            btn.classList.add('text-green-400');
            setTimeout(() => {{
              btn.innerText = 'Copy';
              btn.classList.remove('text-green-400');
            }}, 1500);
          }});
        ">
        <div class="overflow-x-auto text-nowrap">{cleaned_preview}</div>
        <span class="text-xs px-2 py-1 bg-white/10 hover:bg-white/20 rounded font-semibold transition">
          Copy
        </span>
      </div>
    ''')
    self.add_class("relative bg-white/5 text-white/80 rounded p-2 text-sm shadow-sm")


class CodeBlock(Div):
  def __init__(self, code: str, language: str = ""):
    code = clean(code)
    language = clean(language)

    super().__init__(f'<pre class="bg-black/30 text-white/80 text-xs font-mono p-2 overflow-auto whitespace-pre-wrap"><code class="language-{language}">{code}</code></pre>')
