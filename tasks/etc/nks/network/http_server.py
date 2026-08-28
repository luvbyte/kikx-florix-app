import flx.loading.hearts

import os
import pty
import sys
import subprocess

from flx.ui import Div, Text
from flx.console import Console
from flx.lib.utils import clean
from flx.console.page import FormPage

console = Console()

path = console.fs.ask_directory()
if path is None:
  exit()

path = str(path[0])

options = (
  FormPage("Service Options")
  .add_text("host", "Host", value="0.0.0.0")
  .add_number("port", "Port", value="8000")
  .display(console)
)

if options is None:
  exit()

host = options["host"]
port = options["port"]

master, slave = pty.openpty()

process = subprocess.Popen(
  [
    sys.executable,
    "-m",
    "http.server",
    port,
    "--bind",
    host,
    "--directory",
    path,
  ],
  stdin=slave,
  stdout=slave,
  stderr=slave,
  close_fds=True,
)

os.close(slave)

console.print("INFO", padding=2, center=True, bg="purple-400/40")
console.wg.copy_box(f"http://{host}:{port}", f"http://{host}:{port}")

console.print(path, padding=1, bg="blue-400/40")

el = Div().add_class("flex flex-col p-1 gap-1 text-xs overflow-y-auto")
console.append(el)

def print(text):
  el.append(Text(clean(text)))
  el.scroll_to_bottom()

try:
  while process.poll() is None:
    try:
      data = os.read(master, 4096)
      if data:
        print(data.decode(errors="replace"))
    except OSError:
      break
except Exception:
  raise
finally:
  os.close(master)
  process.wait()
