import json
from time import sleep

from flx.ui import Animate, Div
from flx.lib.crypto import generate_uuid
from flx.lib.utils import sanitize_html, clean


# Pages Console
class ConsolePage:
  def __init__(self, console):
    self._console = console

  @property
  def scr(self):
    return self._console

  def display(self, name: str):
    fn = getattr(self, f"page_{name}", None)
    if fn is None:
      raise Exception(f"Page not found: {name}")

    self.scr.clear()
    fn().display(self.scr)

# Page Result
class PageResult:
  def __init__(self, input_) -> None:
    self._input = input_

  def get_input(self) -> str:
    return self._input

  @property
  def is_closed(self) -> bool:
    return self.get_input() == "__page__closed__"

  @property
  def is_back(self):
    return self.get_input() == "__page__back__"

# Page
class Page:
  def __init__(
    self,
    title: str | None = None,
    banner: str | None = None,
    back_button: bool  = False,
    close_button: bool = False
  ) -> None:
    self.title = title
    self.back_button = back_button
    self.close_button = close_button

    self.banner = banner

    self._input = None

  def to_text(self, code: str) -> str:
    return clean(code)

  def sanitize(self, code: str) -> str:
    return sanitize_html(code)

  def set_banner(self, banner: str) -> None:
    self.banner = banner

  def render_back_button(self) -> str:
    if not self.back_button:
      return ""
    
    return '''
      <button onclick="sendInput('__page__back__')" 
        class="flex items-center p-1 rounded bg-white/20">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 12 24"><path fill="currentColor" fill-rule="evenodd" d="m3.343 12l7.071 7.071L9 20.485l-7.778-7.778a1 1 0 0 1 0-1.414L9 3.515l1.414 1.414z"/></svg>
      </button>
    '''

  def render_close_button(self) -> str:
    if not self.close_button:
      return ""
    
    return '''
      <button onclick="sendInput('__page__closed__')" 
        class="p-1 rounded bg-red-400 flex items-center">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="m12 13.4l-4.9 4.9q-.275.275-.7.275t-.7-.275t-.275-.7t.275-.7l4.9-4.9l-4.9-4.9q-.275-.275-.275-.7t.275-.7t.7-.275t.7.275l4.9 4.9l4.9-4.9q.275-.275.7-.275t.7.275t.275.7t-.275.7L13.4 12l4.9 4.9q.275.275.275.7t-.275.7t-.7.275t-.7-.275z"/></svg>
      </button>
    '''

  def render_banner(self) -> str:
    if self.banner is None:
      return ""
    
    return f'''
      <pre class="p-4 bg-purple-400/10 border-b border-white/40 flex justify-center items-center overflow-auto text-xs text-center">
        {self.sanitize(self.banner)}
      </pre>
    '''

  def get_header(self) -> str:
    # If nothing to show then return empty
    if not self.title and not self.back_button and not self.close_button:
      return ""

    return f"""
      <div class="px-2 py-3 bg-blue-400/60 flex justify-between items-center gap-1">
        
        <!-- Left Side -->
        <div class="flex items-center gap-2">
          {self.render_back_button()}
          {f'<h1 class="text-lg text-bold truncate">{self.to_text(self.title)}</h1>' if self.title else ''}
        </div>

        <!-- Right Side -->
        {self.render_close_button()}
      </div>
    """

  def _render(self, body) -> Animate:
    el = Div(
      self.get_header(),
      self.render_banner(),
      body
    )

    el.add_class("flex-1 flex flex-col overflow-hidden")
    
    return Animate(el)

  def _start_input_loop(self, console, inject=None) -> PageResult:
    el = inject or console
    
    while True:
      el.clear()
      el.append(self.render())

      input_ = input()
      el.clear()

      return PageResult(input_)

# Options page
class OptionsPage(Page):
  def __init__(
    self,
    options,
    title: str | None = "Select an option",
    banner: str | None = None,
    back_button: bool = False,
    close_button: bool = False,
    display_index: bool = False
  ) -> None:
    super().__init__(title=title, banner=banner, back_button=back_button, close_button=close_button)
    self.options = options
    self.display_index = display_index

  def render(self) -> Animate:
    options = []

    for index, option in enumerate(self.options):
      index_tag = f'<span class="min-w-2 text-blue-400">{index + 1}</span>' if self.display_index else ""
      
      code = f'<div onclick="sendInput({index + 1})" class="px-2 py-3 border-b border-white/40 flex items-center gap-2 active:bg-white/20 transition-colors">{index_tag}{self.to_text(option)}</div>'
      options.append(code)

    return self._render(f'<div class="flex-1 flex flex-col overflow-y-auto">{"".join(options)}</div>')
 
  def display(self, console, inject=None) -> PageResult:
    return self._start_input_loop(console, inject=inject)

