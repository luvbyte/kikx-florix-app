import re
import json
import difflib
from time import sleep

from typing import Any
from contextlib import contextmanager

from flx import panel, js
from flx.os import is_installed
from flx.ui.helpers import ClassBuilder
from flx.ui import Div, Animate, Pre, Text
from flx.utils import check_version
from flx.lib.utils import clean, escape, bclean, get_item, sanitize_html

from flx.widgets.fs import FSWrapper
from flx.widgets.dialogue import AlertWrapper
from flx.widgets.text import LoadingText, TypingText, CopyText, CodeBlock
from flx.widgets.ui import ProgressBar, Panel


class Console:
  def __init__(
    self,
    font_size: int = 14,
    padding: int | None = None,
    auto_scroll: bool = True
  ):
    panel.clear()

    self.padding = padding
    self.font_size = font_size
    self.auto_scroll = auto_scroll

    self._box = (
      Div()
        .add_class(f"text-[{self.font_size}px] relative flex-1 flex flex-col overflow-y-auto overflow-x-hidden text-white scrollbar-thin font-body scrollbar-thumb-white/20")
        .add_class(ClassBuilder().add_if(f"p-{self.padding}", self.padding).done())
      )

    panel.inject(self.box)

  # -------------------------
  # Wrappers
  # -------------------------
  
  @property
  def box(self):
    return self._box

  @property
  def fs(self) -> FSWrapper:
    return FSWrapper()

  @property
  def alert(self) -> AlertWrapper:
    return AlertWrapper()

  @property
  def wg(self) -> 'ConsoleWidgets':
    return ConsoleWidgets(self)

  # -------------------------
  # Cleaning
  # -------------------------

  def clean(self, text: str) -> str:
    return clean(text)

  def sanitize(self, html_content) -> str:
    return sanitize_html(html_content)

  def escape(self, *args, **kwargs) -> str:
    return escape(*args, **kwargs)
  
  # -------------------------
  # Updating Box UI
  # -------------------------
  
  def append(self, el, auto_scroll: bool = False) -> None:
    self.box.append(el)
    if self.auto_scroll and auto_scroll:
      self.scroll_to_bottom()

  def replace(self, el) -> None:
    self.box.replace(el)

  def clear(self) -> None:
    self.box.clear()

  # -------------------------
  # Parsing
  # -------------------------

  def _parse_markup(self, text: str) -> str:
    def replacer(match):
      color = match.group(1).lower()
      content = match.group(2)
      return f'<span class="text-{color}-400">{content}</span>'
  
    pattern = re.compile(r'\[([a-zA-Z]+)\](.*?)\[/\1\]', re.DOTALL)
    return pattern.sub(replacer, text)
  
  # -------------------------
  # Display 
  # -------------------------

  def print(
    self,
    *lines,
    size: float = None,
    center: bool = False,
    padding: int | None = None,
    dom_purify: bool = True,
    bg: str | None = None,
    fg: str | None = None,
    class_list: str | None = None,
    auto_scroll: bool = False,
    effect: str | None = None
  ):
    div = Div(*[
        f"<p>{self._parse_markup(clean(line)) if dom_purify else self._parse_markup(self.sanitize(line))}</p>"
        for line in lines
      ]).add_class("w-full flex gap-x-1 break-all").add_class(
        ClassBuilder()
        .add_if(f"p-{padding}", padding)
        .add_if(f"text-[{size}px]", size)
        .add_if("justify-center", center)
        .add_if(f"bg-{bg}", bg)
        .add_if(f"text-{fg}", fg)
        .add_multiple((class_list or "").split())
        .done()
      )
    self.append(Animate(div, effect=effect) if isinstance(effect, str) else div, auto_scroll=auto_scroll)

  def print_success(self, message, *args, **kwargs) -> None:
    self.print(f"[green][+][/green] {message}", *args, **kwargs)

  def print_error(self, message, *args, **kwargs) -> None:
    self.print(f"[red][-][/red] {message}", *args, **kwargs)

  def pre(
    self,
    text: str,
    height: str = "auto",
    justify: str = "start",
    align: str = "start",
    text_align: str = "start",
    effect: str | None = None
  ) -> Pre:
    el = Pre(text)
    el.add_style("height", height)
    el.add_class(
      "text-xs", "flex", f"justify-{justify}", f"items-{align}", f"text-{text_align}"
    )
    self.append(Animate(el, effect=effect) if isinstance(effect, str) else el)
    
    return el

  def color_box(self, text: str, color: str = "gray", effect="fadeIn"):
    div = Div(f"""
      <div class="bg-{color}-400/60 border-b border-{color}-300/60 p-2 text-{color}-100 shadow-sm break-all">
        {clean(text)}
      </div>
    """)

    self.append(Animate(div, effect=effect) if isinstance(effect, str) else div, auto_scroll=True)
  
  def print_json(self, obj: dict):
    self.print(f'<pre class="text-xs whitespace-pre-wrap">{json.dumps(obj, indent=2)}</pre>', dom_purify=False)
  
  def hr(self) -> None:
    self.append('<div class="w-full bg-white min-h-[1px]"></div>')

  def br(self, times: int = 1) -> None:
    self.append(Div("<br>" * times))

  def loader(self, text: str = "") -> Text:
    self.clear()

    el = Text(text)
    
    self.append(Div(
      Div().add_class("border-white border-b w-6 h-6 animate-spin rounded-full"),
      el
    ).add_class("flex-1 flex flex-col gap-2 items-center justify-center"))
    
    return el

  # -------------------------
  # Input
  # -------------------------
  
  def input(self, label: str = "", autohide: bool = True, focus: bool = False, effect: str = "slideInUp") -> str:
    js.set_config("block-user-input", False)
    result = js.ask_input(label, autohide=autohide, focus=focus, effect=effect)
    js.set_config("block-user-input", True)
    return result

  # -------------------------
  # Utils
  # -------------------------

  def check_pkgs(self, *names):
    required = []

    for name in names:
      if not is_installed(name):
        required.append(name)
    
    if not required:
      return True

    self.alert.error(f"'{ ' '.join(required) }' is not installed", "Program Not Found")
    exit()

  def scroll_to_bottom(self) -> None:
    self.box.scroll_to_bottom()

  def wait(self, seconds: float) -> None:
    sleep(seconds)

  # -------------------------
  # JS
  # -------------------------

  def notify(self, message, type: str = 'info', priority: str = "normal") -> None:
    js.notify(message, type=type, priority=priority)



