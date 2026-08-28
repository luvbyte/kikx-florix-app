import re
import json
import difflib
from time import sleep

from typing import Any

from flx import panel, js
from flx.ui.helpers import ClassBuilder
from flx.ui import Div, Animate, Pre
from flx.lib.utils import clean, escape, bclean, get_item, sanitize_html

from flx.widgets.fs import FSWrapper
from flx.widgets.dialogue import AlertWrapper


# Themes: default, neon, matrix, scifi, solarized
class Console:
  def __init__(self, font_size: int = 14, theme: str = "default", padding=None, auto_scroll=True):
    panel.clear()

    self.font_size = font_size
    self.padding = padding

    self._box = Div()
    self.set_theme(theme)

    self.auto_scroll = auto_scroll

    panel.inject(self.box)

  @property
  def box(self):
    return self._box

  def clean(self, *args, **kwargs) -> str:
    return clean(*args, **kwargs)

  def sanitize(self, html_content) -> str:
    return sanitize_html(html_content)
  
  def escape(self, *args, **kwargs) -> str:
    return escape(*args, **kwargs)

  def set_theme(self, theme_name: str) -> None:
    theme = ConsoleThemes.THEMES.get(theme_name)
    if not theme:
      raise Exception(f"Unknown theme: '{theme_name}'")
  
    self.box.cls.clear()
  
    # Build all theme-related classes at once
    base_classes = [
      "relative flex-1 flex flex-col overflow-y-auto overflow-x-hidden",
      theme['bg'],
      theme['text'],
      theme['scrollbar'],
      theme.get('font', 'font-body'),
      theme.get('extras', ''),
      f"text-[{self.font_size}px]",
      ClassBuilder().add_if(f"p-{self.padding}", self.padding).done()
    ]

    # Add them in one call
    self.box.add_class(*filter(None, base_classes))
    self.active_theme = theme
  
  def set_theme_class(self, text: str) -> str:
    self.box.cls.clear()
    self.box.add_class(text)

  def append(self, el, auto_scroll: bool = False) -> None:
    self.box.append(el)
    if self.auto_scroll or auto_scroll:
      self.scroll_to_bottom()

  def replace(self, el) -> None:
    self.box.replace(el)

  def _parse_markup(self, text: str):
    def replacer(match):
      color = match.group(1).lower()
      content = match.group(2)
      return f'<span class="text-{color}-400">{content}</span>'
  
    pattern = re.compile(r'\[([a-zA-Z]+)\](.*?)\[/\1\]', re.DOTALL)
    return pattern.sub(replacer, text)

  def color_box(self, text: str, color: str = "gray", effect="fadeIn"):
    div = Div(f"""
      <div class="bg-{color}-400/60 border-b border-{color}-300/60 p-2 text-{color}-100 shadow-sm">
        {clean(text)}
      </div>
    """)

    self.append(Animate(div, effect=effect) if isinstance(effect, str) else div, auto_scroll=True)

  def print(self, *lines, size=None, center=False, padding=None, dom_purify=True, bg=None, fg=None, class_list="", auto_scroll=False, effect=None):
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
        .add_multiple(class_list.split())
        .done()
      )
    self.append(Animate(div, effect=effect) if isinstance(effect, str) else div, auto_scroll=auto_scroll)

  def pre(self, text: str, height: str = "auto", justify: str = "start", align: str = "start", text_align: str = "start", effect: str = None) -> Pre:
    el = Pre(text)
    el.add_style("height", height)
    el.add_class(
      "text-xs", "flex", f"justify-{justify}", f"items-{align}", f"text-{text_align}"
    )
    self.append(Animate(el, effect=effect) if isinstance(effect, str) else el)
    
    return el

  def pre_center(self, text: str, text_align: str = "start", effect = None, wait: int = 1) -> Pre:
    self.clear()
    el = self.pre(
      text, height="100%", justify="center", align="center", text_align=text_align, effect=effect
    )
    sleep(wait)
    return el

  def input(self, label: str = "", autohide: bool = True, focus: bool = False, effect: str = "slideInUp") -> str:
    js.set_config("block-user-input", False)
    result = js.ask_input(label, autohide=autohide, focus=focus, effect=effect)
    js.set_config("block-user-input", True)
    return result

  def print_error(self, message, *args, **kwargs):
    self.print(f"[red][ERROR][/red] {message}", *args, **kwargs)

  def print_success(self, message, *args, **kwargs):
    self.print(f"[green][OK][/green] {message}", *args, **kwargs)

  def print_json(self, obj: dict):
    self.print(ConsoleHelpers.format_json(obj), dom_purify=False)

  def wait(self, seconds: float) -> None:
    sleep(seconds)

  def hr(self) -> None:
    self.box.append('<div class="w-full bg-white min-h-[1px]"></div>')
    self.scroll_to_bottom()
  
  def br(self, times: int = 1) -> None:
    self.append(Div("<br>" * times))

  def clear(self) -> None:
    self.box.clear()

  @property
  def fs(self) -> FSWrapper:
    return FSWrapper()

  @property
  def alert(self) -> AlertWrapper:
    return AlertWrapper()

  @property
  def wg(self) -> 'ConsoleWidgets':
    return ConsoleWidgets(self)

  def render(self) -> None:
    panel.inject(self.box)
  
  def scroll_to_bottom(self) -> None:
    self.box.scroll_to_bottom()

  def notify(self, message, type: str = 'info', priority: str = "normal") -> None:
    js.notify(message, type=type, priority=priority)

