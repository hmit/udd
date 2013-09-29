"""Auxillary methods for the UDD"""

import yaml
import sys
import psycopg2
from os import path
import fcntl
import re
from email.Utils import parseaddr

# If debug is something that evaluates to True, then print_debug actually prints something
debug = 0

def quote(s):
  "Quote a string for SQL and encode it to UTF-8 if it is a unicode string"
  if isinstance(s, unicode):
    s = s.encode('utf-8')
  return "'" + s.replace("\\", "\\\\").replace("'", "''") + "'"

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
  c = psycopg2.connect("dbname=" + config['general']['dbname'] + p)
  c.set_client_encoding("UTF8")
  return c

__locks = {}
def lock(config, source):
  lock_dir = config['general']['lock-dir']
  lock_path = path.join(lock_dir, source)
  f = file(lock_path, "w+")
  __locks[lock_path] = f
  try:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
  except IOError:
    print source+": lockfile found, exiting."
    exit(1)

def unlock(config, source):
  lock_dir = config['general']['lock-dir']
  lock_path = path.join(lock_dir, source)
  if lock_path in __locks:
    f = file(lock_path)
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    del __locks[lock_path]

def load_config(str):
  """Load and check configuration from the string"""
  config = yaml.safe_load(str)
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
    sys.stdout.flush()

def parse_email(str):
  """Use email.Utils to parse name and email.  Afterwards check whether it was successful and try harder to get a reasonable address"""
  name, email = parseaddr(str)
  # if no '@' is detected in email but string contains a '@' anyway try harder to get a reasonable Mail address
  if email.find('@') == -1 and str.find('@') != -1:
    email = re.sub('^[^<]+[<\(]([.\w]+@[.\w]+)[>\)].*',                  '\\1', str)
    name  = re.sub('^[^\w]*([^<]+[.\w\)\]]) *[<\(][.\w]+@[.\w]+[>\)].*', '\\1', str)
    print_debug("parse_email: %s ---> %s <%s>" % (str, name, email))
  return name, email

def validutf8(str):
  try:
    str.decode('utf-8')
    return True
  except UnicodeDecodeError:
    return False

def to_unicode(value, encoding='utf-8'):
    if isinstance(value, str):
        return value.decode(encoding)
    else:
        return unicode(value)
