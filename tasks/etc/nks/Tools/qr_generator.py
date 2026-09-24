import flx.loading.hearts

from urllib.parse import quote

from flx.console import Console
from flx.console.page import FormPage, IframePage

from flx.ui import Div
from flx.lib.utils import clean

console = Console()

options = (
  FormPage("Generate QR Code")
  .add_textarea(
    "data",
    "Text / URL",
    required=True,
  )
  .display(console)
)

if options is None:
  exit()

data = options["data"]

qr_url = (
  "https://api.qrserver.com/v1/create-qr-code/"
  "?size=200x200"
  f"&data={quote(data)}"
)

loader = Div("""
 <svg xmlns="http://www.w3.org/2000/svg" class="mb-8" width="46" height="46" viewBox="0 0 24 24">
	<path d="M0 0h24v24H0z" fill="none" />
	<circle cx="18" cy="12" r="0" fill="currentColor">
		<animate attributeName="r" begin=".67" calcMode="spline" dur="1.5s" keySplines="0.2 0.2 0.4 0.8;0.2 0.2 0.4 0.8;0.2 0.2 0.4 0.8" repeatCount="indefinite" values="0;2;0;0" />
	</circle>
	<circle cx="12" cy="12" r="0" fill="currentColor">
		<animate attributeName="r" begin=".33" calcMode="spline" dur="1.5s" keySplines="0.2 0.2 0.4 0.8;0.2 0.2 0.4 0.8;0.2 0.2 0.4 0.8" repeatCount="indefinite" values="0;2;0;0" />
	</circle>
	<circle cx="6" cy="12" r="0" fill="currentColor">
		<animate attributeName="r" begin="0" calcMode="spline" dur="1.5s" keySplines="0.2 0.2 0.4 0.8;0.2 0.2 0.4 0.8;0.2 0.2 0.4 0.8" repeatCount="indefinite" values="0;2;0;0" />
	</circle>
</svg>
""").add_class("absolute z-90 w-full h-full flex flex-col justify-center items-center")

console.append(loader)

console.append(
  Div(
    f'<img src="{qr_url}" onload="$(\'#{loader.id}\').fadeOut()" />',
    f'<div class="px-2 break-words">{clean(str(data))}</div>'
  ).add_class("flex-1 flex flex-col justify-center items-center gap-1")
)
