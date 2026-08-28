import flx.loading.hearts

import shlex
import subprocess

from time import sleep
from pathlib import Path

from flx.js import invoke
from flx.lib.utils import clean
from flx.console import Console
from flx.utils import generate_uuid
from flx.ui import Div, Text, Animate
from flx.console.page import SelectionPage
from flx.path import HOME_PATH, ensure_dir, joinpath

from concurrent.futures import ThreadPoolExecutor



CLIST = [
  # Basic details and screenshot
  ["shell getprop", "props.txt"],
  ["exec-out screencap -p", "screenshot.png"],

  # Contacts, Sms, Call logs
  ["shell content query --uri content://sms", "messages.txt"],
  ["shell content query --uri content://contacts/phones/", "contacts.txt"],
  ["shell content query --uri content://call_log/calls", "call_logs.txt"],
  
  # Device settings
  ["shell settings list system", "settings_system.txt"],
  ["shell settings list secure", "settings_secure.txt"],
  ["shell settings list global", "settings_global.txt"],
  
  # Android apps list
  ["shell pm list packages", "packages.txt"],
  ["shell pm list packages -s", "packages_system.txt"],
  ["shell pm list packages -3", "packages_user.txt"],
  
  # Get system info
  ["shell df -h", "storage_info.txt"],
  ["shell cat /proc/cpuinfo", "cpu_info.txt"],
  ["shell cat /proc/meminfo", "mem_info.txt"],
  ["shell dumpsys sensorservice", "sensors_info.txt"],
  
  # Network information
  ["shell ip addr", "network_interfaces_info.txt"],
  ["shell ip route", "network_ip_route_info.txt"],
  
  # Get clipboard text
  ["shell service call clipboard 1", "clipboard.txt"],
]

# ---------------- Screen
class ConsoleScreen(Console):
  def __init__(self) -> None:
    super().__init__()

  def log(self, message, color="blue", title=None):
    message = clean(str(message))
    color = clean(str(color))

    if title:
      title = f"""
        <div class="w-full bg-{color}-400/20 px-3 py-2 rounded-t truncate">
          {clean(str(title))}
        </div>
      """

    el = Div(f"""
      {title or ''}
      <div class="flex w-full justify-between items-center px-2">
        <div class="min-w-1 h-full bg-{color}-400 rounded-l"></div>
        <div class="flex-1 text-center bg-{color}-400/20 p-2 break-all">{message}</div>
        <div class="min-w-1 h-full bg-{color}-400 rounded-r"></div>
      </div>
    """).add_class("w-full flex flex-col gap-2 mt-2")

    self.append(Animate(el))
  
  def table_rows(self, data: dict) -> str:
    return "".join(
      f"""
      <div class="flex justify-between items-center gap-4 p-2">
        <span class="font-medium">{clean(str(key))}</span>
        <span class="text-right break-all">{clean(str(value))}</span>
      </div>
      """
      for key, value in data.items()
    )

  def table(self, title, data: dict, color="blue"):
    color = clean(str(color))
    rows = self.table_rows(data)

    el = Div(f'<div class="bg-{color}-400/20 p-2 text-center">{clean(str(title))}</div>', rows).add_class(
      f"w-full bg-{color}-400/20 text-white mt-2"
    )

    self.append(Animate(el))

scr = ConsoleScreen()

# ---------------- Utils
def sh(command: str, input_text: list[str] = [], shell: bool = False) -> str:
  result = subprocess.run(command if shell else command.strip().split(), capture_output=True, shell=shell, text=True, input="\n".join(input_text))
  if result.returncode != 0:
    raise Exception(result.stderr.strip())
  return result.stdout.strip()

def adb(command: str, input_text: list[str] = [], shell: bool = False) -> str:
  return sh(f"adb {command}", input_text=input_text, shell=shell)

def prop(serial: str, name: str) -> str:
  return adb(f"-s {serial} shell getprop {name}")

# ---------------- Device
class Config:
  def __init__(self) -> None:
    self.path: Path = ensure_dir(HOME_PATH / "etc/xadb")

    self.scripts_dir: Path = ensure_dir(self.path / "scripts")
    self.uploads_dir: Path = ensure_dir(self.path / "uploads")

class Device:
  def __init__(self, serial: str, uploads_dir) -> None:
    self.id: str = generate_uuid()
    self.serial: str = serial
    self.model: str = prop(self.serial, "ro.product.model")
    self.manufacturer: str = prop(self.serial, "ro.product.manufacturer")

    self.uploads_name: str = f"{self.manufacturer}_{self.model}_{self.id}"

    # / device path
    self.path: Path = ensure_dir(uploads_dir / self.uploads_name)
    # / device/files
    self.files_path: Path = ensure_dir(self.path / "files")

  @property
  def name(self) -> str:
    return f"{self.manufacturer} {self.model}"

  # Execute adb command
  def exec(self, command: str, shell: bool = False) -> str:
    return adb(f"-s {self.serial} {command}", shell=shell)

  # Run shell command
  def shell(self, command: str, shell: bool = False) -> str:
    return self.exec(f"shell {command}", shell=shell)

  # Pull file from device 
  def pull(self, line: str, script_name: str) -> None:
    try:
      src, filename = shlex.split(line)

      dest_dir: Path = ensure_dir(joinpath(self.files_path, script_name))
      self.exec(f"pull {src} {joinpath(dest_dir / filename)}")

      scr.log(src, color="green", title=script_name)
    except Exception:
      scr.log(src, color="red", title=script_name)

  # Save to file
  def save_to_file(self, command: str, filename: str) -> None:
    try:
      self.exec(f"{command} > {self.path / filename}", shell=True)
      scr.log(filename.capitalize(), color="purple")
    except Exception:
      scr.log(filename.capitalize(), color="red")

