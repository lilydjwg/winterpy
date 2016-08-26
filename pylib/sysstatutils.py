from collections import defaultdict

def read_iostat(f):
  # data[sdc][rrqm/s] = list
  data = defaultdict(lambda: defaultdict((list)))

  fields = []
  for l in f:
    if l.startswith('Device:'):
      fields = l.split()[1:]
    elif not l.strip():
      fields = None
    elif fields:
      device, *values = l.split()
      for field, value in zip(fields, values):
        data[device][field].append(value)

  return data

