import flx.loading.hearts

import ast
import sys
import json
import shlex
import httpx
import asyncio
import uvicorn
import logging
import threading

from pathlib import Path
from datetime import datetime
from pydantic import BaseModel

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketState
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse

from flx import js
from flx.console import Console
from flx.lib.utils import clean
from flx.utils import generate_uuid
from flx.ui import Div, Text, Animate
from flx.console.page import OptionsPage, FormPage
from flx.path import HOME_PATH, joinpath, ensure_dir


class ConsoleScreen(Console):
  def __init__(self) -> None:
    super().__init__()

    self.tbox = Div()
    self.bbox = Div()

    self.status = Div()

    self.tbox.add_class("flex-1 flex flex-col bg-blue-400/20 overflow-y-auto gap-2 py-2")
    self.bbox.add_class("h-[60%] flex flex-col bg-blue-400/30 overflow-hidden")
    self.status.add_class("flex bg-blue-400/30 text-white/60 hidden items-center")

    self.cbox = Div(self.tbox, self.status, self.bbox)
    self.cbox.add_class("flex-1 flex flex-col overflow-hidden")

    # name: function
    self.panels = {}

    # active panel
    self.active_panel = None
    self.fullscreen = False

    self.box.append(Animate(self.cbox))

  def append(self, el, auto_scroll=True) -> None:
    self.tbox.append(el)

    if auto_scroll:
      self.tbox.scroll_to_bottom()
  
  def clear(self) -> None:
    self.tbox.clear()
  
  def toggle_fullscreen(self) -> None:
    self.bbox.toggle_class("hidden")
    self.fullscreen = not self.fullscreen
    self.status.toggle_class("hidden")

    if not self.fullscreen:
      self.tbox.scroll_to_bottom()

  def create_loader(self, label, color="blue"):
    label = clean(label)
    color = clean(color)

    loader = Div().add_class(f"h-2 w-0 rounded-full bg-{color}-400")

    self.append(
      Div(Text(label).add_class("break-all"), loader).add_class(f"p-2 bg-{color}-400/20 w-full flex flex-col gap-1")
    )

    return lambda v: loader.update_style({"width": f"{v}%"})
  
  def log(self, message, color="blue", title=None) -> None:
    message = clean(message)
    color = clean(color)
  
    if title:
      title = f"""
        <div class="w-full bg-{color}-400/20 px-3 py-2 rounded-t truncate">
          {clean(title)}
        </div>
      """

    el = Div(f"""
      {title or ''}
      <div class="flex w-full justify-between items-center px-2">
        <div class="min-w-1 h-full bg-{color}-400 rounded-l"></div>
        <div class="flex-1 text-center bg-{color}-400/20 p-2 break-all">{message}</div>
        <div class="min-w-1 h-full bg-{color}-400 rounded-r"></div>
      </div>
    """).add_class("w-full flex flex-col gap-2")

    self.append(Animate(el))

  def info(self, message) -> None:
    self.log(message, "blue")

  def success(self, message) -> None:
    self.log(message, "green")

  def error(self, message) -> None:
    self.log(message, "red")

  def warning(self, message) -> None:
    self.log(message, "yellow")
  
  def table_rows(self, data: dict) -> str:
    return "".join(
      f"""
      <div class="flex justify-between items-center gap-4 p-2">
        <span class="font-medium break-all">{clean(key)}</span>
        <span class="text-right break-all">{clean(value)}</span>
      </div>
      """
      for key, value in data.items()
    )

  def table(self, title, data: dict, color="blue") -> None:
    color = clean(color)
    rows = self.table_rows(data)

    el = Div(f'<div class="bg-{color}-400/20 p-2 text-center">{clean(title)}</div>', rows).add_class(
      f"w-full bg-{color}-400/20 text-white"
    )

    self.append(Animate(el))

  def get_panel(self, name: str) -> str:
    return self.panels[name]()

  def load_panel(self, name: str):
    self.active_panel = name

    names = [
      f"""<button onclick="sendInput('__panel__{name}')" class="p-2 px-4 rounded font-heading {"bg-blue-400/60" if self.active_panel == name else ""}">{name.upper()}</button>"""
      for name in self.panels.keys()
    ]

    if not names:
      return None

    self.bbox.replace(Div(f"""
      <div class="bg-blue-400/20 p-2 flex items-center justify-center border-y border-blue-400/20">
        { "".join(names) }
      </div>
      
      <div class="flex-1 flex flex-col p-2 overflow-y-auto">{self.get_panel(name)}</div>
    """).add_class("flex-1 flex flex-col overflow-hidden"))