# Input Text Page
class InputPage(Page):
  def __init__(
    self,
    body: str | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    input_type=str,
    placeholder: str | None = None,
    autohide: bool = False
  ) -> None:
    super().__init__()
    
    # Auto hide after getting input
    self.autohide = autohide

    self.error_text = None

    self.body = body
    
    self.placeholder = placeholder
    
    self.min_length = min_length
    self.max_length = max_length
    self.input_type = input_type

  def _validate(self, text: str):
    expected_type = self.input_type
  
    try:
      text = expected_type(text)
    except (ValueError, TypeError):
      raise TypeError(
        f"Expected type {expected_type.__name__}, got {type(text).__name__}"
      )
  
    min_length = getattr(self, "min_length", None)
    max_length = getattr(self, "max_length", None)
  
    # ---- Numeric validation ----
    if isinstance(text, (int, float)):
      if min_length is not None and text < min_length:
        raise ValueError(f"Minimum value allowed is {min_length}")
  
      if max_length is not None and text > max_length:
        raise ValueError(f"Maximum value allowed is {max_length}")
  
    # ---- Length validation ----
    elif hasattr(text, "__len__"):
      if min_length is not None and len(text) < min_length:
        raise ValueError(f"Required minimum length is {min_length}")
  
      if max_length is not None and len(text) > max_length:
        raise ValueError(f"Required maximum length is {max_length}")
  
    return text

  def validate(self, text: str):
    try:
      return self._validate(text)
    except Exception as e:
      self.error_text = str(e)

    return None
  
  def render_error(self) -> str:
    return f'<div class="flex-1 flex justify-center items-center text-red-400"><h1>{self.to_text(self.error_text)}</h1></div>'

  def get_body(self) -> str:
    if self.error_text is not None:
      return self.render_error()

    if self.body is None:
      return ""
    
    return f'<div class="flex-1 flex justify-center items-center">{self.sanitize(self.body)}</div>'

  def set_body(self, body) -> None:
    self.body = body

  def render(self) -> Animate:
    return self._render(self.get_body())

  def display(self, console, inject=None) -> PageResult:
    el = inject or console

    while True:
      el.clear()
      el.append(self.render())

      self.error_text = None

      result = PageResult(console.input(self.placeholder or "", autohide=self.autohide))
      if result.is_back or result.is_closed:
        return result

      if self.validate(result.get_input()) is not None:
        el.clear()
        return result

# Iframe Page
class IframePage(Page):
  def __init__(self, url: str) -> None:
    super().__init__()
    self.url = url
  
  def render(self) -> Animate:
    return self._render(f'<iframe class="w-full h-full" src="{self.to_text(self.url)}"></iframe>')

  def display(self, console, inject=None) -> PageResult:
    el = inject or console

    el.clear()
    el.append(self.render())
    
    result = PageResult(input())
    
    el.clear()

    return result

