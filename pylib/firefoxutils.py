import base64
import ctypes

class NSSItem(ctypes.Structure):
    _fields_ = [('type', ctypes.c_uint),
                ('data', ctypes.c_void_p),
                ('len', ctypes.c_uint)]

class NSSError(Exception):
  def __str__(self):
    return '%s: %s' % self.args

class NSSDecryptor:
  # modified from
  # https://github.com/Unode/firefox_decrypt

  def handle_error(self):
    nss = self.nss
    error = nss.PORT_GetError()
    error_str = nss.PR_ErrorToString(error).decode('utf-8')
    error_name = nss.PR_ErrorToName(error).decode('utf-8')
    raise NSSError(error_name, error_str)

  def __init__(self, profile_dir, password=''):
    nss = self.nss = ctypes.CDLL('libnss3.so')
    nss.PR_ErrorToString.restype = ctypes.c_char_p
    nss.PR_ErrorToName.restype = ctypes.c_char_p

    ret = nss.NSS_Init(profile_dir.encode('utf-8'))
    if ret != 0:
      self.handle_error()

    if password:
      p_password = ctypes.c_char_p(password.encode('utf-8'))
      keyslot = nss.PK11_GetInternalKeySlot()
      if keyslot is None:
        self.handle_error()

      ret = nss.PK11_CheckUserPassword(keyslot, p_password)
      if ret != 0:
        self.handle_error()

  def decrypt(self, s):
    datain = NSSItem()
    dataout = NSSItem()
    raw = base64.b64decode(s)
    datain.data = ctypes.cast(ctypes.c_char_p(raw), ctypes.c_void_p)
    datain.len = len(raw)
    ret = self.nss.PK11SDR_Decrypt(
      ctypes.byref(datain), ctypes.byref(dataout), None)
    if ret == -1:
      self.handle_error()

    data = ctypes.string_at(dataout.data, dataout.len)
    return data.decode()