class UI:
  def cmd_button(self, label, cmd, color="blue", disabled: bool = False, classes="") -> str:
    label = clean(label)
    disabled_attr = "disabled" if disabled else ""
    disabled_class = "opacity-50 cursor-not-allowed" if disabled else f"active:bg-{color}-400/80"

    return f"""
      <button
        onclick="sendInput('__cmd__{cmd}')"
        class="p-2 px-4 bg-{color}-400/40 rounded {disabled_class} {classes}"
        {disabled_attr}
      >{label}</button>
    """

  def cmd_toggle_button(self, label, cmd, color="blue", toggled: bool = False, classes="") -> str:
    label = clean(label)
    disabled_class = "opacity-50 cursor-not-allowed" if toggled else ""

    return f"""
      <button
        onclick="
          sendInput('__cmd__{cmd}');
          this.classList.toggle('bg-{color}-400/40');
        "
        class="p-2 px-4 rounded bg-{color}-400/40 {disabled_class} {classes}"
      >{label}</button>
    """

scr = ConsoleScreen()
ui = UI()

# ------- Utils
class ScrHandler(logging.Handler):
  def emit(self, record):
    try:
      msg = self.format(record)
      scr.print(msg)
    except Exception:
      self.handleError(record)

def is_websocket_connected(ws: WebSocket) -> bool:
  if not isinstance(ws, WebSocket):
    return False

  return (
    ws.client_state is WebSocketState.CONNECTED
    and ws.application_state is WebSocketState.CONNECTED
  )

def parse_arg(value: str):
  try:
    return ast.literal_eval(value)
  except (ValueError, SyntaxError):
    return value

# ------- App
class AppSettings(BaseModel):
  alerts: bool = True
  host: str = "127.0.0.1"
  port: int = 8090

class AppConfig:
  def __init__(self) -> None:
    self.uploads_name = self.generate_timestamp()

    self.trix_dir: Path = ensure_dir(HOME_PATH / "etc" / "trix")
    self.upload_dir: Path = ensure_dir(self.trix_dir / "uploads" / self.uploads_name)
    self.pages_dir: Path = ensure_dir(self.trix_dir / "pages")
    self.files_dir: Path = ensure_dir(self.upload_dir / "files")
    
    self.ws_scripts_dir: Path = ensure_dir(self.trix_dir / "scripts")
    self.payloads_dir: Path = ensure_dir(self.trix_dir / "payloads")
  
    self.settings_file_path: Path = self.trix_dir / "settings.json"
    self.logs_file_path: Path = self.upload_dir / "logs.json"

    self.static_dir: Path = ensure_dir(Path(sys.argv[0]).parent / "etc/trix/static")

    self.submits_count: int = 0
    self.ip_dumps_count: int = 0
    self.data_dumps_count: int = 0
  
    self.load()

  @property
  def settings(self) -> AppSettings:
    return self._settings

  def generate_timestamp(self) -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

  def load(self) -> None:
    try:
      with self.settings_file_path.open("r", encoding="utf-8") as f:
        self._settings = AppSettings(**json.load(f))
    except Exception:
      self._settings = AppSettings()
      self.save()

  def save(self) -> None:
    self.settings_file_path.write_text(
      self._settings.model_dump_json(indent=2),
      encoding="utf-8",
    )

  def upload_json(self, filename: str, data: dict) -> None:
    with open(self.upload_dir / filename, "w", encoding="utf-8") as file:
      json.dump(data, file, indent=2)

  def submit(self, data: dict) -> None:
    self.upload_json(f"submit_{self.submits_count}.json", data)
    self.submits_count += 1

  def ip_dump(self, data: dict) -> None:
    self.upload_json(f"ip_{self.ip_dumps_count}.json", data)
    self.ip_dumps_count += 1

  def data_dump(self, data: dict) -> None:
    self.upload_json(f"data_{self.data_dumps_count}.json", data)
    self.data_dumps_count += 1

  def open_path(self) -> None:
    js.invoke("openApp", {
      "name": "com.kikx.explorer",
        "query": {
          "path": f"home://etc/trix/uploads/{self.uploads_name}"
        }
      })

  def get_scripts(self) -> list[str]:
    return [p.stem for p in self.ws_scripts_dir.iterdir() if p.is_file() and p.suffix == ".js"]

  def get_ws_script(self, path: str) -> Path:
    return joinpath(self.ws_scripts_dir, f"{path}.js").read_text()

