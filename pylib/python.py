import os

def mymodsImported(scriptfile):
  '''导入的模块哪些是通过环境变量找到的？'''
  try:
    dirs = os.getenv('PYTHONPATH').split(':')
  except AttributeError:
    return []

  if not dirs:
    return []

  from modulefinder import ModuleFinder
  finder = ModuleFinder()
  finder.run_script(scriptfile)

  def filterdir(mod):
    file = mod.__file__
    if not file:
      return False
    for i in dirs:
      if file.startswith(i):
        return True
    return False

  return [m for m in finder.modules.values() if filterdir(m)]
