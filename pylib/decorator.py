#!/usr/bin/env python3
# vim:fileencoding=utf-8

def run_in_thread_daemon(fn):
  import threading
  def run(*k, **kw):
    t = threading.Thread(target=fn, args=k, kwargs=kw)
    t.daemon = True
    t.start()
  return run

def run_in_thread(fn):
  import threading
  def run(*k, **kw):
    t = threading.Thread(target=fn, args=k, kwargs=kw)
    t.start()
  return run

