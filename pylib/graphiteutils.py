import socket
import logging

logger = logging.getLogger(__name__)

class Graphite:
  def __init__(self, host, port=2003):
    self.host = host
    self.port = port
    self._connect()

  def _connect(self):
    self.sock = socket.socket()
    self.sock.connect((self.host, self.port))

  def send_stats(self, data):
    logger.info('sending %d metrics to Graphite %s:%s',
                len(data), self.host, self.port)
    data = [x.encode() + b'\n' for x in data]
    data = b''.join(data)
    try:
      self.sock.sendall(data)
    except ConnectionResetError:
      # retry e.g. server has restarted
      self._connect()
      self.sock.sendall(data)
