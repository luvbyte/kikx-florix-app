from uuid import uuid4
from packaging.version import Version, InvalidVersion
from packaging.specifiers import SpecifierSet, InvalidSpecifier

from flx.__init__ import __version__



def generate_uuid() -> str:
  return uuid4().hex


def _convert_requirement(requirement: str) -> str:
  requirement = requirement.strip()

  # caret (^)
  if requirement.startswith("^"):
    v = Version(requirement[1:])

    if v.major > 0:
      upper = f"{v.major + 1}.0.0"
    elif v.minor > 0:
      upper = f"0.{v.minor + 1}.0"
    else:
      upper = f"0.0.{v.micro + 1}"

    return f">={v},<{upper}"

  # tilde (~)
  if requirement.startswith("~") and not requirement.startswith("~="):
    v = Version(requirement[1:])
    upper = f"{v.major}.{v.minor + 1}.0"
    return f">={v},<{upper}"

  # Bare version -> compatible release
  if not any(requirement.startswith(op) for op in ("<", ">", "!", "=", "~")):
    return f"~={requirement}"

  return requirement


def is_version_match(current_version: str, requirement: str) -> bool:
  try:
    version = Version(current_version)
    spec = SpecifierSet(_convert_requirement(requirement))
    return version in spec
  except (InvalidVersion, InvalidSpecifier):
    return False


def check_version(version: str) -> bool:
  return is_version_match(__version__, version)