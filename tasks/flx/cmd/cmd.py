import shlex
import inspect

from pydantic import BaseModel
from typing import Literal, Optional, Any

from flx.js import set_config
from flx.lib.process import sh
from flx.ui import Animate, Div
from flx.lib.utils import escape
from flx.console import SConsole
from flx.lib.utils import sanitize_html


DATA_TYPE = Literal['str', 'int', 'yon']

# Options Model
class OptionModel(BaseModel):
  type: DATA_TYPE = "str"
  value: Optional[Any] = None

  required: bool = True

  # Shared validation
  min: Optional[int] = None
  max: Optional[int] = None

# Options
class CommandOptions:
  def __init__(self, options=None):
    self._options: dict[str, OptionModel] = {} if options is None else { name: OptionModel(**option) for name, option in options.items() }

  def items(self):
    return self._options.items()
  
  def add(self, name: str, **kwargs):
    self._options[name] = OptionModel(**kwargs)
  
  def set(self, name: str, value):
    option = self._options.get(name)

    if option is None:
      raise Exception("Option not found")

    if option.type == "str":
      if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")

      if option.min is not None and len(value) < option.min:
        raise ValueError(f"{name} must be at least {option.min} characters")

      if option.max is not None and len(value) > option.max:
        raise ValueError(f"{name} must be at most {option.max} characters")
        
    elif option.type == "int":
      try:
        value = int(value)
      except (TypeError, ValueError):
        raise TypeError(f"{name} must be an int")
  
      if option.min is not None and value < option.min:
        raise ValueError(f"{name} must be >= {option.min}")
  
      if option.max is not None and value > option.max:
        raise ValueError(f"{name} must be <= {option.max}")

    elif option.type == "yon":
      if isinstance(value, str):
        value = value.lower()

      if value not in ("yes", "no"):
        raise TypeError(f"{name} must be 'yes' or 'no'")
    
    option.value = value

  def get(self, name: str):
    return self._options[name]

  def check(self):
    require_list = set()

    for name, option in self.items():
      if option.required and option.value is None:
        require_list.add(name)
    
    if len(require_list) > 0:
      raise Exception(f"Require options: [ {' '.join(require_list)} ]")
  
  def is_options_ok(self):
    try:
      self.check()
      return True
    except Exception:
      return False

# Command Parser
class ParsedCommand:
  def __init__(self, command: str):
    self.raw = command.strip()
    self.split_args = shlex.split(self.raw)
    self.length = len(self.split_args)

    self.command = ""
    self.args = []

    if self.length >= 1:
      self.command = self.split_args[0]
      self.args = self.split_args[1:]
    
    self.args_string = " ".join(self.args)

  def __str__(self):
    return self.raw

# Screen Control
class IScreen(SConsole):
  def __init__(self):
    super().__init__(padding=1)
    self.box.add_class("gap-y-1")
  
  def insert(self, code: str, auto_scroll=True):
    self.append(Animate(Div(code)), auto_scroll=auto_scroll)

class ICommand:
  def __init__(self, prompt=None, options=None):
    self._scr = IScreen()
    self._prompt = prompt or "Type command"
    # Command Registers
    self.commands = {
      name.removeprefix("do_"): getattr(self, name)
      for name in dir(self)
      if name.startswith("do_") and callable(getattr(self, name))
    }
    self.options = CommandOptions(options=options)

  @property
  def scr(self):
    return self._scr

  @property   # prompt
  def prompt(self):
    return self._prompt

  def commands_list(self) -> list[str]:
    return [name for name in self.commands.keys() if not name.startswith("_")]
  
  # Add Option
  def add_option(self, name, **kwargs):
    self.options.add(name, **kwargs)

  # Set prompt
  def set_prompt(self, prompt: str):
    self._prompt = prompt
  
  def add_func(self, name, func):
    if callable(func):
      self.commands[name] = func

  # Decorator
  def on(self, name: str):
    def wrapper(func):
      self.add_func(name, func)
    return wrapper
  
  def on_default(self, line):
    func = self.commands.get("_default")
    if callable(func):
      func(line)
  
  def on_precmd(self, line):
    func = self.commands.get("_precmd")
    if callable(func):
      func(line)
  
  def on_error(self, err, line):
    func = self.commands.get("_error")
    if callable(func):
      func(err, line)

  # Start io loop
  def cmdloop(self):
    while True:
      line = ParsedCommand(self._scr.input(self.prompt, autohide=False))
      
      self.on_precmd(line)

      if line.length <= 0:
        continue
  
      if line.command in { "exit", "quit", "q" }:
        break

      func = self.commands.get(line.command)

      if callable(func):
        try:
          if func(self.scr, line) is True:
            break
        except Exception as e:
          self.on_error(e, line)
      else:
        self.on_default(line)

