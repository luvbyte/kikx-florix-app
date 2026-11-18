from flx.ui import Text, Div, Animate
from flx.lib.utils import clean



class ProgressBar(Div):
  def __init__(
    self,
    value: int = 0,
    text: str | None = None,
    max_value: int = 100
  ):
    self.max = max_value
    self.value = max(0, min(value, max_value))

    self.label = Text(text or "")
    self.value_text = Text(f"{self.percent}%")

    self.fill = Div()
    self.fill.add_class(
      "h-full",
      "rounded-full",
      "bg-blue-500",
      "transition-all",
      "duration-300",
    )

    self.track = Div(self.fill)
    self.track.add_class(
      "h-2",
      "w-full",
      "overflow-hidden",
      "rounded-full",
      "bg-white/10"
    )

    header = Div(
      self.label,
      self.value_text
    ).add_class(
      "flex",
      "items-center",
      "justify-between",
      "mb-1"
    )

    super().__init__(
      header,
      self.track
    )

    self.add_class("w-full bg-white/10 p-2")

    self._update_fill()

  @property
  def percent(self) -> int:
    if self.max <= 0:
      return 0

    return round((self.value / self.max) * 100)

  def _update_fill(self):
    self.fill.add_style(
      "width",
      f"{self.percent}%"
    )

  def set(self, value: int):
    self.value = max(0, min(value, self.max))

    self._update_fill()

    self.value_text.inner_text(
      f"{self.percent}%"
    )

    return self

  def update(self, amount: int = 1):
    return self.set(self.value + amount)

  def increment(self, amount: int = 1):
    return self.update(amount)

  def decrement(self, amount: int = 1):
    return self.update(-amount)

  def done(self):
    return self.set(self.max)

  def reset(self):
    return self.set(0)

  def iter(self, iterable, total: int | None = None):
    if total is None:
      try:
        total = len(iterable)
      except TypeError:
        total = 0

    self.max = total
    self.set(0)
  
    for item in iterable:
      yield item
      self.update()
  
    if total:
      self.done()


class Panel(Div):
  def __init__(
    self,
    message: str,
    title: str = "",
    type: str = 'info',
    collapsible: bool = False,
    open_by_default: bool = True
  ):
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

    super().__init__(f'''
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
