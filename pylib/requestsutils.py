CHUNK_SIZE = 40960

def download_into(session, url, file, process_func=None):
  r = session.get(url, stream=True)
  length = int(r.headers.get('Content-Length') or 0)
  received = 0
  for chunk in r.iter_content(CHUNK_SIZE):
    received += len(chunk)
    file.write(chunk)
    if process_func:
      process_func(received, length)
  if not length and process_func:
    process_func(received, received)

def download_into_with_progressbar(url, dest):
  import time
  from functools import partial
  import requests
  from termutils import download_process, get_terminal_size

  w = get_terminal_size()[1]
  with open(argv[2], 'wb') as f:
    download_into(requests, argv[1], f, partial(
      download_process, argv[2], time.time(), width=w))

if __name__ == '__main__':
  from sys import argv, exit

  if len(argv) != 3:
    exit('URL and output file not given.')

  try:
    download_into_with_progressbar(argv[1], argv[2])
  except KeyboardInterrupt:
    exit(2)