class Payloads:
  def __init__(self, config: AppConfig) -> None:
    self._config: AppConfig = config

  @property
  def settings(self) -> AppSettings:
    return self._config.settings

  @property
  def payloads_dir(self) -> Path:
    return self._config.payloads_dir
  
  def get(self, path: str, params: dict) -> str:
    return self.compile(joinpath(self.payloads_dir, path).read_text(), params)

  def _compile(self, line: str, params: dict) -> str:
    return line.format_map({
      "host": self.settings.host,
      "port": self.settings.port,
      **params
    })

  def compile(self, code: str, params: dict) -> str:
    lines = []
    
    for line in code.splitlines():
      lines.append(self._compile(line, params))

    return "\n".join(lines)

class Device:
  def __init__(self, ws: WebSocket, device_id: str, meta=None):
    self.uid: str = generate_uuid()
    self.device_id: str = device_id

    self.ws: WebSocket = ws
    self.meta = meta or {}

  @property
  def is_connected(self) -> bool:
    return is_websocket_connected(self.ws)

  async def send_event(self, event: str, payload=None) -> None:
    if not self.is_connected:
      return None

    await self.ws.send_json({
      "event": event, "payload": payload
    })
  
  async def run_code(self, code) -> None:
    if not code:
      return None

    await self.send_event("run-code", code)

  async def close(self) -> None:
    if self.is_connected:
      await self.ws.close()

class WS:
  def __init__(self, config: AppConfig):
    self.config: AppConfig = config
    self._devices: dict[str, Device] = {}
    self.device_id_count: int = 0

    self.selected: Device | None = None

  def is_selected_device(self, device: Device) -> bool:
    return self.selected and self.selected.uid == device.uid

  def get_device_by_uid(self, uid: str) -> Device | None:
    return self._devices.get(uid, None)

  def get_device_by_id(self, device_id: str) -> Device | None:
    return next((d for d in self._devices.values() if d.device_id == device_id), None)

  async def on_connect(self, ws: WebSocket, meta=None) -> Device:
    device = Device(ws, self.device_id_count, meta=meta)
    self._devices[device.uid] = device
    self.device_id_count += 1

    scr.table("DEVICE-CONNECTED", {
      "id": device.device_id,
      "uid": device.uid,

      **(meta or {})
    })

    return device

  async def on_disconnect(self, device: Device) -> None:
    scr.table("DEVICE-DISCONNECTED", {
      "id": device.device_id,
      "uid": device.uid,
    }, color="red")

  async def on_data(self, device: Device, data: dict) -> None:
    event, payload = data.values()
    if event == "log":
      message, color = payload.values()
      scr.log(message, title=f"Device({device.device_id}) {device.uid}", color=color)

    elif event == "table":
      scr.table(f"Device({device.device_id}) {device.uid}", payload)

  async def close_device(self, uid: str) -> None:
    device = self._devices.pop(uid)
    if not device:
      scr.error(f"Device: {uid} not found")
      return None
    
    if self.is_selected_device(device):
      self.selected = None

    await device.close()

  def select_device(self, uid: str) -> None:
    self.selected = self.get_device_by_uid(uid)

  async def run_code(self, code: str, device_id: int | None = None) -> None:
    device =  self.get_device_by_id(device_id) if device_id else self.selected
    if device is None:
      return None

    await device.run_code(code)

