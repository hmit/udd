#/usr/bin/env python
# Last-Modified: <Fri 23 May 2008 19:33:11 CEST>

from psycopg2 import connect
from debian_bundle.deb822 import Packages
import os
import syck
import sys
import gzip

archs = []
distr_id = None

def get_archs(conn):
  c = conn.cursor();
  c.execute("SELECT * from arch_ids")
  result = {}
  for row in c.fetchall():
    result[row[1]] = row[0]
  return result

def get_distr_id(conn, distr):
  c = conn.cursor();
  c.execute("SELECT distr_id from distr_ids WHERE name = '" + distr + "'")
  rows = c.fetchall()
  if len(rows) == 0:
    return None
  elif len(rows) > 1:
    print "Warning: Distribution %s exists more than once in distr_ids" % distr
  else:
    return rows[0][0]
  

def import_pkgs(file, conn):
  "Import file specified by file into database"
  try:
    for control in Packages(gzip.open(file)):
      c = conn.cursor()
      c.execute("INSERT INTO pkgs (name, distr_id, arch_id, version, src_id) VALUES ('%s', %d, %d, '%s', 0)" % (control["Package"], distr_id, archs[control["Architecture"]], control["Version"]))
  except Exception, message:
    print "Could not parse %s: %s" % (file, message)

if __name__ == '__main__':
  if len(sys.argv) != 3:
    print "Usage: %s <config> <source>" % (sys.argv[0])
    sys.exit(1)

  cfg_file = sys.argv[1]
  config = syck.load(open(cfg_file))
  if not 'dbname' in config:
    print "dbname not specified in " + cfg_file
    sys.exit(1)

  source_name = sys.argv[2]
  if not source_name in config:
    print "%s not specified in %s" % (source_name, cfg_file)
    sys.exit(1)

  source_config = config[source_name]
  conn = connect('dbname=' + config['dbname'])
  archs = get_archs(conn)
  
  dir = source_config['directory']
  distr = source_config['distribution']
  distr_id = get_distr_id(conn, distr)
  if distr_id is None:
    c = conn.cursor()
    c.execute("INSERT INTO distr_ids (name) VALUES ('%s')" % (distr))
    distr_id = get_distr_id(conn, distr)
    if distr_id is None:
      print "Error: Could not create distr_id"
      sys.exit(1)

  for part in source_config['parts']:
    for arch in source_config['archs']:
      import_pkgs(os.path.join(dir, part, 'binary-' + arch, 'Packages.gz'), conn)

  conn.commit()

