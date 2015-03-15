# HALF WORK, TAKE CARE!

import sys
from collections import namedtuple

import serial

class ATError(Exception):
  pass

class SMSInfo(namedtuple('SMSInfo', 'stat pdu')):
  def tpdu_length(self):
    raise NotImplementedError

class AT:
  debug = False

  def __init__(self, device):
    self.s = serial.Serial(device)

  def sms_read(self, index):
    info, pdu = self.command('+CMGR=1')
    stat, reserved, length = info.split(None, 1)[1].decode().split(',')
    return SMSInfo(int(stat), pdu)

  def sms_write(self, sms):
    cmd = '+CMGW=%d,%d\r' % (sms.tpdu_length(), sms.stat)
    cmd = cmd.encode() + sms.pdu + b'\x1a'
    self.command(cmd)

  def command(self, s):
    if isinstance(s, str):
      s = s.encode()
    s = b'AT' + s + b'\r\n'
    self._dprint('>', s)
    self.s.write(s)
    return self.read_reply()

  def read_reply(self):
    s = self.s
    ret = []
    while True:
      l = s.readline().rstrip()
      self._dprint('<', l)
      if not l:
        continue
      elif l.startswith((b'AT+', b'AT^')):
        continue
      elif l in (b'ERROR', b'COMMAND NOT SUPPORT'):
        raise ATError(l.decode())
      elif l.startswith(b'+CMS ERROR: '):
        raise ATError(l.decode())
      elif l == b'OK':
        break
      else:
        ret.append(l)
    return ret

  def shutup(self):
    s = self.s
    s.write(b"AT^CURC=0\r\n")
    s.setTimeout(0.1)
    s.readall()
    s.setTimeout(None)

  def _dprint(self, *args):
    if self.debug:
      print(*args, file=sys.stderr)
