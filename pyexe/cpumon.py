#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
监视CPU的使用，过高时自动执行命令

2010年7月17日
'''

cmd = 'echo ================== >> ~/tmpfs/cpumon && top -n 1 -b | awk \'{if($4 != 0) print}\' >> ~/tmpfs/cpumon'

import os
import time

def getCPUUsage():
  cpu_before = open('/proc/stat').readline().split()[1:]
  time.sleep(1)
  cpu_after = open('/proc/stat').readline().split()[1:]
  cpu = list(map(lambda x, y: int(y)-int(x), cpu_before, cpu_after))
  # print(cpu_before, cpu_after, sep='\n')
  # print(cpu, sum(cpu))
  return 1 - cpu[3] / sum(cpu)

def monitor(cmd=cmd, threshold=0.9):
  while True:
    usage = getCPUUsage()
    print('CPU Usage: %.2f' % usage)
    if usage > threshold:
      os.system(cmd)

if __name__ == '__main__':
  try:
    monitor(threshold=.5)
  except KeyboardInterrupt:
    print('退出')
