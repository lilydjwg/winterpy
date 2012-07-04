import sys
import logging
from xml.etree import ElementTree as ET

from pyxmpp2.jid import JID
from pyxmpp2.message import Message
from pyxmpp2.presence import Presence
from pyxmpp2.client import Client
from pyxmpp2.settings import XMPPSettings
from pyxmpp2.interfaces import EventHandler, event_handler, QUIT, NO_CHANGE
from pyxmpp2.streamevents import AuthorizedEvent, DisconnectedEvent
from pyxmpp2.interfaces import XMPPFeatureHandler
from pyxmpp2.interfaces import presence_stanza_handler, message_stanza_handler
from pyxmpp2.ext.version import VersionProvider
from pyxmpp2.iq import Iq

class AutoAcceptMixin:
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


class XMPPBot(EventHandler, XMPPFeatureHandler):
  autoReconnect = True

  def __init__(self, my_jid, settings, autoReconnect=None, main_loop=None):
    self.jid = my_jid
    self.settings = settings
    if autoReconnect is not None:
      self.autoReconnect = autoReconnect
    self.do_quit = False
    self.main_loop = main_loop

  def newclient(self):
    version_provider = VersionProvider(self.settings)
    self.client = Client(
      self.jid, [self, version_provider], self.settings,
      main_loop=self.main_loop,
    )

  def start(self):
    while not self.do_quit:
      self.newclient()
      self.client.connect()
      self.client.run()
      if not self.autoReconnect:
        self.do_quit = True

  def disconnect(self):
    self.do_quit = True
    self.client.disconnect()
    self.client.run(timeout=2)

  @property
  def roster(self):
    return self.client.roster

  @message_stanza_handler()
  def handle_message(self, stanza):
    if stanza.stanza_type and stanza.stanza_type.endswith('chat') and stanza.body:
      logging.info("%s said: %s", stanza.from_jid, stanza.body)
      self.last_chat_message = stanza
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

  def delayed_call(self, seconds, func, *args, **kwargs):
    self.client.main_loop.delayed_call(seconds, partial(func, *args, **kwargs))

  def get_vcard(self, jid, callback):
    '''callback is used as both result handler and error handler'''
    q = Iq(
      to_jid = jid.bare(),
      stanza_type = 'get'
    )
    vc = ET.Element("{vcard-temp}vCard")
    q.add_payload(vc)
    self.stanza_processor.set_response_handlers(q, callback, callback)
    self.send(q)

  def update_roster(self, jid, name=NO_CHANGE, groups=NO_CHANGE):
    self.client.roster_client.update_item(jid, name, groups)

  @presence_stanza_handler()
  def handle_presence_available(self, stanza):
    logging.info('%s[%s]', stanza.from_jid, stanza.show or 'available')
    return True

  @event_handler(DisconnectedEvent)
  def handle_disconnected(self, event):
    if self.do_quit:
      return QUIT
    else:
      logging.warn('XMPP disconnected. Reconnecting...')
      # We can't restart here because the stack will overflow
      return True

  @event_handler()
  def handle_all(self, event):
    """Log all events."""
    logging.info("-- {0}".format(event))

class AutoAcceptBot(AutoAcceptMixin, XMPPBot): pass

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
  if args.jid.endswith('@gmail.com'):
    settings['starttls'] = True
    settings['tls_verify_peer'] = False

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

  bot = AutoAcceptBot(JID(args.jid), settings)

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
  except:
    bot.disconnect()
    import traceback
    traceback.print_exc()

if __name__ == '__main__':
  main()
