import flx.loading.hearts

import os
import pty
import sys
import subprocess

from flx import panel
from flx.console import Console
from flx.console.page import FormPage


console = Console()

options = (
  FormPage("Cloudflared Tunnel")
  .add_select(
    "mode",
    "Tunnel Mode",
    {
      "Quick Tunnel": "quick",
      "Named Tunnel": "named",
    }
  )
  .add_text("tunnel_name", "Tunnel Name")
  .add_url("service", "Local Service URL", required=True)
  .add_text("hostname", "Public Hostname")
  .add_select(
    "protocol",
    "Protocol",
    {
      "Auto": "auto",
      "HTTP/2": "http2",
      "QUIC": "quic",
    }
  )
  .add_checkbox("no_tls_verify", "Disable TLS Verification", False)
  .add_number("metrics_port", "Metrics Port")
  .add_text("credentials", "Credentials File")
  .add_textarea("extra_args", "Extra Arguments")
  .display(console)
)

if options is None:
  exit()

# Example command construction
args = ["cloudflared"]

if options["mode"] == "quick":
  args += ["tunnel", "--url", options["service"]]

else:
  args += ["tunnel", "run"]

  if options["tunnel_name"]:
    args.append(options["tunnel_name"])

if options["protocol"] and options["protocol"] != "auto":
  args += ["--protocol", options["protocol"]]

if options["no_tls_verify"]:
  args.append("--no-tls-verify")

if options["metrics_port"]:
  args += ["--metrics", f"localhost:{options['metrics_port']}"]

panel.clear(force=True)

master, slave = pty.openpty()

process = subprocess.Popen(
  args,
  stdin=slave,
  stdout=slave,
  stderr=slave,
  close_fds=True,
)

os.close(slave)

while process.poll() is None:
  try:
    data = os.read(master, 4096)
    if data:
      print(data.decode(errors="replace"))
  except OSError:
    break

os.close(master)
process.wait()
