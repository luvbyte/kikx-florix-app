from sys import argv
from pathlib import Path

from importlib import import_module


def run_script(path: Path, args):
  if not path.exists():
    raise FileNotFoundError(f"Script ({path} not found)")

  scripts = {
    "": "bix",
    ".sh": "bix",
    ".lua": "lux",
    ".py": "pyx",

    ".js": "webx",
    ".html": "webx"
  }

  script = scripts.get(path.suffix, None)
  if script is None:
    raise KeyError(f"Can't run '{path.suffix}' format")

  module = import_module(f"etc.anyx.{script}")
  func = getattr(module, "start", None)
  if func is None:
    return None

  func(path, args)


def main():
  path = argv[1]
  args = argv[2:]

  try:
    run_script(Path(path), args)
  except Exception:
    raise


if __name__ == "__main__":
  main()