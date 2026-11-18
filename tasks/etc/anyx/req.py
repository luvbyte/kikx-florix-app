import flx.loading.hearts

import json
import requests

from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict
from flx.console import Console


console = Console()


class RConfig(BaseModel):
  model_config = ConfigDict(extra="forbid")

  url: str
  method: Literal["GET", "POST"] = "GET"
  headers: dict[str, str] = Field(default_factory=dict)
  params: dict = Field(default_factory=dict)
  data: dict | str | None = None
  json: dict | list | None = None
  timeout: float = Field(default=15.0, gt=0)
  verify: bool = True


class Request:
  def __init__(self, config: dict | RConfig):
    self.config = (
      config
      if isinstance(config, RConfig)
      else RConfig.model_validate(config)
    )

    self.response = None

  def run(self):
    config = self.config

    try:
      with requests.Session() as session:
        self.response = session.request(
          method=config.method,
          url=config.url,
          headers=config.headers,
          params=config.params,
          data=config.data,
          json=config.json,
          timeout=config.timeout,
          verify=config.verify,
        )

      return self.response

    except requests.RequestException as exc:
      console.print(f"Request failed: {exc}")
      return None

  def json(self):
    if self.response is None:
      return None

    try:
      return self.response.json()
    except requests.exceptions.JSONDecodeError:
      return None

  def text(self):
    if self.response is None:
      return None

    return self.response.text

  def status_code(self):
    if self.response is None:
      return None

    return self.response.status_code

  def raise_for_status(self):
    if self.response is not None:
      self.response.raise_for_status()


def start(path, args=None):
  path = Path(path)

  try:
    with path.open("r", encoding="utf-8") as file:
      config = json.load(file)

    request = Request(config)
    response = request.run()

    if response is None:
      return None

    console.print(f"Status: {response.status_code}")

    return response

  except FileNotFoundError:
    console.print(f"Config file not found: {path}")

  except json.JSONDecodeError as exc:
    console.print(f"Invalid JSON configuration: {exc}")

  except Exception as exc:
    console.print(f"Error: {exc}")

  return None