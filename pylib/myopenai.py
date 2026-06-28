import json

def print_streaming_response(r):
  ret = []
  if r.headers['Content-Type'] == 'text/event-stream':
    for line in r.iter_lines():
      if not line:
        continue

      line = line.removeprefix('data: ')
      if line == '[DONE]':
        break

      data = json.loads(line)
      for m in data['choices']:
        if (d := m['delta']) and (c := d.get('content', d.get('reasoning_content'))):
          print(c, end='', flush=True)
          ret.append(c)

  else:
    r.read()
    raise Exception(r.text)

  print()
  return ret

PROMPT = "\001\033[95m\002LLM>> \001\033[0m\002"

def interact(client, url, model, messages):
  import readline
  readline.parse_and_bind('set enable-bracketed-paste on')
  while True:
    try:
      prompt = input(PROMPT).strip()
    except EOFError:
      print()
      break
    if not prompt:
      continue

    messages.append({
      'role': 'user',
      'content': prompt,
    })
    j = {
      'model': model,
      'messages': messages,
      'reasoning_effort': 'minimal',
      'stream': True,
    }
    with client.stream('POST', url, json=j, timeout=120) as r:
      res = print_streaming_response(r)
      messages.append({
        'role': 'assistant',
        'content': ''.join(res),
      })
