import sys
import logging

from pyxmpp2.jid import JID
from pyxmpp2.message import Message
from pyxmpp2.presence import Presence
from pyxmpp2.client import Client
from pyxmpp2.settings import XMPPSettings
from pyxmpp2.interfaces import EventHandler, event_handler, QUIT
from pyxmpp2.streamevents import AuthorizedEvent, DisconnectedEvent
from pyxmpp2.interfaces import XMPPFeatureHandler
from pyxmpp2.interfaces import presence_stanza_handler, message_stanza_handler
from pyxmpp2.ext.version import VersionProvider

class XMPPBot(EventHandler, XMPPFeatureHandler):
  def __init__(self, my_jid, settings, **kwargs):
    version_provider = VersionProvider(settings)
    self.client = Client(my_jid, [self, version_provider], settings, **kwargs)
    self.connect = self.client.connect
    self.disconnect = self.client.disconnect
    self.run = self.client.run
    self.roster = self.client.roster

  @message_stanza_handler()
  def handle_message(self, stanza):
    if stanza.stanza_type.endswith('chat') and stanza.body:
      logging.info("%s said: %s", stanza.from_jid, stanza.body)
    else:
      logging.info("%s message: %s", stanza.from_jid, stanza.serialize())
    return True

  def send_message(self, receiver, msg):
    m = Message(
      stanza_type = 'chat',
      from_jid = self.client.jid,
      to_jid = receiver,
      body = msg,
    )
    self.send(m)

  def send(self, stanza):
    self.client.stream.send(stanza)

  @presence_stanza_handler("subscribe")
  def handle_presence_subscribe(self, stanza):
    logging.info("{0} requested presence subscription"
                          .format(stanza.from_jid))
    presence = Presence(to_jid = stanza.from_jid.bare(),
                          stanza_type = "subscribe")
    return [stanza.make_accept_response(), presence]

  @presence_stanza_handler("subscribed")
  def handle_presence_subscribed(self, stanza):
    logging.info("{0!r} accepted our subscription request"
                          .format(stanza.from_jid))
    return True

  @presence_stanza_handler("unsubscribe")
  def handle_presence_unsubscribe(self, stanza):
    logging.info("{0} canceled presence subscription"
                          .format(stanza.from_jid))
    presence = Presence(to_jid = stanza.from_jid.bare(),
                          stanza_type = "unsubscribe")
    return [stanza.make_accept_response(), presence]

  @presence_stanza_handler("unsubscribed")
  def handle_presence_unsubscribed(self, stanza):
    logging.info("{0!r} acknowledged our subscrption cancelation"
                          .format(stanza.from_jid))
    return True

  @presence_stanza_handler()
  def handle_presence_available(self, stanza):
    logging.info('%s[%s]', stanza.from_jid, stanza.show or 'available')
    return True

  @event_handler(DisconnectedEvent)
  def handle_disconnected(self, event):
    """Quit the main loop upon disconnection."""
    return QUIT

  @event_handler()
  def handle_all(self, event):
    """Log all events."""
    logging.info("-- {0}".format(event))

def main():
  import os
  from getpass import getpass
  import argparse
  from myutils import enable_pretty_logging
  from cli import repl

  """Parse the command-line arguments and run the bot."""
  parser = argparse.ArgumentParser(description = 'XMPP echo bot',
                  parents = [XMPPSettings.get_arg_parser()])
  parser.add_argument('jid', metavar = 'JID',
                    help = 'The bot JID')
  parser.add_argument('--debug',
            action = 'store_const', dest = 'log_level',
            const = logging.DEBUG, default = logging.INFO,
            help = 'Print debug messages')
  parser.add_argument('--quiet', const = logging.ERROR,
            action = 'store_const', dest = 'log_level',
            help = 'Print only error messages')
  parser.add_argument('--trace', action = 'store_true',
            help = 'Print XML data sent and received')

  args = parser.parse_args()
  settings = XMPPSettings({
              "software_name": "pyxmpp2 Bot"
              })
  settings.load_arguments(args)

  if settings.get("password") is None:
    password = getpass("{0!r} password: ".format(args.jid))
    settings["password"] = password

  if args.trace:
    logging.info('enabling trace')
    for logger in ("pyxmpp2.IN", "pyxmpp2.OUT"):
      logger = logging.getLogger(logger)
      logger.setLevel(logging.DEBUG)

  enable_pretty_logging(level=args.log_level)
  root = logging.getLogger()
  root.handlers[0].setFormatter(root.handlers[1].formatter)
  del root.handlers[1]
  del root

  bot = XMPPBot(JID(args.jid), settings)

  q = sys.exit
  self = bot

  try:
    bot.connect()
    while True:
      try:
        bot.run()
      except KeyboardInterrupt:
        v = vars()
        v.update(globals())
        repl(v, os.path.expanduser('~/.xmppbot_history'))
  except SystemExit:
    bot.disconnect()
    bot.run(timeout=2)
  except:
    bot.disconnect()
    bot.run(timeout=2)
    import traceback
    traceback.print_exc()

if __name__ == '__main__':
  main()
