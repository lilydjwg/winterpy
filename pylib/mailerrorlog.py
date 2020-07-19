from __future__ import annotations

import logging
from typing import List, Tuple, Deque
from collections import deque
from collections.abc import Sequence
import time

from mailutils import assemble_mail, sendmail

class LocalSMTPHandler(logging.Handler):
  def __init__(
    self,
    fromaddr: str,
    toaddrs: List[str],
    /,
    tag: str,
    min_gap_seconds: int,
    *,
    max_num: int = 10,
  ) -> None:
    super().__init__()
    self.fromaddr = fromaddr
    if isinstance(toaddrs, str):
      toaddrs = [toaddrs]
    self.toaddrs = toaddrs
    self.tag = tag
    self.min_gap_seconds = min_gap_seconds

    self.last_mail_time = 0.0
    self.deque: Deque[logging.LogRecord] = deque(maxlen = max_num)

  def emit(self, record: logging.LogRecord) -> None:
    self.deque.append(record)

    t = time.time()
    if t <= self.last_mail_time + self.min_gap_seconds:
      return

    subject, body = self.format_as_mail(self.deque)
    try:
      mail = assemble_mail(
        f'[{self.tag}] {subject}',
        self.toaddrs,
        self.fromaddr,
        text = body,
      )
      sendmail(mail)
      self.deque.clear()
      self.last_mail_time = t
    except Exception:
      self.handleError(record)

  def format_as_mail(self, records: Sequence[logging.LogRecord]) -> Tuple[str, str]:
    if len(records) == 1:
      subject = 'An error occurred: %s' % records[0].getMessage()
    else:
      subject = '%d errors occurred' % len(records)

    ret = []

    for record in records:
      formatted = self.format(record)
      ret.append(formatted)

    return subject, '\n'.join(ret) + '\n'

