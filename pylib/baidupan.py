import time
import json
from urllib.parse import quote

class PanException(Exception): pass

class CaptchaRequired(PanException): pass

class Pan:
  _session = None

  def __init__(self, session):
    self._session = session

  def download(self, url):
    import subprocess

    info = self.get_info(url)
    print(info)
    code = s = captcha_exc = None
    while True:
      try:
        fileinfo = self.get_download_link(
          uk = info['uk'],
          fs_ids = str(info['fs_ids']),
          share_id = info['share_id'],
          sign = info['sign'],
          vcode_input = code,
          vcode_str = s,
          captcha_exc = captcha_exc,
        )
        break
      except CaptchaRequired as e:
        captcha_exc = e
        img, s = self.get_captcha(e)
        img = self._session.get(img).content
        p = subprocess.Popen(["display", "-"], stdin=subprocess.PIPE)
        p.stdin.write(img)
        p.stdin.close()
        code = input('请输入验证码：')
        p.terminate()
    print(fileinfo)
    cmd = ["wget", "-c", fileinfo['url']]
    if 'name' in fileinfo:
      cmd.extend(["-O", fileinfo['name']])
    subprocess.call(cmd)

  def get_captcha(self, captcha_exc):
    if len(captcha_exc.args) == 3:
      return captcha_exc.args[1:]

    url = 'http://pan.baidu.com/api/getcaptcha?prod=share&bdstoken=&channel=chunlei&clienttype=0&web=1&app_id=250528'
    text = self._session.get(url).content.decode('utf-8')
    data = json.loads(text)
    return data['vcode_img'], data['vcode_str']

  def get_info(self, url):
    # TODO: use mobile version
    # TODO: parse out #path (desktop) or dir (mobile)
    url = url.replace('/wap/', '/share/') # mobile version is harder to parse
    text = self._session.get(url).content.decode('utf-8')
    ret = {}
    for l in text.splitlines():
      l = l.strip()
      if l.startswith('yunData.MYUK'):
        ret.setdefault('uk', l.split('"')[1])
      elif l.startswith('yunData.SHARE_ID'):
        ret['share_id'] = l.split('"')[1]
      elif l.startswith('yunData.SIGN'):
        ret['sign'] = l.split('"')[1]
      elif l.startswith('yunData.FILEINFO'):
        fileinfo = json.loads(l.split()[2][:-1])
        ret['fs_ids'] = [x['fs_id'] for x in fileinfo]
      elif l.startswith('yunData.SHAREPAGETYPE'):
        # single_file_page, multi_file
        ret['share_type'] = l.split('"')[1]

    if set(ret.keys()) != {'uk', 'share_id', 'sign', 'fs_ids', 'share_type'}:
      raise PanException('parameter parsing failed: only got keys %s' % list(ret.keys()))

    return ret

  def get_download_link(self, uk, fs_ids, share_id, sign, vcode_input=None, vcode_str=None, captcha_exc=None):
    post = {
      'uk': uk,
      'product': 'share',
      'encrypt': '0',
      'fid_list': fs_ids,
      'primaryid': share_id,
    }
    if vcode_input:
      post['vcode_input'] = vcode_input
      post['vcode_str'] = vcode_str

    t = captcha_exc and captcha_exc.args[0] or int(time.time())
    url = 'http://pan.baidu.com/api/sharedownload?sign=%s&timestamp=%s&bdstoken=&channel=chunlei&clienttype=0&web=1&app_id=250528' % (
      sign, t,
    )
    text = self._session.post(url, data=post).content.decode('utf-8')
    data = json.loads(text)

    errno = data['errno']
    if errno == 0:
      pass
    elif errno == -20:
      raise CaptchaRequired(t)
    elif errno == 112:
      raise PanException('expired, please retry')
    elif errno in (121, 113):
      # TODO download by smaller groups
      # http://pan.baidu.com/share/list?uk=1479304633&shareid=392044338&page=1&num=100&dir=%2F%E9%9F%B3%E4%B9%90&order=time&desc=1&_=1415690295367&bdstoken=&channel=chunlei&clienttype=0&web=1&app_id=250528
      raise PanException('too many files to download')
    else:
      raise PanException('unknown errno %s' % errno)

    if 'dlink' in data:
      # batchdownload
      return {
        'url': data['dlink'],
      }

    # FIXME: isdir: 1 and path exists, or multiple files
    fileinfo = data['list'][0]
    print(fileinfo)
    # What does md5 field do?
    return {
      'url': fileinfo['dlink'],
      'name': fileinfo['server_filename'],
    }

  def get_download_link_mobile(self, uk, fs_ids, share_id, sign,
                               vcode_input=None, vcode_str=None, captcha_exc=None):
    '''use mobile interface, can only download one file per time'''
    t = captcha_exc and captcha_exc.args[0] or int(time.time())
    url = 'http://pan.baidu.com/share/download?uk=%s&shareid=%s&fid_list=%s&sign=%s&timestamp=%s' % (
      uk, share_id, quote(fs_ids), sign, t)
    if vcode_input:
      url += '&input=%s&vcode=%s' % (vcode_input, vcode_str)

    text = self._session.get(url).content.decode('utf-8')
    data = json.loads(text)

    errno = data['errno']
    if errno == 0:
      pass
    elif errno == -19:
      raise CaptchaRequired(t, data['img'], data['vcode'])
    else:
      raise PanException('unknown errno %s' % errno)

    return {
      'url': data['dlink'],
    }