# Items Selection Page
class SelectionPage(Page):
  def __init__(
    self,
    items: dict[str, str] = dict(),
    title: str | None = None,
    selected: list[str] = list()
  ) -> None:
    super().__init__()

    self.uid: str = generate_uuid()

    self.title: str | None = title
    self.items: dict[str, str] = items
    self.selected: list[str] = selected
  
  def add(self, label: str, name: str) -> "SelectionPage":
    self.items[label] = name
    return self

  def get_header(self):
    if not self.title:
      return ""

    return f"""
      <h1 class="p-2 bg-pink-400/60 border-b border-pink-400/60 text-white text-center text-lg">{self.to_text(self.title)}</h1>
    """

  def render_items(self) -> list[str]:
    items = []

    for label, name in self.items.items():
      is_selected = name in self.selected
      
      items.append(f"""
        <div
          data-name="{name}"
          data-selected="{'true' if is_selected else 'false'}"
          onclick="
            const selected = this.dataset.selected === 'true';
            this.dataset.selected = (!selected).toString();
            this.classList.toggle('bg-white/20');
            const values = [...this.parentElement.querySelectorAll('[data-selected=true]')]
              .map(e => e.dataset.name);
            document.getElementById('{self.uid}').value = JSON.stringify(values);
          "
          class="px-2 py-3 border-b border-b-white/40 flex items-center gap-2 cursor-pointer transition-colors {'bg-white/20' if is_selected else ''}">
          {self.to_text(label)}
        </div>
        """
      )
    
    return items

  def render(self) -> Animate:
    items = self.render_items()

    html = f"""
      <form class="flex-1 flex flex-col overflow-y-auto">
        <input
          type="hidden"
          id="{self.uid}"
          value='{json.dumps(list(self.selected))}'>

        <div class="flex-1 flex flex-col overflow-y-auto">
          {''.join(items)}
        </div>

        <div class="flex border-t border-white/20">
          <button
            type="button"
            onclick="sendInput('__cancel__')"
            class="flex-1 bg-white/10 px-4 py-3 text-white font-medium hover:bg-white/20 active:bg-white/30 transition-colors">
            Cancel
          </button>
          
          <button
            type="button"
            onclick="sendInput(document.getElementById('{self.uid}').value)"
            class="flex-1 bg-white/20 px-4 py-3 text-white font-medium hover:bg-white/20 active:bg-white/30 transition-colors">
            Done
          </button>
      </div>
    </form>
    """

    return self._render(html)

  def display(self, console, inject=None) -> list[str]:
    el = inject or console
    
    el.clear()
    el.append(self.render())

    input_data = input()
    
    el.clear()

    if input_data == "__cancel__":
      return []

    return json.loads(input_data)

