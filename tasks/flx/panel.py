from . import js

from .ui.base import recursive_emit
from .ui import render, Element, Template 


def inject(el):
  if isinstance(el, str):
    js.html("#panel", el)
  else:
    js.html("#panel", render(el))
    
  recursive_emit(el, "injected")

def append(el):
  js.append("#panel", render(el))
  
  recursive_emit(el, "injected")

def text(el):
  js.text("#panel", el)

def clear(force=False):
  js.clear_panel(force=force)
