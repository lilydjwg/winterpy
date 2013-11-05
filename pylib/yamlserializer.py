from serializer import Serializer, SerializerError
from yamlutils import load, dump

class YAMLData(Serializer):
  def save(self):
    dump(self.data, open(self.fname, 'w'))

  def load(self):
    self.data = load(open(self.fname, 'r'))

