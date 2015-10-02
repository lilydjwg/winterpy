#!/usr/bin/env python3

import os
import sys
import tempfile
from subprocess import check_call as run
from subprocess import Popen, PIPE, CalledProcessError
from xml.etree import ElementTree as ET
from collections import namedtuple

from myutils import at_dir, firstExistentPath

VER_ATTR = '{http://schemas.android.com/apk/res/android}versionName'
ICON_ATTR = '{http://schemas.android.com/apk/res/android}icon'
NAME_ATTR = '{http://schemas.android.com/apk/res/android}label'

ApkInfo = namedtuple('ApkInfo', 'id version name icon')
class ApktoolFailed(Exception): pass

def read_string(s):
  if s and s.startswith('@string/'):
    sid = s.split('/', 1)[1]
    for d in ('values-zh-rCN', 'values-zh-rTW', 'values-zh-rHK', 'values'):
      if not os.path.isdir(d):
        continue
      strings = ET.parse(os.path.join(d, 'strings.xml')).getroot()
      val = strings.findtext('string[@name="%s"]' % sid)
      if val:
        return val
  return s

def apkinfo(apk):
  with tempfile.TemporaryDirectory('apk') as tempdir:
    try:
      run(["apktool", "d", "-f", "-s", apk, "-o", tempdir])
    except CalledProcessError:
      raise ApktoolFailed

    with at_dir(tempdir):
      manifest = ET.parse('AndroidManifest.xml').getroot()
      package_id = manifest.get('package')
      package_ver = manifest.get(VER_ATTR)

      app = manifest.find('application')
      icon = app.get(ICON_ATTR)
      name = app.get(NAME_ATTR)

      if os.path.isdir('res'):
        with at_dir('res'):
          name = read_string(name)
          package_ver = read_string(package_ver)

          if icon and icon.startswith('@'):
            dirname, iconname = icon[1:].split('/', 1)
            iconfile = firstExistentPath(
              '%s/%s.png' % (d, iconname) for d in
              (dirname + x for x in
               ('-xxhdpi', '-xhdpi', '-hdpi', '', '-nodpi'))
            )
            with open(iconfile, 'rb') as f:
              icon = f.read()

    return ApkInfo(package_id, package_ver, name, icon)

def showInfo(apks):
  for apk in apks:
    try:
      info = apkinfo(apk)
    except ApktoolFailed:
      print('E: apktool failed.')
      continue

    print('I: displaying info as image...')
    display = Popen(['display', '-'], stdin=PIPE)
    convert = Popen([
      'convert', '-alpha', 'remove',
      '-font', '文泉驿正黑', '-pointsize', '12', '-gravity', 'center',
      'label:' + info.id,
      'label:%s' % info.version,
      '-' if info.icon else 'label:(No Icon)',
      'label:' + (info.name or '(None)'),
      '-append', 'png:-',
    ], stdin=PIPE, stdout=display.stdin)
    if info.icon:
      convert.stdin.write(info.icon)
    convert.stdin.close()
    convert.wait()
    display.stdin.close()
    display.wait()

if __name__ == '__main__':
  showInfo(sys.argv[1:])
