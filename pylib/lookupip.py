import os

from QQWry import QQWry
import ipdb
import geoip2

Q = QQWry()
D = ipdb.IPDB(ipdb.DEFAULT_FILE_LOCATION)
if os.path.exists("/var/lib/GeoIP/GeoLite2-City.mmdb"):
  G = geoip2.GeoIP2(
    "/var/lib/GeoIP/GeoLite2-City.mmdb",
    "/var/lib/GeoIP/GeoLite2-ASN.mmdb",
  )
else:
  G = geoip2.GeoIP2(
    "~/etc/data/GeoLite2-City.mmdb",
    "~/etc/data/GeoLite2-ASN.mmdb",
  )

def lookupip(ip):
  gi = G.lookup(ip)
  if gi.country_code != 'CN':
    return gi.display
  if '.' in ip:
    return ''.join(Q[ip][2:])
  else:
    return ' '.join(D.lookup(ip).info).replace('\t', ' ')
