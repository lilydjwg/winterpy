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

