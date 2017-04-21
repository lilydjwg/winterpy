import struct
import enum
from collections import namedtuple

class AggregationType(enum.IntEnum):
  average = 1
  sum = 2
  last = 3
  max = 4
  min = 5

class WhisperMeta(namedtuple(
  'WhisperMeta', 'type max_retention x_files_factor archive_count')):
  def __eq__(self, other):
    return \
        self.type == other.type and \
        self.max_retention == other.max_retention and \
        double_to_float(self.x_files_factor) == \
          double_to_float(other.x_files_factor) and \
        self.archive_count == other.archive_count

metadata_fmt = '!2LfL'
metadata_size = struct.calcsize(metadata_fmt)

def get_metadata(fp):
  data = fp.read(metadata_size)
  d = struct.unpack(metadata_fmt, data)
  info = WhisperMeta(AggregationType(d[0]), d[1], d[2], d[3])
  return info

def set_metadata(fp, data):
  d = struct.pack(metadata_fmt, *data)
  fp.write(d)

def double_to_float(f):
  return struct.unpack("f", struct.pack("f", f))[0]
