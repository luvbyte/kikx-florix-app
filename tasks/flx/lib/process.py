import os
import sys
import pty
import shlex
import subprocess



class PTYProcess:
  def __init__(self, cmd, callback=None):
    self.cmd = cmd
    self.callback = callback
    self.stdout = []

  @property
  def args(self):
    return shlex.split(self.cmd) if isinstance(self.cmd, str) else self.cmd
  
  @property
  def output(self) -> str:
    return "".join(self.stdout)
  
  @property
  def returncode(self) -> int | None:
    return self.process.returncode

  @property
  def is_ok(self) -> bool:
    return self.returncode == 0

  def on_output(self, func):
    self.callback = func
    return func

  def run(self):
    master, slave = pty.openpty()

    try:
      self.process = subprocess.Popen(
        self.args,
        stdin=slave,
        stdout=slave,
        stderr=slave,
        close_fds=True,
      )

      os.close(slave)

      while self.process.poll() is None:
        try:
          data = os.read(master, 4096)

          if not data:
            continue

          output = data.decode(errors="replace")
          self.stdout.append(output)

          if self.callback:
            self.callback(output)

        except OSError:
          break

      self.process.wait()
      return self.returncode

    finally:
      for fd in (master, slave):
        try:
          os.close(fd)
        except OSError:
          pass


class CmdBuilder:
  def __init__(self, command: str):
    self.args = [command]

  def add(self, *args) -> "CmdBuilder":
    self.args.extend(str(arg) for arg in args)
    return self

  def flag(self, flag: str, condition: bool = True) -> "CmdBuilder":
    if condition:
      self.args.append(flag)
    return self

  def option(self, flag: str, value, condition: bool = True) -> "CmdBuilder":
    if condition and value is not None and str(value) != "":
      self.args.extend([flag, str(value)])
    return self

  def choice(self, value, choices: dict) -> "CmdBuilder":
    if value in choices:
      self.args.append(choices[value])
    return self

  def extend(self, args, condition: bool = True) -> "CmdBuilder":
    if condition and args:
      self.args.extend(str(arg) for arg in args)
    return self

  def build(self) -> list[str]:
    return self.args.copy()

  def __str__(self) -> str:
    return " ".join(self.args)


class Process:
  def __init__(self, proc):
    self._process = proc
    self._process.wait()
    
  def output(self):
    return self._process.stdout.read().decode('utf-8').strip()
  
  def error(self):
    return self._process.stderr.read().decode('utf-8').strip()
  
  def text(self):
    return f"{self.output()}{self.error()}"

  @property
  def returncode(self):
    return self._process.returncode


class ProcessBuilder:
  def __init__(self, cmd, cwd=None):
    self.cmd = cmd
    self.stdout, self.stdin, self.stderr = (
      subprocess.PIPE,
      subprocess.PIPE,
      subprocess.PIPE,
    )

    self.cwd = cwd or os.getcwd()
    self.shell = True
    
  def pipe(self, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    self.stdin = stdin
    self.stdout = stdout
    self.stderr = stderr
    return self.run()
  
  def run(self):
    return Process(subprocess.Popen(self.cmd, cwd=self.cwd, shell=self.shell, stdin=self.stdin, stdout=self.stdout, stderr=self.stderr))

 
def sh(cmd, *args, **kwargs):
  return ProcessBuilder(cmd, *args, **kwargs)
