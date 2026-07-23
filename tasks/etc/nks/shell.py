import os
import json
from subprocess import PIPE
from flx import js, panel
from flx.lib.process import sh


INTRO = """
SIMPLE SHELL

🟨🟨🟨🟨🟨🟨🟨🟨🟨
🟨🟨🟨🟨🟨🟨🟨🟨🟨
🟨🐧🟨🐧🟨🐧🟨🐧🟨
🟧🟧🟧🟧🟧🟧🟧🟧🟧

It's not a real TTY.
Long-running programs may not work.

"""


js.set_config("block-user-clear", False)
js.set_config("block-user-input", False)

js.run_code("$panel.addClass('p-1')")

def print_command(command, error=False):
  js.set_config("parse-ansi", False)
  
  name = "bg-red-400/60" if error else "bg-blue-400/60"
  
  print(f'<div class="mb-0.5 p-1 {name} rounded">{command}</div>')
  js.set_config("parse-ansi", True)

def print_intro():
  panel.append(f'<pre class="flex justify-center text-center pt-1 bg-purple-400/20 rounded mb-1 animate__animated animate__fadeIn">{INTRO}</pre>')

print_intro()

while True:
  input_text = js.ask_input("Enter command", autohide=False, effect="fadeIn").strip()
  
  print_command(input_text)

  if input_text == "exit":
    break
  elif input_text == "clear":
    js.run_code("clearPanel()")
  elif input_text.startswith("cd"):
    try:
      parts = input_text.split(maxsplit=1)
      dest = "~" if len(parts) == 1 else parts[1]
      
      dest = os.path.expanduser(dest)
      os.chdir(dest)
      
      print(f"Cwd: {os.getcwd()}")
    except Exception as e:
      print_command(f"Error : {e}", error=True)
  else:
    process = sh(input_text).pipe(stderr=PIPE)
    
    error = process.error().strip()
    
    if process.returncode != 0 and error: # success
      print_command(f"Error ({process.returncode}): {error}", error=True)

