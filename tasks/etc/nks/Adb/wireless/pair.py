from flx.console import Console
from flx.console.page import InputPage

from flx.lib.process import sh


console = Console(padding=2)
console.check_pkgs("adb")


def print(text):
  console.print(text)

host = InputPage("Enter device IP", placeholder="Type here").display(console).value
port = InputPage("Enter Port", input_type=int, placeholder="Type here").display(console).value
code = InputPage("Pairing Code", input_type=int, placeholder="Type here").display(console).value


console.clear()
print(f"Pairing: [blue]{host}[/blue]:{port} [red]{code}[/red]")

result = sh(f"adb pair {host}:{port} {code}").run()

print(result.text())