class App:
  def __init__(self):
    self.ui: UI = UI()

    self.config: AppConfig = AppConfig()
    self.router: FastAPI = FastAPI()

    self.payloads: Payloads = Payloads(self.config)
    self.ws: WS = WS(self.config)

    # Panels
    scr.panels = {
      "server": self.server_panel,
      "display": self.display_panel,
      "ws": self.ws_panel,
      "settings": self.settings_panel
    }

    self.status_buttons = [
      {
        "label": '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24"><path d="M0 0h24v24H0z" fill="none" /><g fill="currentColor" fill-rule="evenodd" clip-rule="evenodd"><path d="M8.60714 22C8.60714 22.4142 8.27136 22.75 7.85714 22.75H2C1.58579 22.75 1.25 22.4142 1.25 22V16.1429C1.25 15.7286 1.58579 15.3929 2 15.3929C2.41421 15.3929 2.75 15.7286 2.75 16.1429V20.1893L8.46967 14.4697C8.76256 14.1768 9.23744 14.1768 9.53033 14.4697C9.82322 14.7626 9.82322 15.2374 9.53033 15.5303L3.81066 21.25H7.85714C8.27136 21.25 8.60714 21.5858 8.60714 22Z" opacity=".5" /><path d="M15.3929 2C15.3929 1.58579 15.7286 1.25 16.1429 1.25H22C22.4142 1.25 22.75 1.58579 22.75 2V7.85714C22.75 8.27136 22.4142 8.60714 22 8.60714C21.5858 8.60714 21.25 8.27136 21.25 7.85714V3.81066L15.5303 9.53033C15.2374 9.82322 14.7626 9.82322 14.4697 9.53033C14.1768 9.23744 14.1768 8.76256 14.4697 8.46967L20.1893 2.75H16.1429C15.7286 2.75 15.3929 2.41421 15.3929 2Z" /></g></svg>',
        "command": "__cmd__toggle_fullscreen"
      },
      {
        "label": '<svg xmlns="http://www.w3.org/2000/svg" width="23" height="22" viewBox="0 0 24 24"><path d="M0 0h24v24H0z" fill="none" /><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="1.5" d="M3 12L3 18.9671C3 21.2763 5.53435 22.736 7.59662 21.6145L10.7996 19.8727M3 8L3 5.0329C3 2.72368 5.53435 1.26402 7.59661 2.38548L20.4086 9.35258C22.5305 10.5065 22.5305 13.4935 20.4086 14.6474L14.0026 18.131" /></svg>',
        "command": "__cmd__start_server",
        "condition": lambda: not self.is_server_running
      },
      {
        "label": '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24"><path d="M0 0h24v24H0z" fill="none" /><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="1.5" d="M22 12C22 16.714 22 19.0711 20.5355 20.5355C19.0711 22 16.714 22 12 22C7.28595 22 4.92893 22 3.46447 20.5355C2 19.0711 2 16.714 2 12C2 7.28595 2 4.92893 3.46447 3.46447C4.92893 2 7.28595 2 12 2C16.714 2 19.0711 2 20.5355 3.46447C21.5093 4.43821 21.8356 5.80655 21.9449 8" /></svg>',
        "command": "__cmd__stop_server",
        "condition": lambda: self.is_server_running
      },
      {
        "label": '<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 16 16"><path d="M0 0h16v16H0z" fill="none" /><path fill="none" stroke="currentColor" stroke-linejoin="round" d="m7 6l4 4m0-4l-4 4M5 3.5h9.5v9H5L1.5 8z" /></svg>',
        "command": "__cmd__clear_screen",
      }
    ]

    self.server_thread = None

    self.code_box_uid: str = generate_uuid()

  @property
  def is_server_running(self) -> bool:
    return self.server_thread and self.server_thread.is_alive()

  @property
  def settings(self) -> AppSettings:
    return self.config.settings

  def update_status(self) -> None:
    if not scr.fullscreen:
      return None

    buttons = []

    for button in self.status_buttons:
      label = button["label"]
      command = button["command"]
      if "condition" in button and not button["condition"]():
        continue

      buttons.append(f"""
        <button class="p-2 flex items-center justify-center active:bg-blue-400/60" onclick="sendInput('{command}')">{label}</button>
      """)
    
    scr.status.replace("".join(buttons))

  def notify(self, message, typ='info') -> None:
    if not self.settings.alerts:
      return None

    scr.notify('Trix-' + str(message), type=typ)

  async def upload_file(self, file: UploadFile) -> None:
    name = file.filename

    filename = f"{generate_uuid()}_{name}"
    filepath = joinpath(self.config.files_dir, filename)

    loader = scr.create_loader(name)

    total = file.size or 0
    uploaded = 0

    with open(filepath, "wb") as f:
      while chunk := await file.read(1024 * 1024):
        f.write(chunk)

        uploaded += len(chunk)

        if total:
          progress = int((uploaded / total) * 100)
          loader(progress)

    self.notify(f"File uploaded {name}")

  def submit(self, data: dict) -> None:
    scr.table("SUBMIT", data)
    self.config.submit(data)

    self.notify("Got submit")

  def ip_dump(self, data: dict) -> None:
    scr.table("IP-DUMP", data, color="pink")
    self.config.ip_dump(data)

    self.notify("Got ip dump")

  def dump_data(self, data: dict) -> None:
    scr.table("SUBMIT-DATA", data, color="purple")
    self.config.data_dump(data)

    self.notify("Got submit-data")
  
  def get_payload(self, path: str, params: dict) -> str:
    return self.payloads.get(path, params)

  async def on_ws_connect(self, ws: WebSocket, meta=None) -> Device:
    device = await self.ws.on_connect(ws, meta)
    self.notify(f"Device {device.uid} connected")

    if not self.ws.selected:
      self.refresh()

    return device

  async def on_ws_disconnect(self, device: Device) -> None:
    await self.ws.on_disconnect(device)
    
    if self.ws.is_selected_device(device):
      self.ws.selected = None
      self.refresh()

  async def on_ws_data(self, device: Device, data) -> None:
    await self.ws.on_data(device, data)

  # ------- Panels
  def bind_btn(self, cmd) -> str:
    return f'''onclick="sendInput('__cmd__{cmd}')"'''

  def server_panel(self) -> str:
    rows = scr.table_rows({
      "Host": self.settings.host,
      "Port": self.settings.port,
      "Status": "Active" if self.is_server_running else "Stopped"
    })
    
    return f"""
      <div class="flex flex-col gap-2">
        <div class="grid grid-cols-2 gap-2 overflow-y-auto">
          {ui.cmd_button('START', 'start_server', 'green', disabled=self.is_server_running)}
          {ui.cmd_button('STOP', 'stop_server', 'red', disabled=not self.is_server_running)}
          {ui.cmd_button('COPY URL', 'copy_url', 'pink', classes="col-span-2") if self.is_server_running else ''}
        </div>

        <div class="rounded bg-blue-400/20">{rows}</div>
      </div>
    """

  # ------- 
  def device_ws_panel(self) -> str:
    scripts = []

    for script in self.config.get_scripts():
      scripts.append(f"""
        <div class="rounded flex items-center border border-white/20 text-white/80 overflow-hidden">
          <button onclick="sendInput('__ws-script__{script}')" class="flex-1 p-2 active:bg-white/10 disabled:bg-gray-400/20">{script}</button>
        </div>
      """)

    return f"""
      <div class="flex justify-between items-center p-1 mb-2 rounded border border-white/10">
        <div class="flex items-center gap-1">
          <button onclick="sendInput('__cmd__ws_unselect_device')"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="M0 0h24v24H0z" fill="none" /><g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"><path d="M20 12H4" opacity=".5" /><path d="M10 6L4 12L10 18" /></g></svg></button>
          <p>{self.ws.selected.device_id}</p>
        </div>
        <div class="opacity-60">Scripts</div>
      </div>
      <div class="flex flex-col gap-2">
        {"".join(scripts)}
      </div>
    """

  def ws_panel(self) -> str:
    if self.ws.selected:
      return self.device_ws_panel()

    devices = []
    
    for device in self.ws._devices.values():
      devices.append(f"""
        <div class="rounded flex items-center border border-white/20 text-white/80 overflow-hidden">
          <div class="bg-blue-400/60 px-4 p-2">{device.device_id}</div>
          <button {'disabled' if not device.is_connected else ''} onclick="sendInput('__cmd__select_ws_device:{device.uid}')" class="flex-1 p-2 active:bg-white/10 disabled:bg-gray-400/20">{device.uid}</button>
          <button onclick="sendInput('__cmd__close_ws_device:{device.uid}')" class="bg-pink-400/60 p-2 px-3"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><path d="M0 0h24v24H0z" fill="none" /><path fill="currentColor" d="m12 13.4l-4.9 4.9q-.275.275-.7.275t-.7-.275t-.275-.7t.275-.7l4.9-4.9l-4.9-4.9q-.275-.275-.275-.7t.275-.7t.7-.275t.7.275l4.9 4.9l4.9-4.9q.275-.275.7-.275t.7.275t.275.7t-.275.7L13.4 12l4.9 4.9q.275.275.275.7t-.275.7t-.7.275t-.7-.275z" /></svg></button>
        </div>
      """)

    return f"""
      <div class="flex flex-col gap-2">
        {"".join(devices)}
      </div>
    """

  def display_panel(self) -> str:
    return f"""
      <div class="grid grid-cols-2 gap-2 overflow-y-auto">
        {ui.cmd_button('Clear', 'clear_screen', 'orange')}
        {ui.cmd_button('Settings', 'display_settings', 'orange')}
        {ui.cmd_button('Status', 'server_status', 'pink')}
        {ui.cmd_button('Fullscreen', 'toggle_fullscreen', 'pink')}
      </div>
    """

  def settings_panel(self) -> str:
    host = self.settings.host
    port = self.settings.port

    return f"""
      <div class="flex flex-col gap-2">
        <div class="grid grid-cols-2 gap-2 overflow-y-auto">
          {ui.cmd_toggle_button('Alerts', 'toggle_alerts', 'blue', toggled = not self.config.settings.alerts)}
          {ui.cmd_toggle_button('Path', 'open_path', 'green')}
        </div>
        
        <div class="flex flex-col gap-2">
          <input type="text" onchange="sendInput(`__cmd__set_setting:host:${{this.value}}`)" class="w-full rounded bg-transparent p-2 border border-white/20 focus:outline-none" placeholder="Host ex:(127.0.0.1)" value="{host}" />
          <input type="number" onchange="sendInput(`__cmd__set_setting:port:${{this.value}}`)" class="w-full rounded bg-transparent p-2 border border-white/20 focus:outline-none" placeholder="Port ex:(8080)" value="{port}" />
        </div>
      </div>
    """

  # ------- Commands
  def run_async_ws_func(self, func, *args, done=None) -> None:
    func = getattr(self.ws, func)
    if not func:
      return None

    if not self.server_loop:
      scr.error("Server event loop not running")
      return None

    future = asyncio.run_coroutine_threadsafe(
      func(*args),
      self.server_loop,
    )

    # handle exceptions from the coroutine
    def done_callback(f):
      try:
        f.result()
        if done:
          done()
      except Exception:
        pass

    future.add_done_callback(done_callback)

  def _compile_code(self, code: str) -> str | None:
    js_code = []
    option_lines = []

    for line in code.splitlines():
      line = line.strip()

      if line.startswith("//!"):
        parts = shlex.split(line[3:].strip())

        function_name = parts[0]
        args = [parse_arg(arg) for arg in parts[1:]]

        option_lines.append((function_name, args))
      else:
        js_code.append(line)

    form = FormPage(title="Script options")

    for function_name, args in option_lines:
      getattr(form, f"add_{function_name}")(*args)

    options = form.display(scr.bbox)

    if options is None:
      return None

    return f"""
    const op = {json.dumps(options)}
    {code}
    """

  def run_ws_script(self, script: str) -> None:
    try:
      code = self._compile_code(self.config.get_ws_script(script))
      if code:
        self.run_async_ws_func("run_code", code)
    except Exception as e:
      scr.error(f"Error running script '{script}': {e}")
    finally:
      self.refresh()

  def cmd_ws_unselect_device(self) -> None:
    self.ws.selected = None

  def cmd_close_ws_device(self, uid: str) -> None:
    self.run_async_ws_func("close_device", uid, done=self.refresh)

  def cmd_set_setting(self, arg: str) -> None:
    name, value = arg.split(":", 1)
    
    if name == "port":
      value = int(value)

    setattr(self.settings, name, value)

    self.config.save()

  def _run_server(self) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    self.server_loop = loop

    loop.run_until_complete(self.server.serve())
    loop.close()

  def cmd_start_server(self) -> None:
    """Start server"""
    if self.server_thread and self.server_thread.is_alive():
      scr.warning("Server already running")
      return None

    self.server_config = uvicorn.Config(
      self.router,
      host=self.settings.host,
      port=self.settings.port,
      log_config=None,
      access_log=False,
    )

    self.server = uvicorn.Server(self.server_config)
    self.server.should_exit = False
    self.server_loop = None

    self.server_thread = threading.Thread(
      target=self._run_server,
      daemon=True,
    )

    self.server_thread.start()

    scr.success("Server started")

  def cmd_stop_server(self) -> None:
    """Stop server"""
    self.ws.selected = None

    if not self.is_server_running:
      scr.warning("Server not running")
      return None

    if self.server:
      self.server.should_exit = True

    if self.server_thread:
      self.server_thread.join(timeout=2)
      self.server_thread = None

    scr.error("Server stopped")

  def cmd_server_status(self) -> None:
    """Server status"""
    scr.table("SERVER", {
      "Host": self.settings.host,
      "Port": self.settings.port,
      "Status": "Active" if self.is_server_running else "Stopped"
    }, "green" if self.is_server_running else "gray")

  def cmd_clear_screen(self) -> None:
    """Clear screen"""
    scr.clear()

  def cmd_toggle_fullscreen(self) -> None:
    scr.toggle_fullscreen()
  
  def cmd_copy_url(self) -> None:
    js.copy_text(f"http://{self.settings.host}:{self.settings.port}")

  def cmd_display_settings(self) -> None:
    """Display settings"""
    scr.table("SETTINGS", self.settings.model_dump(), color="orange")

  def cmd_toggle_alerts(self) -> None:
    self.config.settings.alerts = not self.config.settings.alerts

    self.config.save()

  def cmd_select_ws_device(self, cmd) -> None:
    self.ws.select_device(cmd)

  def cmd_open_path(self) -> None:
    self.config.open_path()

  def on_cmd(self, cmd) -> None:
    splitted = cmd.split(":", 1)

    func = getattr(self, f"cmd_{splitted[0]}", None)
    if func is None:
      return None

    try:
      if len(splitted) > 1:
        func(splitted[1])
      else:
        func()
    except Exception as e:
      scr.error(e)

  # ------- Start
  def refresh(self) -> None:
    # refresh panel
    scr.load_panel(scr.active_panel)
    self.update_status()

  def cmdloop(self) -> None:
    scr.load_panel("server")

    while True:
      input_text = input().strip()

      if input_text in {"q", "exit", "quit"}:
        self.server.should_exit = True
        self.config.save()
        break
      # Panel change
      if input_text.startswith("__panel__"):
        scr.load_panel(input_text[9:])
        self.refresh()
      # Cmd
      elif input_text.startswith("__cmd__"):
        self.on_cmd(input_text[7:])
        self.refresh()
      elif input_text.startswith("__ws-script__"):
        self.run_ws_script(input_text[13:])

  def start(self) -> None:
    logging.getLogger("uvicorn").disabled = True
    # handler = ScrHandler()
    # handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    
    # for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    #   logger = logging.getLogger(logger_name)
    #   logger.handlers.clear()
    #   logger.addHandler(handler)
    #   logger.setLevel(logging)
    #   logger.propagate = False

    self.cmdloop()

