from flx.lib.process import PTYProcess



def start(path, args):
  path.chmod(path.stat().st_mode | 0o111)

  cmd = ["sh", str(path), *args] if path.suffix == ".sh" else [str(path), *args]

  PTYProcess(cmd, callback=print).run()