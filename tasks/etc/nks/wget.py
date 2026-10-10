import flx.loading.hearts

import os
import sys

from flx import panel
from flx.console import Console
from flx.console.page import FormPage
from flx.lib.process import PTYProcess, CmdBuilder



console = Console()
console.check_pkgs("wget")

options = (
  FormPage("Wget File Downloader")
  .add_url("url", "Download URL", required=True)
  .add_path("directory", "Download Path", type="directory", required=True)
  .add_text("output", "Output Filename")
  .add_number("tries", "Retry Attempts")
  .add_number("timeout", "Timeout (seconds)")
  .add_checkbox("continue", "Resume Download", False)
  .add_checkbox("no_clobber", "Don't Overwrite Existing File", False)
  .add_checkbox("show_progress", "Show Progress", True)
  .add_checkbox("notify", "Notify on complete", False)
  .add_textarea("extra_args", "Extra Arguments")
  .display(console)
)

if options is None:
  exit()

url = options["url"]

builder = (
  CmdBuilder("wget")
  .flag("-c", options["continue"])
  .flag("-nc", options["no_clobber"])
  .option("-t", options["tries"])
  .option("-T", options["timeout"])
  .option("-P", options["directory"])
  .option("-O", options["output"])
)

if not options["show_progress"]:
  builder.flag("-q")

if options["extra_args"]:
  builder.extend(options["extra_args"].split())

builder.add(url)

args = builder.build()

panel.clear(force=True)

process = PTYProcess(args, print)

process.run()

if options["notify"]:
  if process.is_ok:
    console.notify(f"Wget: Download successful - {url}")
  else:
    console.notify(f"Wget: Download failed - {url}")