# ------- Routes

app = App()

@app.router.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
  scr.error(
    f"Unhandled exception: "
    f"{request.method} {request.url.path} - "
    f"{type(exc).__name__}: {exc}"
  )
  return JSONResponse(
    status_code=500,
    content={"detail": "Internal server error"},
  )

app.router.mount("/static", StaticFiles(directory=str(app.config.static_dir)), name="static")

@app.router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
  uploaded_files = []
  
  for file in files:
    try:
      await app.upload_file(file)
      uploaded_files.append(file.filename)
    except Exception as e:
      scr.error(f"File {file.filename} failed: {e}")

  return {
    "success": True,
    "filenames": uploaded_files
  }

@app.router.get("/submit")
def submit(request: Request):
  try:
    params = dict(request.query_params)
    app.submit(params)

    return {"res": "ok"}
  except Exception as e:
    scr.error(f"Submit-get failed: {e}")

@app.router.post("/submit")
async def submit_data(request: Request):
  try:
    content_type = request.headers.get("content-type", "").lower()

    if content_type.startswith("application/json"):
      data = await request.json()

    elif (
      content_type.startswith("multipart/form-data")
      or content_type.startswith("application/x-www-form-urlencoded")
    ):
      form = await request.form()
      data = dict(form)
    else:
      raise HTTPException(
        status_code=415,
        detail="Content-Type must be application/json or form data"
      )
    
    app.dump_data(data)

    return {"res": "ok"}
  except Exception as e:
    scr.error(f"Submit-post failed: {e}")

