'''
系统工具，大多是调用外部程序
'''

import subprocess

def getCPUTemp():
  status, output = subprocess.getstatusoutput('sensors')
  if status != 0:
    raise SubprocessError("failed to execute `sensors'")
  output = output.split('\n')
  for l in output:
    if l.startswith('CPU Temperature:'):
      end = l.find('°')
      return float(l[16:end])
  raise SubprocessError('CPU Temperature not available')

def setMaxCPUFreq(freq):
  cmd = ['cpufreq-set', '--max', str(freq)]
  retcode = subprocess.call(cmd)
  if retcode != 0:
    raise SubprocessError()

class SubprocessError(SystemError): pass
