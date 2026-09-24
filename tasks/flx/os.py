# os

import os
import shutil
import platform


# Check if user root
def is_root():
  return os.geteuid() == 0

# Get package manager
def get_package_manager():
  if not os.path.exists("/etc/os-release"):
    return None

  info = {}

  with open("/etc/os-release") as f:
    for line in f:
      if "=" in line:
        key, value = line.rstrip().split("=", 1)
        info[key] = value.strip('"')

  distro_id = info.get("ID", "").lower()

  package_managers = {
    # Debian-based
    "debian": "apt",
    "ubuntu": "apt",
    "linuxmint": "apt",
    "pop": "apt",
    "elementary": "apt",
    "kali": "apt",
  
    # Red Hat-based
    "fedora": "dnf",
    "rhel": "dnf",
    "rocky": "dnf",
    "almalinux": "dnf",
    "centos": "dnf",
  
    # Arch-based
    "arch": "pacman",
    "manjaro": "pacman",
    "endeavouros": "pacman",
  
    # SUSE
    "opensuse": "zypper",
    "opensuse-leap": "zypper",
    "opensuse-tumbleweed": "zypper",
    "sles": "zypper",
  
    # Alpine
    "alpine": "apk",
  
    # Void
    "void": "xbps-install",
  
    # Gentoo
    "gentoo": "emerge",
  
    # Nix
    "nixos": "nix",
  
    # Guix
    "guix": "guix",
  }

  return package_managers.get(distro_id)

# Installed programs list
def get_programs_list(extra=False):
  programs = []

  for directory in os.environ.get("PATH", "").split(os.pathsep):
    if not os.path.isdir(directory):
      continue

    try:
      for name in os.listdir(directory):
        path = os.path.join(directory, name)

        if os.path.isfile(path) and os.access(path, os.X_OK):
          programs.append({
            "path": os.path.abspath(path),
            "name": name,
          } if extra else name)
    except PermissionError:
      continue

  return programs

# Get prog path
def which(prog: str):
  return shutil.which(prog)

# Check if program installed
def is_installed(name) -> bool:
  return which(name) is not None