class ConsoleWidgets:
  def __init__(self, console):
    self.console = console
  
  @property
  def print(self):
    return self.console.print

  def panel(
    self,
    message: str,
    title: str = "",
    type: str = 'info',
    collapsible: bool = False,
    open_by_default: bool = True
  ) -> None:
    self.console.append(Panel(message, title, type, collapsible, open_by_default))

  def table(
    self,
    rows: list[list[Any]],
    columns: list[str],
    border: bool = True,
    striped: bool = True,
    size: str = 'sm',
    align: str = "left"
  ) -> None:
    if not rows:
      self.print("[yellow]No data to display.[/yellow]")
      return None

    table_classes = [
      "table-auto",
      f"text-{size}",
      "w-full",
      "border-separate",
      "border-spacing-x-0.5"
    ]

    align_class = {
      "left": "text-left",
      "center": "text-center",
      "right": "text-right"
    }.get(align, "text-left")

    html = [
      f'<div class="overflow-x-auto"><table class="{" ".join(table_classes)}">'
    ]

    # Header
    html.append("<thead>")
    html.append(f'<tr class="bg-black/30 text-white/80 {align_class}">')

    for column in columns:
      html.append(
        f'<th class="p-2 whitespace-nowrap">'
        f'{clean(column)}</th>'
      )

    html.append("</tr></thead>")

    # Body
    html.append("<tbody>")

    for i, row in enumerate(rows):
      row_bg = "bg-black/10" if striped and i % 2 else "bg-black/5"

      html.append(
        f'<tr class="{row_bg} text-white/70 '
        f'hover:bg-black/20 transition {align_class}">'
      )

      for cell in row:
        safe_html = bclean(
          str(cell),
          tags=["span", "i", "b", "img"]
        )

        html.append(
          f'<td class="p-2 whitespace-nowrap">'
          f'{safe_html}</td>'
        )

      html.append("</tr>")

    html.append("</tbody></table></div>")

    self.console.append("".join(html))

  def mini_table(self, data: dict, color: str = "white/60") -> None:
    # Build table rows with proper text wrapping
    rows = "".join(
      f'<div class="flex justify-between gap-2 py-2 border-b border-white/5 text-{color}">'
      f'<span class="min-w-0 flex-1 font-semibold [overflow-wrap:anywhere]">{clean(str(k))}</span>'
      f'<span class="min-w-0 flex-1 text-right [overflow-wrap:anywhere]">{clean(str(v))}</span>'
      f'</div>'
      for k, v in data.items()
    )

    # Append the table to the console
    self.console.append(f'<div class="px-2 min-w-0">{rows}</div>')
  
  # Code Block
  def code(self, code: str, language: str = "") -> None:
    code = clean(code)
    language = clean(language)
    
    self.console.append(f'<pre class="bg-black/30 text-white/80 text-xs font-mono p-2 overflow-auto whitespace-pre-wrap"><code class="language-{language}">{code}</code></pre>')

  # Copy Text
  def copy_text(self, preview: str, text: str) -> None:
    self.console.append(CopyText(preview, text))

  def quote(self, message: str, author: str = "", color: str = "purple-300") -> None:
    self.console.append(f'''
      <div class="italic text-{color} bg-white/5 p-2 rounded border-l-4 border-{color} break-words">
        “{clean(message)}”
        {f'<div class="text-sm text-right mt-2">— {clean(author)}</div>' if author else ""}
      </div>
    ''')

  # Loading 
  @contextmanager
  def loader(self, text: str = "") -> LoadingText:
    loader = LoadingText(text).add_class("flex items-center justify-center")
    self.console.append(Animate(loader))
    try:
      yield loader
      loader.destroy()
    except Exception as e:
      loader.error(e)

  # Typing text
  def typing_text(
    self, text: str = "",
    delay: float | None = None
  ) -> TypingText:
    el = TypingText()
    self.console.append(el)
    return el.play(text, delay)

  @contextmanager
  def progress(
    self,
    text: str | None = None,
    total: int = 100
  ):
    progress = ProgressBar(
      value=0,
      text=text,
      max_value=total
    )
  
    self.console.append(progress)

    try:
      yield progress
    finally:
      progress.done()
