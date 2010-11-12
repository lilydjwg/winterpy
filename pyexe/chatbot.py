#!/usr/bin/env python3
# vim:fileencoding=utf-8

'''
插件描述
  messages:
    每当有消息时调用 handler，参数为 Chatterous 对象，消息
    如果定义了 start，在机器人就绪时调用，参数为 Chatterous 对象
    如果定义了 end，在机器人结束时调用，参数为 Chatterous 对象
  initiative:
    并行运行，不需要（但可以）定义 start （以及 end）
    参数为 Chatterous 对象

  handler 在一个线程中运行，但 start 和 end 不是这样！

chatter 的附加属性
  msg_plugins, starters, enders
  run 是否要继续运行
'''

import sys
import traceback
import chatterous
import threading
from path import path as Path

groups = ['scu_ubuntu']
# groups = ['qingdao']

def thread_run(func, *args):
  t = threading.Thread(target=func, args=args)
  t.daemon = True
  t.start()

def import_plugin(type):
  dir = Path(chatterous.plugin_dir).join(type).expand()
  plugins = dir.glob('*.py')
  plugins.sort()
  sys.path[0:0] = [str(dir)]
  ret = []
  starters = []
  enders = []
  for x in plugins:
    name = x.rootname
    try:
      new = __import__(name) 
    except:
      print('加载插件 %s 时出错：' % name, file=sys.stderr)
      traceback.print_exc()
      continue
    try:
      new.handler
    except AttributeError:
      print('警告：插件 %s 没有定义 handler' % name)
      continue
    try:
      new.start
    except AttributeError:
      pass
    else:
      starters.append(new)
    try:
      new.end
    except AttributeError:
      pass
    else:
      enders.append(new)

    print('载入插件：%s' % name)
    ret.append(new)

  del sys.path[0]
  return ret, starters, enders

def chatbot():
  chatter = chatterous.Chatterous('lilybot')
  chatter.handshake()
  chatter.checkgroup(groups)
  chatter.subscribe(groups)
  chatter.run = True
  chatter.msg_plugins, chatter.starters, chatter.enders = import_plugin('messages')
  t = import_plugin('initiative')
  chatter.starters.extend(t[1])
  chatter.enders.extend(t[2])
  chatter.initiative = t[0]
  for f in chatter.starters:
    try:
      f.start(chatter)
    except:
      traceback.print_exc()

  print('开始接收消息')

  for f in chatter.initiative:
    try:
      thread_run(f.handler, chatter)
    except:
      traceback.print_exc()

  try:
    while chatter.run:
      msg = chatter.recvmsg()
      messages = [x for x in msg if 'data' in x]

      for m in messages:
        gp_id = m['channel'].rsplit('/', 2)[-1]
        gp = [x for x in chatter.groups if chatter.groups[x]['chat'] == gp_id][0]
        m['group'] = gp

      for f in chatter.msg_plugins:
        for m in messages:
          try:
            thread_run(f.handler, chatter, m)
          except:
            traceback.print_exc()

  except chatterous.ChatterousError:
    traceback.print_exc()
  except KeyboardInterrupt:
    print('退出。')

  for f in chatter.enders:
    try:
      f.end(chatter)
    except:
      traceback.print_exc()

if __name__ == '__main__':
  try:
    chatbot()
  except KeyboardInterrupt:
    print('退出。')
