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


class IFrame(Element):
  def __init__(self, *_, **kwargs):
    super().__init__(tag="iframe", **kwargs)

  def set_src(self, url):
    self.set_property("src", url)

  def set_doc(self, code):
    self.set_property("srcdoc", code)