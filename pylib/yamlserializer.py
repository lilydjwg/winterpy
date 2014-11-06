from serializer import Serializer, SerializerError
from yamlutils import load, dump
from myutils import safe_overwrite

class YAMLData(Serializer):
  def save(self):
    data = dump(self.data)
    safe_overwrite(self.fname, data)

  def load(self):
    self.data = load(open(self.fname, 'r'))