@app.router.get("/ip-dump")
async def ip_dump(request: Request, ip: str | None = None):
  try:
    client_ip = ip or request.client.host
  
    async with httpx.AsyncClient() as client:
      response = await client.get(
        f"http://ip-api.com/json/{client_ip}"
      )

    app.ip_dump(response.json())

    return {"res": "ok"}
  except Exception as e:
    scr.error(f"IP-Dump failed: {e}")

@app.router.get("/p/{path:path}", response_class=PlainTextResponse)
async def get_payload(path: str, request: Request):
  try:
    params = dict(request.query_params)
    return app.get_payload(path, params)
  except Exception:
    raise HTTPException(500, "Failed to process request")

@app.router.get("/{path:path}")
async def page(path: str = ""):
  if len(path.strip()) <= 0:
    path = "index.html"
  
  fpath = joinpath(app.config.pages_dir, path)

  if not fpath.is_file():
    raise HTTPException(404, "File not found")

  return FileResponse(fpath)

@app.router.websocket("/device")
async def websocket_connection(websocket: WebSocket):
  await websocket.accept()

  meta = dict(websocket.query_params)

  try:
    device = await app.on_ws_connect(ws=websocket, meta=meta)
  except Exception as e:
    scr.error(f"Error device connect: {e}")

    await websocket.close()
    return None

  while True:
    try:
      data = await websocket.receive_json()

      try:
        await app.on_ws_data(device, data)
      except Exception as e:
        scr.error(e)
    except WebSocketDisconnect:
      await app.on_ws_disconnect(device)
      break
    except RuntimeError:
      await app.on_ws_disconnect(device)
      break
    except Exception:
      await app.on_ws_disconnect(device)
      break

# ------- Main
def start():
  app.start()


if __name__ == "__main__":
  start()

