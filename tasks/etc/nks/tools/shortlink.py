import flx.loading.hearts

import requests

from flx.ui import Div
from urllib.parse import quote
from flx.console import Console
from flx.console.page import FormPage


console = Console()


def shorten_tinyurl(url):
  response = requests.get(
    "https://tinyurl.com/api-create.php",
    params={"url": url},
    timeout=10,
  )
  response.raise_for_status()
  result = response.text.strip()

  if not result.startswith("http"):
    raise RuntimeError(result)

  return result

options = (
  FormPage("Short Link Generator")
  .add_url(
    "url",
    "URL to Shorten",
    required=True,
  )
  .add_checkbox("qr", "Generate QR")
  .display(console)
)

if options is None:
  exit()

url = options["url"]
generate_qr = options["qr"]

console.append(Div("""
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
""").add_class("flex-1 flex flex-col justify-center items-center"))

try:
  short_url = shorten_tinyurl(url)
except Exception as e:
  console.clear()
  console.print("Failed to create short link:")
  console.print(str(e))
  exit(1)

console.clear()

console.print("Link Created", padding=3, center=True, bg="purple-400/40")
console.wg.copy_box(short_url, short_url)

console.print(url, padding=2, bg="blue-400/40")

if generate_qr:
  qr_url = (
    "https://api.qrserver.com/v1/create-qr-code/"
    "?size=200x200"
    f"&data={quote(short_url)}"
  )
  console.append(
    Div(
      f'<img src="{qr_url}" />',
    ).add_class("w-full py-6 flex justify-center items-center")
  )
