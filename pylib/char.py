å­—ç¬¦é›†.py           open(self, path, fi)
           and the file handle should be set directly."""
        return 0
    
    def opendir(self, path):
        """Returns a numerical file handle."""
        return 0
    
    def read(self, path, size, offset, fh):
        """Returns a string containing the data requested."""
        raise OSError(ENOENT, '')
    
    def readdir(self, path, fh):
        """Can return either a list of names, or a list of (name, attrs, offset)
           tuples. attrs is a dict as in getattr."""
        return ['.', '..']
    
    def readlink(self, path):
        raise OSError(ENOENT, '')
    
    def release(self, path, fh):
        return 0
    
    def releasedir(self, path, fh):
        return 0
    
    def removexattr(self, path, name):
        raise OSError(ENOTSUP, '')
    
    def rename(self, old, new):
        raise OSError(EROFS, '')
    
    def rmdir(self, path):
        raise OSError(EROFS, '')
    
    def setxattr(self, path, name, value, options, position=0):
        raise OSError(ENOTSUP, '')
    
    def statfs(self, path):
        """Returns a dictionary with keys identical to the statvfs C structure
           of statvfs(3).
           On Mac OS X f_bsize and f_frsize must be a power of 2 (minimum 512)."""
        return {}
    
    def symlink(self, target, source):
        raise OSError(EROFS, '')
    
    def truncate(self, path, length, fh=None):
        raise OSError(EROFS, '')
    
    def unlink(self, path):
        raise OSError(EROFS, '')
    
    def utimens(self, path, times=None):
        """Times is a (atime, mtime) tuple. If None use current time."""
        return 0
    
    def write(self, path, data, offset, fh):
        raise OSError(EROFS, '')


class LoggingMixIn:
    def __call__(self, op, path, *args):
        logging.debug('-> %s %s %s', op, path, repr(args))
        ret = '[Unknown Error]'
        try:
            ret = getattr(self, op)(path, *args)
            return ret
        except OSError as e:
            ret = str(e)
            raise
        finally:
            logging.debug('<- %s %s', op, repr(ret))

        raise OSError(EROFS, '')
    
    def create(self, path, mode, fi=None):
        """When raw_fi is False (default case), fi is None and create should
           return a numerical file handle.
           When raw_fi is True the file handle should be set directly by create
           and return 0."""
        raise OSError(EROFS, '')
    
    def destroy(self, path):
        """Called on filesystem destruction. Path is always /"""
        pass
    
    def flush(self, path, fh):
        return 0
    
    def fsync(self, path, datasync, fh):
        return 0
    
    def fsyncdir(self, path, datasync, fh):
        return 0
    
    def getattr(self, path, fh=None):
        """Returns a dictionary with keys identical to the stat C structure
           of stat(2).
           st_atime, st_mtime and st_ctime should be floats.
           NOTE: There is an incombatibility between Linux and Mac OS X concerning
           st_nlink of directories. Mac OS X counts all files inside the directory,
           while Linux counts only the subdirectories."""
        
        if path != '/':
            raise OSError(ENOENT, '')
        return dict(st_mode=(S_IFDIR | 0o755), st_nlink=2)
    
    def getxattr(self, path, name, position=0):
        raise OSError(ENOTSUP, '')
    
    def init(self, path):
        """Called on filesystem initialization. Path is always /
           Use it instead of __init__ if you start threads on initialization."""
        pass~2· 
    def li%&·elf, target, source):
        raise OSError(EROFS, '')
 ¤ó·    def listxattA