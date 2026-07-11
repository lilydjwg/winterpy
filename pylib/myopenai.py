import argparse
import os
import json
from contextlib import AbstractContextManager
from typing import Literal, Any, get_args

import httpx

def print_streaming_response(r: httpx.Response) -> list[str]:
  ret = []
  if r.headers['Content-Type'].split(';', 1)[0] == 'text/event-stream':
    thinking = False

    for line in r.iter_lines():
      if not line:
        continue

      line = line.removeprefix('data: ')
      if line == '[DONE]':
        break

      data = json.loads(line)
      for m in data['choices']:
        if d := m['delta']:
          if c := d.get('content'):
            if thinking:
              print('\n</think>')
              thinking = False
          elif c := d.get('reasoning_content'):
            if not thinking:
              print('<think>')
              thinking = True
          else:
            continue

          print(c, end='', flush=True)
          ret.append(c)

  else:
    r.read()
    raise Exception(r.text)

  print()
  return ret

PROMPT = "\001\033[95m\002LLM>> \001\033[0m\002"

def interact(client, url, model, messages, extra_args={}):
  import readline
  readline.parse_and_bind('set enable-bracketed-paste on')
  while True:
    try:
      prompt = input(PROMPT).strip()
    except EOFError:
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
      'stream': True,
    }
    j.update(extra_args)
    with client.stream('POST', url, json=j, timeout=120) as r:
      res = print_streaming_response(r)
      messages.append({
        'role': 'assistant',
        'content': ''.join(res),
      })

API_TYPE = Literal['local', 'gemini', 'opencode']
API_CHOICES = get_args(API_TYPE)
API_ENDPOINTS: dict[API_TYPE, str] = {
  'local': 'http://127.0.0.1:8080/v1/chat/completions',
  'gemini': 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
  'opencode': 'https://opencode.ai/zen/go/v1/chat/completions',
}
Messages = list[dict[str, Any]]

class Client:
  def __init__(self, api: API_TYPE, model: str) -> None:
    self.url = API_ENDPOINTS[api]
    self.model = model
    self.api = api

    if api == 'gemini':
      headers = {
        'Authorization': f'Bearer {os.environ['GEMINI_API_KEY']}',
      }
    elif api == 'opencode':
      headers = {
        'Authorization': f'Bearer {os.environ['OPENCODE_API_KEY']}',
      }
    else:
      headers = {}
    self.client = httpx.Client(http2=True, headers=headers)

  def stream(
    self,
    messages: Messages,
    *,
    disable_thinking: bool = True,
    extra: dict[str, Any] | None = None,
  ) -> AbstractContextManager[httpx.Response]:
    j = self._get_request_json(
      messages,
      streaming = True,
      disable_thinking = disable_thinking,
      extra = extra,
    )
    return self.client.stream('POST', self.url, json=j, timeout=120)

  def request(
    self,
    messages: Messages,
    *,
    disable_thinking: bool = True,
    extra: dict[str, Any] | None = None,
  ) -> httpx.Response:
    j = self._get_request_json(
      messages,
      streaming = False,
      disable_thinking = disable_thinking,
      extra = extra,
    )
    return self.client.post(self.url, json=j, timeout=120)

  def _get_request_json(
    self,
    messages: Messages,
    *,
    streaming: bool,
    disable_thinking: bool = True,
    extra: dict[str, Any] | None = None,
  ) -> dict[str, Any]:
    j = {
      'model': self.model,
      'messages': messages,
      'stream': streaming,
    }

    if disable_thinking:
      j.update(self._disable_thinking_args())

    if extra:
      j.update(extra)

    return j

  def _disable_thinking_args(self) -> dict[str, Any]:
    j: dict[str, Any] = {}
    if self.api == 'local':
      j['chat_template_kwargs'] = {'enable_thinking': False}
    elif self.api == 'gemini':
      j['reasoning_effort'] = 'minimal'
    elif self.api == 'opencode':
      j['enable_thinking'] = False # glm-5.2
      j['thinking'] = {'type': 'disabled'} # deepseek-v4-flash

    return j

  def interact(self, messages: Messages) -> None:
    extra = self._disable_thinking_args()
    interact(self.client, self.url, self.model, messages, extra)

  @staticmethod
  def add_common_argument(
    parser: argparse.ArgumentParser,
    *,
    default_api: API_TYPE,
  ):
    parser.add_argument('-m', '--model',
                        help='name of model to use')
    parser.add_argument('--api', choices=API_CHOICES,
                        default=default_api,
                        help=f'API service to use. [default: {default_api}]')

def set_process_name(title: str) -> None:
  try:
    import setproctitle
    setproctitle.setproctitle(title)
  except ImportError:
    pass
