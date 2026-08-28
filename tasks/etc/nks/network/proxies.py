import flx.loading.hearts

import random
import requests
import subprocess

from pathlib import Path

from flx.console import Console
from flx.console.page import OptionsPage, LoadingPage, InputPage



console = Console()


class OpenProxy:
  def __init__(self):
    self.data_path = Path("data/list_proxies")
    self.data_path.mkdir(parents=True, exist_ok=True)
    
    # Load proxies
    self.proxies = []

    if self.proxies_path.exists():
      self.proxies = self._load_proxies()
    else:
      self.update_proxies(ui=True)

  @property
  def proxies_path(self):
    return self.data_path / "proxies-list.txt"
  
  @property
  def proxies_length(self):
    return len(self.proxies)
  
  def _load_proxies(self):
    return [p for p in self.proxies_path.read_text().strip().splitlines() if p]

  # Update proxies list
  def update_proxies(self, ui=False):
    done = LoadingPage(label="Updating").display(console) if ui else lambda: None

    subprocess.run(
      [
        "curl",
        "-sL",
        "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.txt",
        "-o",
        str(self.proxies_path),
      ],
      text=True
    )
    self.proxies = self._load_proxies()
    
    done()

  # List proxies
  def get_proxies(self, count=None, update=False, startswith=None):
    if update or not self.proxies_path.exists():
      self.update_proxies()
  
    proxies = self.proxies
  
    if startswith:
      proxies = [p for p in proxies if p.startswith(startswith)]
  
    if count is not None:
      return proxies[:count]
  
    return proxies

  # Random proxies
  def get_random(self, proxies, count):
    return random.sample(proxies, min(count, len(proxies)))

open_proxy = OpenProxy()

def ask_count(max_length=None):
  available = max_length or open_proxy.proxies_length
  return int(InputPage(body=f"Availbale ({available})", input_type=int, placeholder=f"Enter proxies count ({available})", min_length=1, max_length=available).display(console).get_input())

def print_proxies(proxies, label=None):
  for proxy in proxies:
    proto, location = proxy.split("://", 1)
    ip, port = location.split(":", 1)
    console.print(f"[red]{proto}[/red] {ip} [green]{port}[/green]", class_list="p-2 border-b border-white/10")

# return proto list
def proto_page():
  protocols = ["http", "socks4", "socks5"]
  result = OptionsPage(protocols, title="Select protocol", back_button=True, close_button=True).display(console)
  
  if result.is_closed:
    return None
  elif result.is_back:
    start()
  else:
    proto = protocols[int(result.get_input()) - 1]
    return open_proxy.get_proxies(startswith=proto)


def start():
  result = OptionsPage([
    "Update proxies",
    "Random proxies",
    "Print proxies",
  ], close_button=True).display(console)
  
  if result.is_closed:
    return None

  option = int(result.get_input())

  if option == 1:
    open_proxy.update_proxies(ui=True)
    start()
  elif option == 2:
    # Get protocol
    proxies = proto_page()

    if not proxies:
      return

    return print_proxies(open_proxy.get_random(proxies, ask_count(max_length=len(proxies))), "Random proxies")
  elif option == 3:
    # Get protocol
    proxies = proto_page()

    if not proxies:
      return

    return print_proxies(proxies[:ask_count(max_length=len(proxies))], "Proxies")
