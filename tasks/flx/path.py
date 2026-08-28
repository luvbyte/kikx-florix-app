from os import environ
from pathlib import Path



APP_PATH = Path(environ["KIKX_APP_PATH"])
HOME_PATH = Path(environ["KIKX_HOME_PATH"])
STORAGE_PATH = Path(environ["KIKX_STORAGE_PATH"])
APP_DATA_PATH = Path(environ["KIKX_APP_DATA_PATH"])


# Join path safely
def joinpath(base: str | Path, *parts) -> Path:
  base = Path(base).resolve()
  target = base.joinpath(*parts).resolve()

  if not target.is_relative_to(base):
    raise Exception("Path traversal detected")

  return target

# Ensure directory
def ensure_dir(path: str | Path) -> Path:
  path = Path(path)
  path.mkdir(parents=True, exist_ok=True)
  return path
