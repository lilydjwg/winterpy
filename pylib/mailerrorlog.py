import logging
from typing import Tuple, Deque
from collections import deque
from collections.abc import Sequence
import threading
from queue import Queue, Empty, Full
import sys

from mailutils import assemble_mail, sendmail

class LogMailSender(threading.Thread):
  name = "LogMailSender"
  daemon = True

  def __init__(
    self,
    queue: Queue,
    handler: LocalSMTPHandler,
    fromaddr: str,
    toaddrs: list[str],
    /,
    tag: str,
    delay: int,
    *,
    max_num: int = 10,
  ) -> None:
    super().__init__()
    self.fromaddr = fromaddr
    if isinstance(toaddrs, str):
      toaddrs = [toaddrs]
    self.toaddrs = toaddrs
    self.tag = tag
    self.delay = delay

    self.last_mail_time = 0.0
    self.deque: Deque[logging.LogRecord] = deque(maxlen = max_num)

    self.queue = queue
    self.handler = handler

  def run(self):
    while True:
      try:
        self.run_one()
      except Exception:
        # unrecoverable error, drop logs and keep the queue running
        print('Error sending logs via SMTP:', file=sys.stderr)
        import traceback
        traceback.print_exc()
        self.deque.clear()

  def run_one(self):
    try:
      record = self.queue.get(timeout=self.delay)
      self.deque.append(record)
      if len(self.deque) < self.deque.maxlen:
        return
    except Empty:
      pass

    if not self.deque:
      return

    subject, body = self.format_as_mail(self.deque)
    mail = assemble_mail(
      f'[{self.tag}] {subject}',
      self.toaddrs,
      self.fromaddr,
      text = body,
    )
    sendmail(mail)
    self.deque.clear()

  def format_as_mail(self, records: Sequence[logging.LogRecord]) -> Tuple[str, str]:
    if len(records) == 1:
      subject = 'An error occurred: %s' % records[0].getMessage()
    else:
      subject = '%d errors occurred' % len(records)

    ret = []

    for record in records:
      formatted = self.handler.format(record)
      ret.append(formatted)

    return subject, '\n'.join(ret) + '\n'

class LocalSMTPHandler(logging.Handler):
  def __init__(
    self,
    fromaddr: str,
    toaddrs: list[str],
    /,
    tag: str,
    delay: int,
    *,
    max_num: int = 10,
  ) -> None:
    super().__init__()
    self.queue: Queue[logging.LogRecord] = Queue(maxsize=1)

    self.worker = LogMailSender(
      self.queue, self,
      fromaddr, toaddrs,
      tag = tag, delay = delay, max_num = max_num,
    )
    self.worker.start()

  def emit(self, record: logging.LogRecord) -> None:
    try:
      # don't block indefinitely here even the sender thread dies
      self.queue.put(record, timeout=0.1)
    except Full:
      print('SMTP logs queue full, log lost', file=sys.stderr)
