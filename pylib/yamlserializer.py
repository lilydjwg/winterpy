#!/usr/bin/env python3
# vim:fileencoding=utf-8

from serializer import Serializer, SerializerError

import yaml
try:
  from yaml import CLoader as Loader
  from yaml import CDumper as Dumper
except ImportError:
  from yaml import Loader, Dumper

def load(src):
  return yaml.load(src, Loader=Loader)

def dump(data, stream=None):
  return yaml.dump(data, stream=stream, Dumper=Dumper,
                   allow_unicode=True, default_flow_style=False)

class YAMLData(Serializer):
  def save(self):
    dump(self.data, open(self.fname, 'w'))

  def load(self):
    self.data = load(open(self.fname, 'r'))

