from flx.js import html

def loading(icon):
  html("#panel", f'<div class="flex-1 flex items-center justify-center opacity-40 animate__animated animate__fadeIn">{icon}</div>')
