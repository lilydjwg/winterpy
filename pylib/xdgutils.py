from string import Template
from collections import defaultdict

class ExecTempate(Template):
  delimiter = '%'
  idpattern = '[A-Za-z%]'
  flags = 0

def prepExec(entry):
  # http://standards.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html#exec-variables
  exec_t = ExecTempate(entry.getExec())
  d = defaultdict(lambda: '')
  d['%'] = '%'
  d['c'] = entry.getName()
  icon = entry.getIcon()
  if icon:
    d['i'] = '--icon "%s"' % icon
  d['k'] = entry.filename
  return exec_t.substitute(d).rstrip()

