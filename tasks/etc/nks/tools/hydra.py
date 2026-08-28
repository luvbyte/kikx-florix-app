import flx.loading.hearts

import os
import pty
import subprocess

from flx import js
from flx import panel
from flx.console import Console
from flx.console.page import OptionsPage, FormPage


console = Console()

BANNER = r"""
        ,     \    /      ,        
       / \    )\__/(     / \       
      /   \  (_\  /_)   /   \      
 ____/_____\__\@  @/___/_____\____ 
|             |\../|              |
|              \VV/               |
|        ----------------         |
|_________________________________|
 |    /\ /      \\       \ /\    | 
 |  /   V        ))       V   \  | 
 |/     `       //        '     \| 
 `              V                '

SELECT A MODULE"""

def sh(cmd: str):
  panel.clear(force=True)
  js.set_default_config()

  master, slave = pty.openpty()

  try:
    proc = subprocess.Popen(
      cmd,
      shell=True,
      stdin=slave,
      stdout=slave,
      stderr=slave,
      text=False
    )

    os.close(slave)

    while True:
      try:
        data = os.read(master, 1024)
        if not data:
          break
        print(data.decode(errors="replace"), end="", flush=True)
      except OSError:
        break

    proc.wait()
    return proc.returncode
  finally:
    os.close(master)

class Hydra:
  def __init__(self):
    self.modules = {
      "ssh": self.ssh,
      "ftp": self.ftp,
      "mysql": self.mysql
    }

  def ask_file(self) -> list[str]:
    fpath = console.fs.ask_file(title="Select Wordlist")
    if fpath is None:
      self.exit()

    return str(fpath[0])

  def hydra_ui(self, module, port, title="Options"):
    options = (
      FormPage(title)
        .add_text("host", "Host", required=True, placeholder="127.0.0.1")
        .add_text("user", "User", required=True, placeholder="User")
        .add_text("port", "Port", required=False, placeholder="Port", value=port)
        .add_number("threads", "Threads", placeholder="Number of threads (1-64)", value=4, min=1, max=64, step=1)
        .add_textarea("extra", "Extra", placeholder="Extra Arguments")
      ).display(console)

    if not options:
      self.exit()

    host = options["host"]
    user = options["user"]
    port = options["port"]
    threads = options["threads"]
    extra = options["extra"]

    file = self.ask_file()
    
    sh(f"hydra -l {user} -P {file} -t {threads} -s {port} {extra} {module}://{host}")

  def ssh(self) -> None:
    self.hydra_ui("ssh", 22, "SSH Options")

  def ftp(self) -> None:
    self.hydra_ui("ftp", 21, "FTP Options")
  
  def mysql(self) -> None:
    self.hydra_ui("mysql", 3306, "MySQL Options")

  def run(self):
    option = OptionsPage(
      list(self.modules.keys()),
      title=None,
      banner=BANNER
    ).display(console).get_input()

    list(self.modules.values())[int(option) - 1]()

  def exit(self):
    raise SystemExit


try:
  Hydra().run()
except SystemExit:
  pass
