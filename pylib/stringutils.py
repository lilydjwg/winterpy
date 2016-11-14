import re
from functools import partial

def try_singularize(word):
  # not accurate but works for most cases
  if word.endswith('ies'):
    return word[:-3] + 'y'

  if word.endswith(('les', 'tes')):
    return word[:-1]
  if word.endswith('es'):
    return word[:-2]

  if word.endswith('us'):
    return word

  if word.endswith('s'):
    return word[:-1]

  return word

_camel_to_underline_re = re.compile(r'[A-Z]')
def _camel_to_underline_replacer(m):
  if m.start() == 0:
    return m.group().lower()
  return '_' + m.group().lower()

camel_to_underline = partial(
  _camel_to_underline_re.sub,
  _camel_to_underline_replacer,
)

line_start_re = re.compile(br'(?<=\n)^(?=.)|(?<=\r)', re.MULTILINE | re.DOTALL)
def prefixer(prefix, stream):
  if isinstance(prefix, str):
    prefix = prefix.encode()
  if hasattr(stream, 'buffer'):
    stream = stream.buffer

  last_char = 0x0a

  def write(data):
    nonlocal last_char

    if not data:
      return

    if isinstance(data, str):
      data = data.encode()

    if last_char == 0x0a:
      stream.write(prefix)
    data = line_start_re.sub(prefix, data)
    last_char = data[-1]
    stream.write(data)
    stream.flush()

  return write
