def run_in_thread(daemon):
  import threading
  fn = None
  def run(*k, **kw):
    t = threading.Thread(target=fn, args=k, kwargs=kw)
    t.daemon = daemon
    t.start()
    return t
  if isinstance(daemon, bool):
    def wrapper(callback):
      nonlocal fn
      fn = callback
      return run
    return wrapper
  else:
    fn = daemon
    daemon = False
    return run

