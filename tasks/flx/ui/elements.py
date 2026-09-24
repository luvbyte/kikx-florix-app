from flx import js
from flx.lib.utils import clean

from .base import Element

from typing import Any



class Div(Element):
  def __init__(self, *children, **kwargs):
    super().__init__(*children, **kwargs)


class Pre(Element):
  def __init__(self, *children, **kwargs):
    super().__init__(*children, tag="pre", **kwargs)


class Center(Element):
  def __init__(self, *children, **kwargs):
    super().__init__(*children, **kwargs)
    self.cls.add("w-full", "h-full", "flex", "items-center", "justify-center")


class Text(Element):
  def __init__(self, text: str = "", **kwargs):
    super().__init__(clean(text), tag="p", **kwargs)

  def set_text(self, text: str) -> str:
    return self.inner_text(text)





# class Box(Element):
#   def __init__(self, child: Element | None = None, width: str = "auto", height: str = "auto", fullscreen: bool = False):
#     super().__init__(child)
#     width, height = ("100%", "100%") if fullscreen else (width, height)
#     self.style.add("width", width)
#     self.style.add("height", height)
