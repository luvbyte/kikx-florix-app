from flx.console import Console
from flx.console.page import FormPage

from flx.lib.process import sh


console = Console()
console.check_pkgs("adb")


options = (
  FormPage("Adb pair options")
  .add_text("host", "Host", required=True)
  .add_number("port", "Port", required=True)
  .add_number("code", "Pair Code", required=True)
  .display(console)
)

if not options:
  exit()

host = options["host"]
port = options["port"]
code = options["code"]

console.clear()
print(f"Pairing: [blue]{host}[/blue]:{port} [red]{code}[/red]")

result = sh(f"adb pair {host}:{port} {code}").run()

print(result.text())

