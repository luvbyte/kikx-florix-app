import sys
import importlib.util

from pathlib import Path
from flx.js import clear_panel


class PyX:
  def __init__(self, script_path: str):
    self.script_path = script_path

def run_py_script(path, args):
  spec = importlib.util.spec_from_file_location("user_script", path)
  if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load {path}")

  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  
  init_func = getattr(module, "init", None)
  if callable(init_func):
    init_func(PyX(path))

  func = getattr(module, "start", None)
  if callable(func):
    func()

def run_from_url(url, args):
  pass

def main():
  path = sys.argv[1]
  args = sys.argv[2:]

  try:
    if path.startswith("https://"):
      return run_from_url(path, args)

    run_py_script(path, args)
  except Exception as e:
    clear_panel(True)
    raise e

if __name__ == "__main__":
  main()


