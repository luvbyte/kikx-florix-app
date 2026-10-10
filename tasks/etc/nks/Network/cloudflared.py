import flx.loading.hearts

import os
import pty
import sys
import subprocess

from flx import panel
from flx.console import Console
from flx.console.page import FormPage

from flx.lib.process import PTYProcess


console = Console()
console.check_pkgs("cloudflared")


options = (
  FormPage("Cloudflared Tunnel")
  .add_select(
    "mode",
    "Tunnel Mode",
    {
      "quick": "Quick Tunnel",
      "named": "Named Tunnel"
    }
  )
  .add_text("tunnel_name", "Tunnel Name")
  .add_url("service", "Local Service URL", required=True)
  .add_text("hostname", "Public Hostname")
  .add_select(
    "protocol",
    "Protocol",
    {
      "auto": "Auto",
      "http2": "HTTP/2",
      "quic": "QUIC"
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

PTYProcess(args, print).run()