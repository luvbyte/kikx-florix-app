from flx.console import Console
from flx.console.page import FormPage
from flx.lib.process import PTYProcess, CmdBuilder
from flx import panel



console = Console()
console.check_pkgs("whois")


options = (
  FormPage("WHOIS Lookup")
  .add_text(
    "target",
    "Domain / IP",
    required=True,
    placeholder="example.com",
  )
  .add_textarea(
    "extra",
    "Extra Arguments",
    placeholder="Extra WHOIS arguments",
  )
  .display(console)
)

if options is None:
  raise SystemExit


args = (
  CmdBuilder("whois")
  .extend(
    options["extra"].split()
    if options["extra"]
    else None
  )
  .add(options["target"])
  .build()
)


panel.clear(force=True)

PTYProcess(args, print).run()
