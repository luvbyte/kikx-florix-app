from flx.console import Console
from flx.console.page import FormPage

from flx.lib.process import sh

console = Console()
console.check_pkgs("adb")


options = (
  FormPage("Adb connect options")
  .add_text("host", "Host", required=True)
  .add_number("port", "Port", required=True)
  .display(console)
)

if not options:
  exit()

host = options["host"]
port = options["port"]

console.clear()
print(f"Connecting: [blue]{host}[/blue]:{port}")

result = sh(f"adb connect {host}:{port}").run()

print(result.text())
