import flx.loading.hearts

import importlib

from lupa import LuaRuntime
from flx.console import Console



runtime = LuaRuntime()
console = Console()

runtime.globals().scr = console
runtime.globals().print = console.print


def lua_require(name):
  try:
    return importlib.import_module(name)
  except ModuleNotFoundError as e:
    raise RuntimeError(f"Lua module not found: {name}") from e


runtime.globals().py_require = lua_require

runtime.execute("""
local lua_require = require

function require(name)
  local ok, result = pcall(lua_require, name)

  if ok then
    return result
  end

  return py_require(name)
end
""")


def start(path, args):
  with open(path, "r") as file:
    runtime.execute(file.read())