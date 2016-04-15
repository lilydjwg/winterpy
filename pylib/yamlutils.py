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

def dump(data, stream=None, **kwargs):
  mykwargs = {
    'allow_unicode': True,
    'default_flow_style': False,
  }
  mykwargs.update(kwargs)
  return yaml.dump(data, stream=stream, Dumper=Dumper, **mykwargs)

def represent_multiline_str(self, data):
  style = '|' if '\n' in data else None
  return self.represent_scalar(
    'tag:yaml.org,2002:str', data, style=style)

Dumper.add_representer(str, represent_multiline_str)

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
