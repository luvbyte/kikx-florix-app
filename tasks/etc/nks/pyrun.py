import flx.loading.hearts

import sys
import shlex
import requests

from flx.console import Console
from flx.console.page import FormPage



console = Console()


def fetch_script(url: str, timeout: int = 30) -> str:
  """Fetch Python source code from a URL."""
  try:
    response = requests.get(
      url,
      timeout=timeout,
      headers = {
        "User-Agent": (
          "Mozilla/5.0 (X11; Linux x86_64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/131.0.0.0 Safari/537.36"
        )
      }
    )

    response.raise_for_status()
    response.encoding = "utf-8"
    code = response.text

    if not code.strip():
      raise ValueError("The URL returned an empty script.")

    return code

  except requests.exceptions.Timeout:
    raise RuntimeError(
      f"Request timed out after {timeout} seconds."
    )

  except requests.exceptions.RequestException as exc:
    raise RuntimeError(f"Failed to fetch script: {exc}") from exc


def execute_code(code: str, args: list):
  """Execute Python source code."""

  sys.argv = ["<remote-script>", *args]

  d_namespace = {
    "__name__": "__main__",
    "__file__": "<remote-script>",
    "input": console.input,
  }

  if code.startswith("#[florix-script]"):
    namespace = {
      **d_namespace,
      "console": console,
      "print": console.print,
    }

    console.clear()
  else:
    from flx import js

    namespace = d_namespace.copy()
    
    js.clear_panel(True)

  exec(compile(code, "<remote-script>", "exec"), namespace)


def start():
  options = (
    FormPage("Python script runner")
      .add_url("url", "Script URL", required=True)
      .add_textarea("args", "", placeholder="Type args here")
      .add_number(
        "timeout",
        "Request Timeout (seconds)",
        value=30
      )
      .display(console)
  )

  if options is None:
    exit()

  url = options["url"]
  args = shlex.split(options["args"])
  timeout = int(options["timeout"] or 30)

  if timeout <= 0:
    console.print("Timeout must be greater than zero.")
    return

  try:
    console.pre(
      '<svg xmlns="http://www.w3.org/2000/svg" class="animate-pulse" width="46" height="46" viewBox="0 0 24 24"><path d="M0 0h24v24H0z" fill="none" /><path fill="currentColor" fill-rule="evenodd" d="M12 1a1.5 1.5 0 0 0-1.5 1.5V4a1.5 1.5 0 0 0 3 0V2.5A1.5 1.5 0 0 0 12 1m3.5 5.5a1.5 1.5 0 0 1 3 0V8a1.5 1.5 0 0 1-3 0zM5.5 7a1.5 1.5 0 1 1 3 0v4.5a1.5 1.5 0 0 1-3 0zM12 7a1.5 1.5 0 0 0-1.5 1.5v7a1.5 1.5 0 0 0 3 0v-7A1.5 1.5 0 0 0 12 7M2.5 9.75a1.5 1.5 0 0 0-1.5 1.5v1.5a1.5 1.5 0 0 0 3 0v-1.5a1.5 1.5 0 0 0-1.5-1.5m3 6.25a1.5 1.5 0 0 1 3 0v1.5a1.5 1.5 0 0 1-3 0zm6.5 2.5a1.5 1.5 0 0 0-1.5 1.5v1.5a1.5 1.5 0 0 0 3 0V20a1.5 1.5 0 0 0-1.5-1.5m9.5-8.75a1.5 1.5 0 0 0-1.5 1.5v1.5a1.5 1.5 0 0 0 3 0v-1.5a1.5 1.5 0 0 0-1.5-1.5m-6 2.75a1.5 1.5 0 0 1 3 0V17a1.5 1.5 0 0 1-3 0z" clip-rule="evenodd" /></svg>',
      justify="center",
      align="center",
      text_align="center",
      height="100%"
    )

    code = fetch_script(url, timeout)

    execute_code(code, args)

  except Exception as exc:
    raise Exception("Error running code: ", exc)


if __name__ == "__main__":
  start()