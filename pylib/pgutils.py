from contextlib import contextmanager

@contextmanager
def savepoint(cursor, name):
  cursor.execute('savepoint %s' % name)
  try:
    yield
  except Exception:
    cursor.execute('rollback to savepoint %s' % name)
    raise
  finally:
    cursor.execute('release savepoint %s' % name)
