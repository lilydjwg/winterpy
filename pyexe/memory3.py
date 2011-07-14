#!/usr/bin/env python3

# taken from http://code.google.com/p/fusepy/

from fuse3 import FUSE, Operations, LoggingMixIn

from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from sys import argv, exit
from time import time

import os
import logging


class Memory(LoggingMixIn, Operations):
    """Example memory filesystem. Supports only one level of files."""
    
    def __init__(self):
        self.files = {}
        self.data = defaultdict(bytearray)
        self.fd = 0
        now = time()
        self.files[b'/'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now,
            st_mtime=now, st_atime=now, st_nlink=2)
        
    def chmod(self, path, mode):
        self.files[path]['st_mode'] &= 0o770000
        self.files[path]['st_mode'] |= mode
        return 0

    def chown(self, path, uid, gid):
        self.files[path]['st_uid'] = uid
        self.files[path]['st_gid'] = gid
    
    def create(self, path, mode):
        self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1,
            st_size=0, st_ctime=time(), st_mtime=time(), st_atime=time())
        self.fd += 1
        return self.fd
    
    def getattr(self, path, fh=None):
        if path not in self.files:
            raise OSError(ENOENT, '')
        st = self.files[path]
        return st
    
    def getxattr(self, path, name, position=0):
        attrs = self.files[path].get('attrs', {})
        try:
            return attrs[name]
        except KeyError:
            return b''       # Should return ENOATTR
    
    def listxattr(self, path):
        attrs = self.files[path].get('attrs', {})
        return attrs.keys()
    
    def mkdir(self, path, mode):
        self.files[path] = dict(st_mode=(S_IFDIR | mode), st_nlink=2,
                st_size=0, st_ctime=time(), st_mtime=time(), st_atime=time())
        self.files[b'/']['st_nlink'] += 1
    
    def open(self, path, flags):
        self.fd += 1
        return self.fd
    
    def read(self, path, size, offset, fh):
        return bytes(self.data[path][offset:offset + size])
    
    def readdir(self, path, fh):
        return [b'.', b'..'] + [x[len(path):].lstrip(b'/') for x in self.files \
                                if x != path and x.startswith(path) \
                                and b'/' not in x[len(path):].lstrip(b'/')
                               ]
    
    def readlink(self, path):
        return self.data[path].decode('utf-8')
    
    def removexattr(self, path, name):
        attrs = self.files[path].get('attrs', {})
        try:
            del attrs[name]
        except KeyError:
            pass        # Should return ENOATTR
    
    def rename(self, old, new):
        self.files[new] = self.files.pop(old)
    
    def rmdir(self, path):
        self.files.pop(path)
        self.files[b'/']['st_nlink'] -= 1
    
    def setxattr(self, path, name, value, options, position=0):
        # Ignore options
        attrs = self.files[path].setdefault('attrs', {})
        attrs[name] = value
    
    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)
    
    def symlink(self, target, source):
        source = source.encode('utf-8')
        self.files[target] = dict(st_mode=(S_IFLNK | 0o777), st_nlink=1,
            st_size=len(source))
        self.data[target] = bytearray(source)
    
    def truncate(self, path, length, fh=None):
        del self.data[path][length:]
        self.files[path]['st_size'] = length
    
    def unlink(self, path):
        self.files.pop(path)
    
    def utimens(self, path, times=None):
        now = time()
        atime, mtime = times if times else (now, now)
        self.files[path]['st_atime'] = atime
        self.files[path]['st_mtime'] = mtime
    
    def write(self, path, data, offset, fh):
        del self.data[path][offset:]
        self.data[path].extend(data)
        self.files[path]['st_size'] = len(self.data[path])
        return len(data)


if __name__ == "__main__":
    if len(argv) != 2:
        print('usage: %s <mountpoint>' % os.path.split(argv[0])[1])
        exit(1)
    logging.getLogger().setLevel(logging.DEBUG)
    fuse = FUSE(Memory(), argv[1], foreground=True)