class XADB:
  def __init__(self) -> None:
    self.config: Config = Config()
    self.selected: Device | None = None

  def get_scripts_list(self) -> list[str]:
    return [p.stem for p in self.config.scripts_dir.iterdir() if p.suffix == ".xadb"]

  def list_devices(self) -> list[Device]:
    output = adb("devices")
    devices = []

    for index, line in enumerate(output.splitlines()):
      if index == 0:
        continue

      serial, status = line.split()
      if status == "offline":
        continue
      
      devices.append(Device(serial, self.config.uploads_dir))

    return devices

  def listen_devices(self, delay: float = 1) -> None:
    while True:
      devices_list = self.list_devices()
  
      if len(devices_list) > 0:
        return devices_list
  
      sleep(delay)

  def display_devices(self) -> Device:
    devices_list = self.listen_devices()
    
    el = Div().add_class("flex-1 flex flex-col overflow-y-auto")

    scr.clear()
    el.append('<div class="p-2 py-4 text-center font-semibold bg-purple-400/60">Select a device</div>')

    while True:
      for index, device in enumerate(devices_list):
        el.append(f"""
          <div
            onclick="sendInput('__select__{index}')"
            class="px-4 py-3 bg-purple-400/40 hover:bg-purple-400/60
             border-b border-purple-300/20
             text-white cursor-pointer
             transition-all duration-200
             hover:pl-5 hover:shadow-sm
             active:bg-purple-400/70"
          >
            <div class="font-medium">{device.name}</div>
            <div class="text-sm text-white/60 mt-0.5">{device.serial}</div>
          </div>
        """)
      
      scr.append(Animate(el))

      input_text = input().strip()
      if input_text.startswith("__select__"):
        return devices_list[int(input_text[10:])]

  def display_scripts(self) -> list[str]:
    if not self.selected:
      return None

    page = SelectionPage({
      name.capitalize(): name for name in self.get_scripts_list()
    }, title="Select scripts to run")

    return page.display(scr) or []

  def run_script(self, name: str) -> None:
    code = joinpath(self.config.scripts_dir / f"{name}.xadb").read_text()
    for line in code.splitlines():
      line = line.strip()

      if line.startswith("//") or len(line) <= 0:
        continue

      self.selected.pull(line, script_name=name)

  # ---------------- Main
  def run_scripts(self, scripts: list[str]) -> None:
    for name in scripts:
      self.run_script(name)

  def run_clist(self) -> None:
    for line in CLIST:
      self.selected.save_to_file(*line)

  def start(self) -> None:
    scr.pre_center('<svg xmlns="http://www.w3.org/2000/svg" class="animate-pulse" width="46" height="46" viewBox="0 0 24 24"><path d="M0 0h24v24H0z" fill="none" /><path fill="currentColor" fill-rule="evenodd" d="M12 1a1.5 1.5 0 0 0-1.5 1.5V4a1.5 1.5 0 0 0 3 0V2.5A1.5 1.5 0 0 0 12 1m3.5 5.5a1.5 1.5 0 0 1 3 0V8a1.5 1.5 0 0 1-3 0zM5.5 7a1.5 1.5 0 1 1 3 0v4.5a1.5 1.5 0 0 1-3 0zM12 7a1.5 1.5 0 0 0-1.5 1.5v7a1.5 1.5 0 0 0 3 0v-7A1.5 1.5 0 0 0 12 7M2.5 9.75a1.5 1.5 0 0 0-1.5 1.5v1.5a1.5 1.5 0 0 0 3 0v-1.5a1.5 1.5 0 0 0-1.5-1.5m3 6.25a1.5 1.5 0 0 1 3 0v1.5a1.5 1.5 0 0 1-3 0zm6.5 2.5a1.5 1.5 0 0 0-1.5 1.5v1.5a1.5 1.5 0 0 0 3 0V20a1.5 1.5 0 0 0-1.5-1.5m9.5-8.75a1.5 1.5 0 0 0-1.5 1.5v1.5a1.5 1.5 0 0 0 3 0v-1.5a1.5 1.5 0 0 0-1.5-1.5m-6 2.75a1.5 1.5 0 0 1 3 0V17a1.5 1.5 0 0 1-3 0z" clip-rule="evenodd" /></svg>')
    
    self.selected = self.display_devices()
    scripts = self.display_scripts()

    scr.clear()
    
    with ThreadPoolExecutor() as executor:
      future1 = executor.submit(self.run_clist)
      future2 = executor.submit(lambda: self.run_scripts(scripts))

      # Wait for both to finish
      future1.result()
      future2.result()
    
    scr.table("COMPLETED", {
      "device": self.selected.name,
      "scripts": len(scripts),
      "path": f"etc/xadb/uploads/{self.selected.uploads_name}"
    })

    invoke("openApp", {
      "name": "com.kikx.explorer",
        "query": {
          "path": f"home://etc/xadb/uploads/{self.selected.uploads_name}"
        }
      })

    scr.append('<div class="min-h-32"></div>')

    scr.notify(f"XAdb {self.selected.name} completed")


def start():
  XADB().start()

if __name__ == "__main__":
  start()

