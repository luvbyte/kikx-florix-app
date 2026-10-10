import importlib.util
from flx.lib.process import PTYProcess
import sys
import os
from pathlib import Path


def start(path, args):
  spec = importlib.util.spec_from_file_location("user_script", path)
  if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load {path}")

  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)

  func = getattr(module, "start", None)
  if callable(func):
    func()