# Smart command
class ISCommand(ICommand):
  def __init__(self, prompt=None, options=None):
    self._icmd = ICommand(prompt=prompt, options=options)
    
    self._icmd.add_func("set", self._set)
    self._icmd.add_func("help", self._help)
    self._icmd.add_func("?", self._help)
    self._icmd.add_func("options", self._options)
    self._icmd.add_func("commands", self._commands)
    self._icmd.add_func("clear", self.clear)

    self._icmd.add_func("_error", self.error)
    self._icmd.add_func("_default", self.default)

    self._icmd.add_func("start", self.__start)

    self.banner = None

    self.init()
    self.intro()
  
  @property
  def scr(self):
    return self._icmd.scr
  
  def get_option(self, name):
    return self._icmd.options.get(name)
   
  def option(self, name):
    return self.get_option(name).value

  def get_options_table(self):
    return f"""
      <!-- Table -->
      <div class="overflow-x-auto rounded-lg border border-zinc-700">
        <table class="min-w-full text-sm whitespace-nowrap">
          <thead class="bg-zinc-800 text-zinc-300">
            <tr>
              <th class="px-3 py-2 text-left">Name</th>
              <th class="px-3 py-2 text-left">Type</th>
              <th class="px-3 py-2 text-left">Value</th>
              <th class="px-3 py-2 text-left">Req</th>
              <th class="px-3 py-2 text-left">Min</th>
              <th class="px-3 py-2 text-left">Max</th>
            </tr>
          </thead>

          <tbody>
            {
              "".join([
                f'''
                <tr class="border-t border-zinc-700">
                  <td class="px-3 py-2 font-medium text-white">
                    {self.scr.clean(name)}
                  </td>
      
                  <td class="px-3 py-2">
                    <span class="rounded bg-red-500/10 px-2 py-1 text-xs font-mono text-red-400">
                      {option.type}
                    </span>
                  </td>
      
                  <td class="px-3 py-2 text-zinc-300">
                    {self.scr.clean(str(option.value)) if option.value is not None else "-"}
                  </td>
      
                  <td class="px-3 py-2">
                    {
                      '<span class="text-green-400">Yes</span>'
                      if option.required
                      else '<span class="text-zinc-500">No</span>'
                    }
                  </td>
      
                  <td class="px-3 py-2 text-zinc-300">
                    {option.min if option.min is not None else "-"}
                  </td>
      
                  <td class="px-3 py-2 text-zinc-300">
                    {option.max if option.max is not None else "-"}
                  </td>
                </tr>
                '''
                for name, option in self._icmd.options.items()
              ])
            }
          </tbody>
        </table>
      </div>
    """

  def intro(self):
    if self.banner:
      self.scr.pre(self.scr.sanitize(self.banner), justify="center", effect="fadeIn")

    self.scr.insert(f"""
      <div class="flex flex-col gap-1">
        <div class="bg-sky-500/15 text-sky-300 border border-sky-500/20 rounded px-2 py-1 font-medium">commands</div>
        <div class="flex flex-wrap gap-1">{ "".join([f'<p class="p-1 px-2 rounded border border-zinc-700 bg-zinc-800 text-zinc-300">{self.scr.clean(name)}</p>' for name in self._icmd.commands_list()])}</div>
        <div class="bg-sky-500/15 text-sky-300 border border-sky-500/20 rounded px-2 py-1 font-medium">options</div>
        {self.get_options_table()}
      </div>
    """)

  def init(self):
    pass

  def add_option(self, name, **kwargs):
    self._icmd.add_option(name, **kwargs)

  def print_box(self, text):
    self.scr.print(text, class_list="bg-black/20 p-1 rounded border border-white/20", effect="fadeIn")

  # Set 
  def help_set(self, scr):
    self.print_box("[blue]Usage[/blue]: set <[red]name[/red]> <[red]value[/red]>")

  def _set(self, scr, line):
    '''Set option'''
    if line.length < 2:
      return self._help_set(scr)

    name = line.args[0]
    value = " ".join(line.args[1:])
    self._icmd.options.set(name, value)

    self.print_box(f"[blue]SET[/blue]: {name}={value}")

  def _commands(self, scr, line):
    '''Display commands'''
    elements = []
    
    elements.append("<div class='space-y-1 rounded'>")
    elements.append('<div class="bg-sky-500/15 text-sky-300 border border-sky-500/20 rounded px-2 py-1 font-medium">command - (desc)</div>')

    for name, fn in sorted(self._icmd.commands.items()):
      if name.startswith("_"):
        continue
      # docstring
      desc = inspect.getdoc(fn) or "No description"

      elements.append(f"""
      <div class="p-1 text-sm rounded border border-zinc-700 bg-zinc-900 text-zinc-100">
        <span class="text-green-400">{scr.clean(name)}</span>
        <span class="text-zinc-400 px-2">-</span>
        <span class="text-zinc-300">{scr.clean(desc)}</span>
      </div>
      """)

    elements.append("</div>")
    
    scr.insert("".join(elements))

  def help_commands(self, scr):
    self.print_box("Display commands")

  # Optipns
  def _options(self, scr, line):
    '''Display options'''
    
    scr.insert('<div class="bg-sky-500/15 text-sky-300 border border-sky-500/20 rounded px-2 py-1 font-medium">options</div>')
    scr.insert(f"<div>{self.get_options_table()}</div>")

  def help_options(self, scr):
    self.print_box("Display options")
  
  # Help
  def _help(self, scr, line):
    '''Display help'''
    if line.length < 2:
      return self.help(scr)
    
    func = getattr(self, f"help_{line.args[0]}")
    if callable(func):
      func(scr)

  def help(self, _):
    self.intro()
  
  def help_help(self, scr):
    self.help(scr)

  # Clear Screen
  def clear(self, scr, _):
    '''Clear screen'''
    scr.clear()

  def help_clear(self, scr):
    self.print_box("clear screen")

  def default(self, line):
    self.print_box(f"Unknown command: [red]{line.command}[/red]")

  def error(self, err, line):
    self.print_box(f"[red]Error[/red]: {err}")

  # Start
  def start(self, scr, args):
    '''Start'''
    pass

  def help_start(self, scr):
    self.print_box("start script")

  def __start(self, scr, line):
    self._icmd.options.check()
    self.start(scr, line.args)

  # Cmdloop
  def cmdloop(self):
    self._icmd.cmdloop()