# FormPage
class FormPage(Page):
  def __init__(
    self,
    title: str | None = None,
  ) -> None:
    super().__init__()

    self.uid = generate_uuid()
    self.title: str | None = title
    self.fields: list[dict] = []
    self.values = {}
  
  def _add(
    self,
    *,
    name: str,
    label: str,
    field_type: str,
    placeholder: str = "",
    info: str | None = None,
    value: str | bool | None = None,
    required: bool = False,
    options: dict[str, str] | None = None,
    attrs: dict[str, str | int | float] | None = None,
  ) -> "FormPage":
    self.fields.append({
      "name": name,
      "label": label,
      "type": field_type,
      "info": info,
      "placeholder": placeholder,
      "value": value if value is not None else self.values.get(name, ""),
      "required": required,
      "options": options or {},
      "attrs": attrs or {},
    })
    return self
  
  def add_text(
    self,
    name: str,
    label: str,
    info: str | None = None,
    placeholder: str = "",
    value: str | None = None,
    required: bool = False,
  ) -> "FormPage":
    return self._add(
      name=name,
      label=label,
      field_type="text",
      info=info,
      placeholder=placeholder,
      value=value,
      required=required,
    )

  def add_password(
    self,
    name: str,
    label: str,
    info: str | None = None,
    placeholder: str = "",
    value: str | None = None,
    required: bool = False,
  ) -> "FormPage":
    return self._add(
      name=name,
      label=label,
      info=info,
      field_type="password",
      placeholder=placeholder,
      value=value,
      required=required,
    )

  def add_email(
    self,
    name: str,
    label: str,
    info: str | None = None,
    placeholder: str = "",
    value: str | None = None,
    required: bool = False,
  ) -> "FormPage":
    return self._add(
      name=name,
      label=label,
      info=info,
      field_type="email",
      placeholder=placeholder,
      value=value,
      required=required,
    )
  
  def add_number(
    self,
    name: str,
    label: str,
    info: str | None = None,
    placeholder: str = "",
    value: str | None = None,
    required: bool = False,
    min: int | float | None = None,
    max: int | float | None = None,
    step: int | float | None = None,
  ) -> "FormPage":
    attrs = {}

    if min is not None:
      attrs["min"] = min
    if max is not None:
      attrs["max"] = max
    if step is not None:
      attrs["step"] = step

    return self._add(
      name=name,
      label=label,
      info=info,
      field_type="number",
      placeholder=placeholder,
      value=value,
      required=required,
      attrs=attrs,
    )

  def add_tel(
    self,
    name: str,
    label: str,
    info: str | None = None,
    placeholder: str = "",
    value: str | None = None,
    required: bool = False,
  ) -> "FormPage":
    return self._add(
      name=name,
      label=label,
      info=info,
      field_type="tel",
      placeholder=placeholder,
      value=value,
      required=required,
    )

  def add_url(
    self,
    name: str,
    label: str,
    info: str | None = None,
    placeholder: str = "",
    value: str | None = None,
    required: bool = False,
  ) -> "FormPage":
    return self._add(
    name=name,
    label=label,
    info=info,
    field_type="url",
    placeholder=placeholder,
    value=value,
    required=required,
    )

  def add_date(
    self,
    name: str,
    label: str,
    info: str | None = None,
    value: str | None = None,
    required: bool = False,
  ) -> "FormPage":
    return self._add(
      name=name,
      label=label,
      info=info,
      field_type="date",
      value=value,
      required=required,
    )

  def add_time(
    self,
    name: str,
    label: str,
    info: str | None = None,
    value: str | None = None,
    required: bool = False,
  ) -> "FormPage":
    return self._add(
      name=name,
      label=label,
      info=info,
      field_type="time",
      value=value,
      required=required,
    )

  def add_datetime(
    self,
    name: str,
    label: str,
    info: str | None = None,
    value: str | None = None,
    required: bool = False,
  ) -> "FormPage":
    return self._add(
      name=name,
      label=label,
      info=info,
      field_type="datetime-local",
      value=value,
      required=required,
    )
  
  def add_color(
    self,
    name: str,
    label: str,
    info: str | None = None,
    value: str | None = "#000000",
    required: bool = False,
  ) -> "FormPage":
    return self._add(
      name=name,
      label=label,
      info=info,
      field_type="color",
      value=value,
      required=required
    )

  def add_checkbox(
    self,
    name: str,
    label: str,
    checked: bool = False,
  ) -> "FormPage":
    return self._add(
      name=name,
      label=label,
      field_type="checkbox",
      value=checked,
    )

  def add_textarea(
    self,
    name: str,
    label: str,
    info: str | None = None,
    placeholder: str = "",
    value: str | None = None,
    required: bool = False,
  ) -> "FormPage":
    return self._add(
      name=name,
      label=label,
      info=info,
      field_type="textarea",
      placeholder=placeholder,
      value=value,
      required=required,
    )

  def add_select(
    self,
    name: str,
    label: str,
    options: dict[str, str],
    info: str | None = None,
    value: str | None = None,
    required: bool = False,
  ) -> "FormPage":
    return self._add(
      name=name,
      label=label,
      info=info,
      field_type="select",
      value=value,
      required=required,
      options=options,
    )

  def get_header(self):
    if not self.title:
      return ""

    return f"""
      <h1 class="p-2 bg-pink-400/60 border-b border-pink-400/60 text-white text-center text-lg">
        {self.to_text(self.title)}
      </h1>
    """
  
  def get_attrs(self, field) -> str:
    return " ".join(
      f'{k}="{self.to_text(v)}"'
      for k, v in field["attrs"].items()
    )
  
  def render_element(self, field, body):
    info_val = field["info"]
    
    info = f"""
      <label class="block text-white/80 text-sm mt-1 text-xs opacity-60">
        {self.to_text(info_val)}
      </label>
    """ if info_val else ""

    return f"""
      <div class="px-3 py-1">
        <label class="block text-white/80 text-sm mb-1 font-heading">
          {self.to_text(field["label"])}
        </label>
        {body}{info}
      </div>
    """

  def render_input(self, field) -> str:
    extra_attrs = self.get_attrs(field)

    return self.render_element(field, f"""
      <input
        data-field="{field["name"]}"
        type="{field["type"]}"
        value="{self.to_text(field["value"])}"
        placeholder="{self.to_text(field["placeholder"])}"
        autocomplete="off"
        autocapitalize="off"
        autocorrect="off"
        spellcheck="false"
        {extra_attrs}
        {"required" if field["required"] else ""}
        class="w-full rounded bg-white/10 border border-white/20 p-2 text-white placeholder-white/40 outline-none focus:border-pink-400">
    """)

  def render_textarea(self, field) -> str:
    extra_attrs = self.get_attrs(field)

    return self.render_element(field, f"""
      <textarea
        data-field="{field["name"]}"
        autocomplete="off"
        autocapitalize="off"
        autocorrect="off"
        spellcheck="false"
        placeholder="{self.to_text(field["placeholder"])}"
        {"required" if field["required"] else ""}
        {extra_attrs}
        class="w-full min-h-32 resize-y rounded bg-white/10 border border-white/20 p-2 text-white placeholder-white/40 outline-none focus:border-pink-400"
        >{self.to_text(field["value"])}</textarea>
    """)

  def render_select(self, field) -> str:
    extra_attrs = self.get_attrs(field)
    selected_value = field["value"]

    options = "".join(
      f"""
      {'<option value="" disabled selected hidden>Select...</option>' if len(selected_value) <= 0 else ''}
      <option
        class="bg-zinc-900 text-white"
        value="{self.to_text(value)}"
        {"selected" if value == selected_value else ""}>
        {self.to_text(label)}
      </option>
      """
      for value, label in field["options"].items()
    )

    return self.render_element(field, f"""
      <select
        data-field="{field["name"]}"
        {"required" if field["required"] else ""}
        {extra_attrs}
        class="w-full rounded bg-white/10 border border-white/20 p-2 text-white outline-none focus:border-pink-400">
        {options}
      </select>
    """)

  def render_checkbox(self, field) -> str:
    extra_attrs = self.get_attrs(field)

    return f"""
      <div class="p-2 px-3 bg-transparent">
        <label class="flex items-center gap-3 cursor-pointer text-white">
          <input
            data-field="{field['name']}"
            type="checkbox"
            {"checked" if field["value"] else ""}
            {extra_attrs}
            class="size-5 appearance-none bg-transparent border border-white/20 rounded checked:bg-pink-400 checked:border-pink-400 transition-colors">
          <span>{self.to_text(field["label"])}</span>
        </label>
      </div>
    """

  def render_color(self, field) -> str:
    extra_attrs = self.get_attrs(field)
    value = self.to_text(field["value"])

    return self.render_element(field, f"""
      <input
        data-field="{field["name"]}"
        type="color"
        value="{value}"
        oninput="this.nextElementSibling.textContent=this.value"
        {"required" if field["required"] else ""}
        {extra_attrs}
        class="h-10 w-14 rounded border border-white/20 bg-transparent cursor-pointer">

      <span class="text-white/70 font-mono">
        {value}
      </span>
    """)

  def render_fields(self) -> list[str]:
    html = []

    for field in self.fields:
      match field["type"]:
        case "textarea":
          html.append(self.render_textarea(field))
        case "select":
          html.append(self.render_select(field))
        case "checkbox":
          html.append(self.render_checkbox(field))
        case "color":
          html.append(self.render_color(field))
        case _:
          html.append(self.render_input(field))

    return html

  def render(self) -> Animate:
    html = f"""
      <div class="flex-1 flex flex-col overflow-y-auto">

        <div id="{self.uid}" class="flex-1 overflow-y-auto">
          {''.join(self.render_fields())}
        </div>

        <div class="flex border-t border-white/20">

          <button
            type="button"
            onclick="sendInput('__cancel__')"
            class="flex-1 bg-white/10 px-4 py-3 text-white font-medium hover:bg-white/20 active:bg-white/30 transition-colors">
            Cancel
          </button>

          <button
            type="button"
            onclick="
              const root = document.getElementById('{self.uid}');
              const values = {{}};
            
              for (const e of root.querySelectorAll('[data-field]')) {{
                if (!e.checkValidity()) {{
                  e.reportValidity();
                  e.focus();
                  return;
                }}
            
                values[e.dataset.field] = e.type === 'checkbox'
                  ? e.checked
                  : e.value;
              }}
            
              sendInput(JSON.stringify(values));
            "
            class="flex-1 bg-white/20 px-4 py-3 text-white font-medium hover:bg-white/30 active:bg-white/40 transition-colors">
            Done
          </button>
        </div>
      </div>
    """

    return self._render(html)

  def display(self, console, inject=None) -> dict[str, str]:
    el = inject or console

    el.clear()
    el.append(self.render())

    result = input()

    el.clear()

    if result == "__cancel__":
      return None

    result = json.loads(result)

    self.values.update(result)
    return result

