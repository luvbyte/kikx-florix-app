import flx.loading.hearts

import os
import shutil

from flx import panel
from flx.console import Console
from flx.console.page import OptionsPage
from flx.os import get_package_manager, is_root
from flx.lib.process import PTYProcess



console = Console()


COMMANDS = {
  "apt": {
    "install": lambda *p: ["apt", "install", "-y", *p],
    "remove": lambda *p: ["apt", "remove", "-y", *p],
    "purge": lambda *p: ["apt", "purge", "-y", *p],
    "search": lambda *p: ["apt", "search", *p],
    "update": lambda: ["apt", "update"],
    "upgrade": lambda: ["apt", "upgrade", "-y"],
    "list": lambda: ["apt", "list", "--installed"],
  },

  "dnf": {
    "install": lambda *p: ["dnf", "install", "-y", *p],
    "remove": lambda *p: ["dnf", "remove", "-y", *p],
    "purge": lambda *p: ["dnf", "remove", "-y", *p],
    "search": lambda *p: ["dnf", "search", *p],
    "update": lambda: ["dnf", "makecache"],
    "upgrade": lambda: ["dnf", "upgrade", "-y"],
    "list": lambda: ["dnf", "list", "installed"],
  },

  "pacman": {
    "install": lambda *p: ["pacman", "-S", "--noconfirm", *p],
    "remove": lambda *p: ["pacman", "-R", "--noconfirm", *p],
    "purge": lambda *p: ["pacman", "-Rns", "--noconfirm", *p],
    "search": lambda *p: ["pacman", "-Ss", *p],
    "update": lambda: ["pacman", "-Sy"],
    "upgrade": lambda: ["pacman", "-Su", "--noconfirm"],
    "list": lambda: ["pacman", "-Q"],
  },

  "zypper": {
    "install": lambda *p: [
      "zypper",
      "--non-interactive",
      "install",
      *p,
    ],
    "remove": lambda *p: [
      "zypper",
      "--non-interactive",
      "remove",
      *p,
    ],
    "purge": lambda *p: [
      "zypper",
      "--non-interactive",
      "remove",
      *p,
    ],
    "search": lambda *p: ["zypper", "search", *p],
    "update": lambda: ["zypper", "refresh"],
    "upgrade": lambda: [
      "zypper",
      "--non-interactive",
      "update",
    ],
    "list": lambda: [
      "zypper",
      "packages",
      "--installed-only",
    ],
  },

  "apk": {
    "install": lambda *p: ["apk", "add", *p],
    "remove": lambda *p: ["apk", "del", *p],
    "purge": lambda *p: ["apk", "del", *p],
    "search": lambda *p: ["apk", "search", *p],
    "update": lambda: ["apk", "update"],
    "upgrade": lambda: ["apk", "upgrade"],
    "list": lambda: ["apk", "info"],
  },

  "xbps": {
    "install": lambda *p: ["xbps-install", "-y", *p],
    "remove": lambda *p: ["xbps-remove", "-y", *p],
    "purge": lambda *p: ["xbps-remove", "-y", *p],
    "search": lambda *p: ["xbps-query", "-Rs", *p],
    "update": lambda: ["xbps-install", "-S"],
    "upgrade": lambda: ["xbps-install", "-Su"],
    "list": lambda: ["xbps-query", "-l"],
  },

  "emerge": {
    "install": lambda *p: ["emerge", *p],
    "remove": lambda *p: ["emerge", "--unmerge", *p],
    "purge": lambda *p: ["emerge", "--unmerge", *p],
    "search": lambda *p: ["emerge", "--search", *p],
    "update": lambda: ["emerge", "--sync"],
    "upgrade": lambda: [
      "emerge",
      "--update",
      "--deep",
      "--newuse",
      "@world",
    ],
    "list": lambda: ["qlist", "-I"],
  },

  "nix": {
    "install": lambda *p: [
      "nix-env",
      "-iA",
      *[f"nixpkgs.{package}" for package in p],
    ],
    "remove": lambda *p: ["nix-env", "-e", *p],
    "purge": lambda *p: ["nix-env", "-e", *p],
    "search": lambda *p: ["nix-env", "-qaP", *p],
    "update": lambda: ["nix-channel", "--update"],
    "upgrade": lambda: ["nix-env", "-u"],
    "list": lambda: ["nix-env", "-q"],
  },

  "guix": {
    "install": lambda *p: ["guix", "install", *p],
    "remove": lambda *p: ["guix", "remove", *p],
    "purge": lambda *p: ["guix", "remove", *p],
    "search": lambda *p: ["guix", "search", *p],
    "update": lambda: ["guix", "pull"],
    "upgrade": lambda: ["guix", "upgrade"],
    "list": lambda: ["guix", "package", "--list-installed"],
  },
}


ROOT_ACTIONS = {
  "install",
  "remove",
  "purge",
  "update",
  "upgrade",
}


def requires_root(action):
  manager = get_package_manager()

  # Nix and Guix can operate in user profiles
  if manager in {"nix", "guix"}:
    return False

  return action in ROOT_ACTIONS


def get_command(action, packages=None):
  manager = get_package_manager()

  if not manager:
    raise RuntimeError(
      "Unsupported or unavailable package manager"
    )

  manager_commands = COMMANDS.get(manager)

  if not manager_commands:
    raise RuntimeError(
      f"Unsupported package manager: {manager}"
    )

  command = manager_commands.get(action)

  if not command:
    raise RuntimeError(
      f"'{action}' is not supported by {manager}"
    )

  if packages:
    return command(*packages)

  return command()


def run_command(command):
  panel.clear(force=True)
  PTYProcess(command, print).run()


def package_action(action, requires_package=True):
  try:
    if requires_root(action) and not is_root():
      console.alert(
        f"'{action.capitalize()}' requires root permission.",
        "error",
      )
      return

    packages = None

    if requires_package:
      package_input = console.input(
        "Enter package names"
      ).strip()

      if not package_input:
        return

      # Support:
      #   git curl wget
      #   git, curl, wget
      #   git   curl   wget
      packages = package_input.replace(",", " ").split()

    run_command(get_command(action, packages))

  except RuntimeError as error:
    console.alert(str(error), "error")


def start():
  options = [
    "Install",
    "Remove",
    "Purge",
    "Search",
    "Update",
    "Upgrade",
    "Installed",
    "Exit",
  ]

  option = OptionsPage(options).display(console)

  if option is None:
    return

  actions = {
    1: lambda: package_action("install"),
    2: lambda: package_action("remove"),
    3: lambda: package_action("purge"),
    4: lambda: package_action("search"),
    5: lambda: package_action("update", False),
    6: lambda: package_action("upgrade", False),
    7: lambda: package_action("list", False),
    8: lambda: None,
  }

  action = actions.get(option.value)

  if action:
    action()