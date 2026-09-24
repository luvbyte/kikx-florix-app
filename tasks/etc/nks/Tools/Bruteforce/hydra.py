import flx.loading.hearts

from flx import js
from flx import panel
from flx.console import Console
from flx.lib.process import PTYProcess, CmdBuilder
from flx.console.page import OptionsPage, FormPage


console = Console()
console.check_pkgs("hydra")


class Hydra:
  def __init__(self):
    self.modules = {
      "ssh": self.ssh,
      "ftp": self.ftp,
      "mysql": self.mysql,
    }

  def ask_file(self):
    fpath = console.fs.ask_file(title="Select Wordlist")

    if fpath is None:
      self.exit()

    return str(fpath[0])

  def hydra_ui(self, module, port, title="Options"):
    options = (
      FormPage(title)
      .add_text(
        "host",
        "Host",
        required=True,
        placeholder="127.0.0.1",
      )
      .add_text(
        "user",
        "User",
        required=True,
        placeholder="User",
      )
      .add_text(
        "port",
        "Port",
        required=False,
        placeholder="Port",
        value=port,
      )
      .add_number(
        "threads",
        "Threads",
        placeholder="Number of threads (1-64)",
        value=4,
        min=1,
        max=64,
        step=1,
      )
      .add_textarea(
        "extra",
        "Extra",
        placeholder="Extra Arguments",
      )
      .display(console)
    )

    if not options:
      self.exit()

    file = self.ask_file()

    args = (
      CmdBuilder("hydra")
      .option("-l", options["user"])
      .option("-P", file)
      .option("-t", options["threads"])
      .option("-s", options["port"])
      .extend(
        options["extra"].split()
        if options["extra"]
        else None
      )
      .add(f"{module}://{options['host']}")
      .build()
    )

    panel.clear(force=True)
    js.set_default_config()

    PTYProcess(args, print).run()

  def ssh(self):
    self.hydra_ui("ssh", 22, "SSH Options")

  def ftp(self):
    self.hydra_ui("ftp", 21, "FTP Options")

  def mysql(self):
    self.hydra_ui("mysql", 3306, "MySQL Options")

  def run(self):
    option = (
      OptionsPage(
        list(self.modules.keys()),
        title="Select module",
      )
      .display(console)
      .value
    )

    list(self.modules.values())[option - 1]()

  def exit(self):
    raise SystemExit


try:
  Hydra().run()
except SystemExit:
  pass