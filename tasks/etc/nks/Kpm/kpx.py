import flx.loading.hearts

import re
import os
import json
import shutil

from uuid import uuid4
from pathlib import Path

from flx import js
from flx.path import HOME_PATH, ensure_dir
from flx.console import Console
from flx.console.page import FormPage, OptionsPage


console = Console()

BASE = ensure_dir(HOME_PATH / "etc/florix/kpx")


class CreateWebApp:
  def __init__(self):
    pass

  def start(self):
    pass


class LocalBuild:
  def __init__(self):
    self.dest = ensure_dir(BASE / "localBuilds")
    self.kikxpath = "home://etc/florix/kpx/localBuilds"

    self.options = (
      FormPage("Build kikx app package")
      .add_path("manifest", "App manifest (app.json / app.debug.json)", type="file", required=True)
      .add_checkbox("open", "Open in installer")
    ).display(console)

    if not self.options:
      exit()

    self.manifest_path = Path(self.options["manifest"]).resolve()
    self.src = self.manifest_path.parent
    self.open = self.options["open"]

    # Loader 
    self.loader = console.loader()

  # Check manifest
  def analyze(self):
    pass

  def load_manifest(self) -> dict:
    if not self.manifest_path.is_file():
      raise Exception("App manifest not found")

    with open(self.manifest_path, "r") as f:
      return json.load(f)

  def start(self):
    manifest = self.load_manifest()
  
    raw_name = manifest["name"]

    name = re.sub(r"[^a-zA-Z0-9_-]+", "_", raw_name).strip("_-")
    name = name or "unnamed_app"
    include = manifest["include"]

    # Ensure destination exists
    self.dest.mkdir(parents=True, exist_ok=True)
  
    # Remove any extension from the app name
    name = Path(name).stem

    temp = self.dest / uuid4().hex
    app_dir = temp / "app"
  
    zip_path = self.dest / f"{name}.zip"
    kikx_path = self.dest / f"{name}.kikx"

    try:
      app_dir.mkdir(parents=True, exist_ok=True)
  
      # Copy manifest into the top-level app folder
      shutil.copy2(self.manifest_path, app_dir / "app.json")
  
      # Copy included files and directories
      for path in include:
        relative_path = Path(path)
  
        # Prevent absolute paths and paths escaping app/
        if relative_path.is_absolute() or ".." in relative_path.parts:
          raise ValueError(f"Invalid include path: {path}")
  
        src = self.src / relative_path
        dst = app_dir / relative_path
  
        if not src.exists():
          raise FileNotFoundError(f"Include path does not exist: {src}")
  
        if src.is_dir():
          shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.is_file():
          dst.parent.mkdir(parents=True, exist_ok=True)
          shutil.copy2(src, dst)
  
      # Create ZIP containing only the app/ folder
      shutil.make_archive(str(zip_path.with_suffix("")), "zip", root_dir=temp)
  
      # Verify the ZIP was actually created
      if not zip_path.is_file():
        raise FileNotFoundError(f"ZIP archive was not created: {zip_path}")
  
      # Replace an existing output archive if necessary
      zip_path.replace(kikx_path)

      # Open the generated package
      if self.open:
        js.open_app("com.kikx.appstore", uri=f"{self.kikxpath}/{kikx_path.name}")
      else:
         js.open_app("com.kikx.explorer", path=self.kikxpath)

    finally:
      shutil.rmtree(temp, ignore_errors=True)
  
      # Remove an incomplete ZIP if packaging failed
      if zip_path.exists():
        zip_path.unlink()


def start():
  bindings = {
    "Create Web App": lambda: CreateWebApp().start(),
    "Local Build": lambda: LocalBuild().start(),
    "Exit": lambda: True
  }

  while True:
    option = OptionsPage(bindings.keys(), justify="center").display(console)
    
    do_break = (list(bindings.values())[option.value - 1])()

    if do_break:
      break
