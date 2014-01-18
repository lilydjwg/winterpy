#
# (C) Copyright 2014 lilydjwg <lilydjwg@gmail.com>
#

"""Message Delivery Receipts

Normative reference:
  - `XEP-0184 <http://xmpp.org/extensions/xep-0184.html>`__
"""

from __future__ import absolute_import, division

__docformat__ = "restructuredtext en"

import platform
import logging

from pyxmpp2.etree import ElementTree as ET

from pyxmpp2.message import Message
from pyxmpp2.interfaces import XMPPFeatureHandler, feature_uri
from pyxmpp2.interfaces import message_stanza_handler

logger = logging.getLogger(__name__)

NS = "urn:xmpp:receipts"

@feature_uri(NS)
class ReceiptSender(XMPPFeatureHandler):
    """Provides the Message Delivery Receipts (XEP-0184) response service."""
    stream = None

    @message_stanza_handler()
    def handle_receipt_request(self, stanza):
        if not self.stream:
            return

        mid = stanza.stanza_id
        if mid:
            x = stanza.get_xml()
            if x.find('{%s}request' % NS) is None:
                # not requested
                return
            response = Message(to_jid = stanza.from_jid)
            payload = ET.Element("{%s}received" % NS, {'id': mid})
            response.set_payload(payload)
            self.stream.send(response)
        # keep handling it
        return False

