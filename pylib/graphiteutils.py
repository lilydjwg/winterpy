import socket
import logging

logger = logging.getLogger(__name__)

class Graphite:
  def __init__(self, host, port=2003):
    self.host = host
    self.port = port
    self.sock = sock = socket.socket()
    sock.connect((host, port))

  def send_stats(self, data):
    logger.info('sending %d metrics to Graphite %s:%s',
                len(data), self.host, self.port)
    data = [x.encode() + b'\n' for x in data]
    data = b''.join(data)
    self.sock.sendall(data)
