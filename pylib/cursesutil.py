import curses
import readline
import ctypes
import ctypes.util
import struct
from 字符集 import width

rllib_path = ctypes.util.find_library('readline')
rllib = ctypes.CDLL(rllib_path)

def getstr(win, y=None, x=None):
  _, col = win.getmaxyx()
  if x is None or y is None:
    y, x = win.getyx()
  inputbox = curses.newwin(1, col-x, y, x)
  ret = ''
  ok = False
  eof = False
  def callback(s):
    nonlocal ok, ret, eof
    if s is None:
      rllib.rl_callback_handler_remove()
      eof = True
    elif not s:
      ok = True
    else:
      ret = s.decode()
      ok = True

  cbfunc = ctypes.CFUNCTYPE(None, ctypes.c_char_p)

  rllib.rl_callback_handler_install.restype = None
  rllib.rl_callback_handler_install(ctypes.c_char_p(b""), cbfunc(callback))

  while True:
    rllib.rl_callback_read_char()
    if ok:
      break
    if eof:
      raise EOFError
    inputbox.erase()
    # 这样获取的值不对。。。
    # bbuf = ctypes.string_at(rllib.rl_line_buffer)
    buf = readline.get_line_buffer()
    bbuf = buf.encode()
    inputbox.addstr(0, 0, buf)
    rl_point = struct.unpack('I', ctypes.string_at(rllib.rl_point, 4))[0]
    w = width(bbuf[:rl_point].decode())
    inputbox.move(0, w)
    inputbox.refresh()

  del inputbox
  return ret

