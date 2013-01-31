'''
Latin1-encoding Translations

This class uses latin1 encoding when parsing the .mo file so that we won't encounter
fatal errors (e.g. Vim's French translation).

Just import this module and the strict GNUTranslations is replaced.

>>> T = gettext.translation('vim', localedir='/usr/share/vim/vim73/lang', languages=['fr'])
'''

import gettext

class GNUTranslations(gettext.GNUTranslations):
    def _parse(self, fp):
        """Override this method to support alternative .mo formats."""
        unpack = gettext.struct.unpack
        filename = getattr(fp, 'name', '')
        # Parse the .mo file header, which consists of 5 little endian 32
        # bit words.
        self._catalog = catalog = {}
        self.plural = lambda n: int(n != 1) # germanic plural by default
        buf = fp.read()
        buflen = len(buf)
        # Are we big endian or little endian?
        magic = unpack('<I', buf[:4])[0]
        if magic == self.LE_MAGIC:
            version, msgcount, masteridx, transidx = unpack('<4I', buf[4:20])
            ii = '<II'
        elif magic == self.BE_MAGIC:
            version, msgcount, masteridx, transidx = unpack('>4I', buf[4:20])
            ii = '>II'
        else:
            raise IOError(0, 'Bad magic number', filename)
        # Now put all messages from the .mo file buffer into the catalog
        # dictionary.
        for i in range(0, msgcount):
            mlen, moff = unpack(ii, buf[masteridx:masteridx+8])
            mend = moff + mlen
            tlen, toff = unpack(ii, buf[transidx:transidx+8])
            tend = toff + tlen
            if mend < buflen and tend < buflen:
                msg = buf[moff:mend]
                tmsg = buf[toff:tend]
            else:
                raise IOError(0, 'File is corrupt', filename)
            # See if we're looking at GNU .mo conventions for metadata
            if mlen == 0:
                # Catalog description
                lastk = k = None
                for b_item in tmsg.split('\n'.encode("ascii")):
                    # use latin1 encoding so that we won't encounter fatal errors
                    item = b_item.decode('latin1').strip()
                    if not item:
                        continue
                    if ':' in item:
                        k, v = item.split(':', 1)
                        k = k.strip().lower()
                        v = v.strip()
                        self._info[k] = v
                        lastk = k
                    elif lastk:
                        self._info[lastk] += '\n' + item
                    if k == 'content-type':
                        self._charset = v.split('charset=')[1]
                    elif k == 'plural-forms':
                        v = v.split(';')
                        plural = v[1].split('plural=')[1]
                        self.plural = c2py(plural)
            # Note: we unconditionally convert both msgids and msgstrs to
            # Unicode using the character encoding specified in the charset
            # parameter of the Content-Type header.  The gettext documentation
            # strongly encourages msgids to be us-ascii, but some applications
            # require alternative encodings (e.g. Zope's ZCML and ZPT).  For
            # traditional gettext applications, the msgid conversion will
            # cause no problems since us-ascii should always be a subset of
            # the charset encoding.  We may want to fall back to 8-bit msgids
            # if the Unicode conversion fails.
            charset = self._charset or 'ascii'
            if b'\x00' in msg:
                # Plural forms
                msgid1, msgid2 = msg.split(b'\x00')
                tmsg = tmsg.split(b'\x00')
                msgid1 = str(msgid1, charset)
                for i, x in enumerate(tmsg):
                    catalog[(msgid1, i)] = str(x, charset)
            else:
                catalog[str(msg, charset)] = str(tmsg, charset)
            # advance to next entry in the seek tables
            masteridx += 8
            transidx += 8

gettext.GNUTranslations = GNUTranslations
