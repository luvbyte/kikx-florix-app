import flx.loading.hearts

from flx import panel
from flx.console import Console
from flx.console.page import FormPage
from flx.lib.process import PTYProcess, CmdBuilder


console = Console()
console.check_pkgs("nmap")


options = (
  FormPage("Nmap Scanner")
  .add_text(
    "target",
    "Target",
    required=True
  )
  .add_select(
    "scan_type",
    "Scan Type",
    {
      "default": "Default Scan",
      "syn": "SYN Scan (-sS)",
      "tcp": "TCP Connect Scan (-sT)",
      "udp": "UDP Scan (-sU)",
      "ack": "ACK Scan (-sA)",
      "fin": "FIN Scan (-sF)",
      "null": "NULL Scan (-sN)",
      "xmas": "Xmas Scan (-sX)",
      "ping": "Ping Scan (-sn)",
    }
  )
  .add_text(
    "ports",
    "Ports",
    placeholder="e.g. 22,80,443 or 1-1000"
  )
  .add_select(
    "service_detection",
    "Service Detection",
    {
      "no": "Disabled",
      "yes": "Enable Version Detection (-sV)"
    }
  )
  .add_select(
    "os_detection",
    "OS Detection",
    {
      "no": "Disabled",
      "yes": "Enable OS Detection (-O)"
    }
  )
  .add_select(
    "timing",
    "Timing",
    {
      "T0": "Paranoid",
      "T1": "Sneaky",
      "T2": "Polite",
      "T3": "Normal",
      "T4": "Aggressive",
      "T5": "Insane",
    }
  )
  .add_checkbox(
    "scripts",
    "Default NSE Scripts (-sC)",
    False
  )
  .add_checkbox(
    "traceroute",
    "Traceroute (--traceroute)",
    False
  )
  .add_checkbox(
    "verbose",
    "Verbose Output (-v)",
    False
  )
  .add_checkbox(
    "reason",
    "Show Scan Reasons (--reason)",
    False
  )
  .add_text(
    "interface",
    "Network Interface",
    placeholder="e.g. eth0"
  )
  .add_text(
    "source_port",
    "Source Port",
    placeholder="e.g. 53"
  )
  .add_textarea(
    "extra_args",
    "Extra Arguments",
    placeholder="e.g. -Pn --open"
  )
  .display(console)
)

if options is None:
  exit()


scan_types = {
  "syn": "-sS",
  "tcp": "-sT",
  "udp": "-sU",
  "ack": "-sA",
  "fin": "-sF",
  "null": "-sN",
  "xmas": "-sX",
  "ping": "-sn",
}


args = (
  CmdBuilder("nmap")

  # Scan type
  .choice(
    options["scan_type"],
    scan_types,
  )

  # Ports
  .option(
    "-p",
    options["ports"],
  )

  # Service/version detection
  .flag(
    "-sV",
    options["service_detection"] == "yes",
  )

  # OS detection
  .flag(
    "-O",
    options["os_detection"] == "yes",
  )

  # Timing
  .flag(
    f"-{options['timing']}",
    bool(options["timing"]),
  )

  # Default NSE scripts
  .flag(
    "-sC",
    options["scripts"],
  )

  # Traceroute
  .flag(
    "--traceroute",
    options["traceroute"],
  )

  # Verbose
  .flag(
    "-v",
    options["verbose"],
  )

  # Scan reasons
  .flag(
    "--reason",
    options["reason"],
  )

  # Network interface
  .option(
    "-e",
    options["interface"],
  )

  # Source port
  .option(
    "--source-port",
    options["source_port"],
  )

  # Extra arguments
  .extend(
    options["extra_args"].split()
    if options["extra_args"]
    else None,
  )

  # Target must be last
  .add(
    options["target"],
  )

  .build()
)


panel.clear(force=True)

PTYProcess(args, print).run()