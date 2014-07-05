from contextlib import contextmanager
import fcntl
import os

@contextmanager
def nonblock(fd):
  old_flags = fcntl.fcntl(fd, fcntl.F_GETFL)
  flags = old_flags | os.O_NONBLOCK
  try:
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)
    yield
  finally:
    fcntl.fcntl(fd, fcntl.F_SETFL, old_flags)
