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