# --------- No Interaction Pages

# Loading page
class LoadingPage:
  def __init__(self, label: str | None = None) -> None:
    self.label = label

  def render_loading_icon(self, size=32) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24"><g fill="currentColor"><circle cx="12" cy="3.5" r="1.5"><animate attributeName="fill-opacity" dur="2.4s" keyTimes="0;0.125;0.25;1" repeatCount="indefinite" values="1;1;0;0"/></circle><circle cx="16.25" cy="4.64" r="1.5" opacity="0"><set fill="freeze" attributeName="opacity" begin="0.2s" to="1"/><animate attributeName="fill-opacity" begin="0.2s" dur="2.4s" keyTimes="0;0.125;0.25;1" repeatCount="indefinite" values="1;1;0;0"/></circle><circle cx="19.36" cy="7.75" r="1.5" opacity="0"><set fill="freeze" attributeName="opacity" begin="0.4s" to="1"/><animate attributeName="fill-opacity" begin="0.4s" dur="2.4s" keyTimes="0;0.125;0.25;1" repeatCount="indefinite" values="1;1;0;0"/></circle><circle cx="20.5" cy="12" r="1.5" opacity="0"><set fill="freeze" attributeName="opacity" begin="0.6s" to="1"/><animate attributeName="fill-opacity" begin="0.6s" dur="2.4s" keyTimes="0;0.125;0.25;1" repeatCount="indefinite" values="1;1;0;0"/></circle><circle cx="19.36" cy="16.25" r="1.5" opacity="0"><set fill="freeze" attributeName="opacity" begin="0.8s" to="1"/><animate attributeName="fill-opacity" begin="0.8s" dur="2.4s" keyTimes="0;0.125;0.25;1" repeatCount="indefinite" values="1;1;0;0"/></circle><circle cx="16.25" cy="19.36" r="1.5" opacity="0"><set fill="freeze" attributeName="opacity" begin="1s" to="1"/><animate attributeName="fill-opacity" begin="1s" dur="2.4s" keyTimes="0;0.125;0.25;1" repeatCount="indefinite" values="1;1;0;0"/></circle><circle cx="12" cy="20.5" r="1.5" opacity="0"><set fill="freeze" attributeName="opacity" begin="1.2s" to="1"/><animate attributeName="fill-opacity" begin="1.2s" dur="2.4s" keyTimes="0;0.125;0.25;1" repeatCount="indefinite" values="1;1;0;0"/></circle><circle cx="7.75" cy="19.36" r="1.5" opacity="0"><set fill="freeze" attributeName="opacity" begin="1.4s" to="1"/><animate attributeName="fill-opacity" begin="1.4s" dur="2.4s" keyTimes="0;0.125;0.25;1" repeatCount="indefinite" values="1;1;0;0"/></circle><circle cx="4.64" cy="16.25" r="1.5" opacity="0"><set fill="freeze" attributeName="opacity" begin="1.6s" to="1"/><animate attributeName="fill-opacity" begin="1.6s" dur="2.4s" keyTimes="0;0.125;0.25;1" repeatCount="indefinite" values="1;1;0;0"/></circle><circle cx="3.5" cy="12" r="1.5" opacity="0"><set fill="freeze" attributeName="opacity" begin="1.8s" to="1"/><animate attributeName="fill-opacity" begin="1.8s" dur="2.4s" keyTimes="0;0.125;0.25;1" repeatCount="indefinite" values="1;1;0;0"/></circle><circle cx="4.64" cy="7.75" r="1.5" opacity="0"><set fill="freeze" attributeName="opacity" begin="2s" to="1"/><animate attributeName="fill-opacity" begin="2s" dur="2.4s" keyTimes="0;0.125;0.25;1" repeatCount="indefinite" values="1;1;0;0"/></circle><circle cx="7.75" cy="4.64" r="1.5" opacity="0"><set fill="freeze" attributeName="opacity" begin="2.2s" to="1"/><animate attributeName="fill-opacity" begin="2.2s" dur="2.4s" keyTimes="0;0.125;0.25;1" repeatCount="indefinite" values="1;1;0;0"/></circle></g></svg>'

  def render_label(self) -> str:
    if self.label is None:
      return ""

    return f'<h1 class="text-sm opacity-80">{clean(str(self.label))}</h1>'

  def render(self) -> Animate:
    return Animate(Div(f"""
      {self.render_loading_icon()}
      <h1>{self.render_label()}</h1>
    """).add_class("bg-black/60 flex-1 flex flex-col justify-center items-center overflow-hidden"))

  def display(self, console, inject=None):
    el = inject or console
    
    el.clear()
    el.append(self.render())

    return lambda: el.clear()

# Animation Page
class AnimationPage:
  def __init__(self, frames: list, delay: float = 0.6) -> None:
    self.delay = delay
    self.frames = frames

  def render(self, frame) -> str:
    return Animate(Div(f"""
      <pre>{sanitize_html(frame)}</pre>
    """).add_class("flex-1 flex flex-col justify-center items-center overflow-hidden"))

  def display(self, console, inject=None) -> None:
    el = inject or console

    for frame in self.frames:
      el.clear()
      el.append(self.render(frame))
    
      sleep(self.delay)

    el.clear()

