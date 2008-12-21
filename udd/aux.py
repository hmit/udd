"""Auxillary methods for the UDD"""

import syck
import sys
import psycopg2
from os import path
import fcntl

# If debug is something that evaluates to True, then print_debug actually prints something
debug = 0

def quote(s):
  "Quote a string for SQL"
  return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"

def null_or_quote(dict, key):
  "If key is an element of dict, return it quoted. Return NULL otherwise"
  if key in dict:
    return quote(dict[key])
  else:
    return 'NULL'

class ConfigException(Exception):
  def __init__(self, message):
    Exception(self)
    self.message = message

  def __str__(self):
    return "ConfigException: " + self.message

def open_connection(config):
  """Open the connection to the database and return it"""
  if 'dbport' in config['general']:
    p = " port=" + str(config['general']['dbport'])
  else:
    p = ""
  return psycopg2.connect("dbname=" + config['general']['dbname'] + p)

__locks = {}
def lock(config, source):
  lock_dir = config['general']['lock-dir']
  lock_path = path.join(lock_dir, source)
  f = file(lock_path, "w+")
  __locks[lock_path] = f
  fcntl.flock(f.fileno(), fcntl.LOCK_EX)

def unlock(config, source):
  lock_dir = config['general']['lock-dir']
  lock_path = path.join(lock_dir, source)
  if lock_path in __locks:
    f = file(lock_path)
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    del __locks[lock_path]

def load_config(str):
  """Load and check configuration from the string"""
  config = syck.load(str)
  if not 'general' in config:
    raise ConfigException('general section not specified')
  
  general = config['general']
  for k in ['dbname', 'archs', 'types', 'lock-dir']:
    if not k in general:
      raise ConfigException(k + ' not specified in node "general"')
  if not 'debug' in general:
    general['debug'] = 0

  # Check that the source-entries are well-formed
  for name in config:
    if name == 'general':
      continue

    src = config[name]
    if not 'type' in src:
      raise ConfigException('type not specified for "%s"' % name)
    if src['type'] not in general['types']:
      raise ConfigException('Type of %s not specified in types' % name)

  return config

def print_debug(*args):
  "Print arguments to stdout if debug is set to something that evaluates to true"
  if debug:
    sys.stdout.write(*args)
    sys.stdout.write("\n")