class ConsoleThemes:
  THEMES = {
    'default': {
      'name': 'Default',
      'bg': '',
      'text': 'text-white',
      'scrollbar': 'scrollbar-thin scrollbar-thumb-white/20',
      'border': '',
      'extras': ''
    },
    'neon': {
      'name': 'Neon Green',
      'bg': 'bg-black/60',
      'text': 'text-green-400',
      'scrollbar': 'scrollbar-thin scrollbar-thumb-green-500/20',
      'extras': ''
    },
    'matrix': {
      'name': 'Matrix',
      'bg': 'bg-black/60',
      'text': 'text-green-300',
      'scrollbar': 'scrollbar-thin scrollbar-thumb-green-700/20',
      'extras': 'tracking-wide'
    },
    'scifi': {
      'name': 'Sci-Fi',
      'bg': 'bg-gradient-to-br from-purple-900/60 via-black to-blue-900/60',
      'text': 'text-purple-200',
      'scrollbar': 'scrollbar-thin scrollbar-thumb-purple-500/30',
      'extras': 'shadow-lg'
    },
    'solarized': {
      'name': 'Solarized Dark',
      'bg': 'bg-[#002b36]/60',
      'text': 'text-[#93a1a1]',
      'scrollbar': 'scrollbar-thin scrollbar-thumb-[#586e75]/30',
      'extras': ''
    },
  }

class ConsoleHelpers:
  """Visual and formatting helpers."""
  @staticmethod
  def format_json(obj: dict):
    return f'<pre class="text-xs whitespace-pre-wrap">{json.dumps(obj, indent=2)}</pre>'

class ConsoleWidgets:
  def __init__(self, console):
    self.console = console
    self.print = self.console.print
  
  def panel(
    self,
    message: str,
    title: str = "",
    type: str = 'info',
    collapsible: bool = False,
    open_by_default: bool = True
  ) -> None:
    title = clean(title)
    message = clean(message)

    color_map = {
      'info':    ('bg-blue-500/20', 'text-blue-200'),
      'success': ('bg-green-500/20', 'text-green-200'),
      'warning': ('bg-yellow-500/20', 'text-yellow-200'),
      'error':   ('bg-red-500/20', 'text-red-200'),
    }

    bg_class, text_class = color_map.get(type, (f'bg-{type}/20', f'text-{type}-200'))
  
    # Begin panel content
    header_html = f'<div class="font-bold text-lg">{title}</div>'
    message_html = f'<div class="whitespace-pre-wrap break-all">{message}</div>'

    self.console.append(f'''
      <details {"open" if open_by_default else ""} class="p-2 {bg_class} {text_class} border-l-4 border-white/20 shadow-sm group">
        <summary class="py-2 cursor-pointer font-semibold text-white/90">{title}</summary>
        <div>{message_html}</div>
      </details>
      ''' if collapsible else f'''
      <div class="p-2 {bg_class} {text_class} shadow-sm">
        {header_html}
        {message_html}
      </div>
    ''')

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
      return

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

  def code_block(self, code: str, language: str = ""):
    code = clean(code)
    language = clean(language)

    html = f'<pre class="bg-black/30 text-white/80 text-xs font-mono p-2 overflow-auto whitespace-pre-wrap"><code class="language-{language}">{code}</code></pre>'
    self.console.append(html)

  def copy_box(self, preview: str, copy_text: str):
    escaped_copy = escape(str(copy_text)).replace("'", "\\'")
    escaped_preview = clean(preview)

    html = f'''
      <div class="relative bg-white/5 text-white/80 rounded p-2 text-sm font-mono border border-white/10 shadow-sm">
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
          <div class="overflow-x-auto text-nowrap">{escaped_preview}</div>
          <span class="text-xs px-2 py-1 bg-white/10 hover:bg-white/20 rounded font-semibold transition">
            Copy
          </span>
        </div>
      </div>
    '''
  
    self.console.append(html)

  def mini_table(self, data: dict, color: str = "white/60") -> None:
    rows = "".join([
      f'<div class="flex justify-between py-2 border-b border-white/5 text-{color}">'
      f'<span class="font-semibold">{clean(k)}</span><span>{clean(v)}</span></div>'
      for k, v in data.items()
    ])
    self.console.append(f'<div class="px-2">{rows}</div>')

  def quote_box(self, message: str, author: str = "", color: str = "purple-300") -> None:
    self.console.append(f'''
      <div class="italic text-{color} bg-white/5 p-2 rounded border-l-4 border-{color} break-words">
        “{clean(message)}”
        {f'<div class="text-sm text-right mt-2">— {clean(author)}</div>' if author else ""}
      </div>
    ''')

  def diff(self, old: str, new: str, context_lines: int = 3) -> None:
    if not isinstance(old, str): 
      old = str(old)
    if not isinstance(new, str): 
      new = str(new)
  
    old_lines = old.splitlines()
    new_lines = new.splitlines()
  
    diff_lines = list(difflib.unified_diff(old_lines, new_lines, lineterm="", n=context_lines))
  
    if not diff_lines:
      self.print("[green]No differences detected.[/green]")
      return
  
    html_lines = []
    for line in diff_lines:
      if line.startswith("+") and not line.startswith("+++"):
        html_lines.append(f'<div class="text-green-400">+ {clean(line[1:])}</div>')
      elif line.startswith("-") and not line.startswith("---"):
        html_lines.append(f'<div class="text-red-400">- {clean(line[1:])}</div>')
      elif line.startswith("@@"):
        html_lines.append(f'<div class="text-yellow-500">{clean(line)}</div>')
      else:
        html_lines.append(f'<div class="text-white/70">{clean(line)}</div>')
  
    self.console.append("".join(html_lines))

