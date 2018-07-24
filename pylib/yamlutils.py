from collections import OrderedDict

import yaml
try:
  from yaml import CLoader as Loader
  from yaml import CDumper as Dumper
except ImportError:
  from yaml import Loader, Dumper

def load(src):
  return yaml.load(src, Loader=Loader)

def load_all(src):
  return yaml.load_all(src, Loader=Loader)

class PrettyDumper(Dumper): pass

def dump(data, stream=None, **kwargs):
  mykwargs = {
    'allow_unicode': True,
    'default_flow_style': False,
  }
  mykwargs.update(kwargs)
  return yaml.dump(data, stream=stream, Dumper=PrettyDumper, **mykwargs)

def represent_multiline_str(self, data):
  style = '|' if '\n' in data else None
  return self.represent_scalar(
    'tag:yaml.org,2002:str', data, style=style)

def _represent_mapping(self, data):
  return self.represent_mapping(
    'tag:yaml.org,2002:map', data.items())

PrettyDumper.add_representer(str, represent_multiline_str)
PrettyDumper.add_representer(OrderedDict, _represent_mapping)

def represent_this_key_first_dict(key, self, data):
  '''
  usage:

  yamlutils.Dumper.add_representer(
    dict, partial(yamlutils.represent_this_key_first_dict, 'name'))
  '''
  value = []
  if key in data:
    node_key = self.represent_data(key)
    node_value = self.represent_data(data[key])
    value.append((node_key, node_value))

  for k, v in data.items():
    if k == key:
      continue
    node_key = self.represent_data(k)
    node_value = self.represent_data(v)
    value.append((node_key, node_value))

  return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)

def edit_as_yaml(doc, editor='vim'):
  import tempfile
  import subprocess
  import os
  import time

  with tempfile.NamedTemporaryFile(
    mode='w+', encoding='utf-8', suffix='.yaml', delete=False) as f:
    name = f.name
    try:
      dump(doc, f)
      f.close()
      now = time.time()
      subprocess.check_call([editor, '--', name])
      st = os.stat(name)
      if st.st_mtime > now:
        with open(name, 'r', encoding='utf-8') as f:
          return load(f)
      else:
        return doc
    finally:
      os.unlink(name)

def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
  # https://stackoverflow.com/a/21912744/296473
  class OrderedLoader(Loader):
    pass

  def construct_mapping(loader, node):
    loader.flatten_mapping(node)
    return object_pairs_hook(loader.construct_pairs(node))

  OrderedLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_mapping)

  return yaml.load(stream, OrderedLoader)
