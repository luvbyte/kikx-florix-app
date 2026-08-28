from uuid import uuid4


def generate_uuid() -> str:
  return uuid4().hex
