"""Auxillary methods for the UDD"""

import syck
import sys

# If debug is something that evaluates to True, then print_debug actually prints something :)
debug = 0

def get_archs(conn):
  """Return a dicitionary, mapping from architecture names to their ids.

  This mapping is retrivied from the connection <conn>"""
  cur = conn.cursor()
  cur.execute("SELECT * from arch_ids")
  result = {}
  for row in cur.fetchall():
    result[row[1]] = row[0]
  return result

def get_distrs(conn):
  """Return a dicitionary, mapping from distribution names to their ids.

  This mapping is retrivied from the connection <conn>"""
  cur = conn.cursor()
  cur.execute("SELECT * from distr_ids")
  result = {}
  for row in cur.fetchall():
    result[row[1]] = row[0]
  return result

class ConfigException(Exception):
  def __init__(self, message):
    Exception(self)
    self.message = message

  def __str__(self):
    return "ConfigException: " + self.message

def load_config(seq):
  """Load and check configuration from seq"""
  config = syck.load(seq)
  if not 'dbname' in config:
    raise ConfigException('dbname not specified')

  if not 'archs' in config:
    raise ConfigException('archs not specified')

  if not 'types' in config:
    raise ConfigException('types not specified')

  if not 'debug' in config:
    config['debug'] = 0

  # Check that the source-entries are well-formed
  for name in config:
    if name in ('dbname', 'archs', 'types', 'debug'):
      continue

    src = config[name]
    if not 'type' in src:
      raise ConfigException('type not specified for "%s"' % name)
    if src['type'] not in config['types']:
      raise ConfigException('Type of %s not specified in types' % name)

  return config

def insert_distr(conn, distr_name):
  "Insert distribution <distr_name> into DB"
  cur = conn.cursor()
  cur.execute("INSERT INTO distr_ids (name) VALUES ('%s')" % distr_name)

def print_debug(*args):
  "Print arguments to stdout if debug is set to something that evaluates to true"
  if debug:
    sys.stdout.write(*args)
    sys.stdout.write("\n")

class BufferedLineReader:
  """Provides an iterator over the input of the specified file."""
  def __init__(self, file, cache_size):
    self.cache_size = cache_size
    self.file = file

  def __iter__(self):
    while True:
      lines = self.file.readlines(self.cache_size)
      if len(lines) == 0:
	break
      for line in lines:
	yield line

