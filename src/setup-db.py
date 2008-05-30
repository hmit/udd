#!/usr/bin/env python
# Last-Modified: <Thu May 29 20:47:58 2008>
# Starting from an empty database, create the necessary tables

from psycopg2 import connect
import syck
import sys

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print "Usage: %s <udd config file>" % (sys.argv[0])
    sys.exit(1)

  # Load configuration
  config = syck.load(open(sys.argv[1]).read())
  # Check configuration
  if not 'dbname' in config:
    print "dbname not specified in" + sys.argv[1]
    sys.exit(1)
  if not 'archs' in config:
    print 'archs not specified in' + sys.argv[1]
    sys.exit(1)

  connection = connect("dbname = " + config['dbname'])
  
  # Create tables
  cursor = connection.cursor()
  cursor.execute("CREATE TABLE pkgs (pkg_id serial, name text, distr_id int, arch_id int, version text, src_id int);")
  cursor.execute("CREATE TABLE sources (src_id serial, name text, upload_date timestamp, uploader_key int, maintainer int, build_archs int, version text, distr_id int);")
  cursor.execute("CREATE TABLE distr_ids (distr_id serial, name text);")
  cursor.execute("CREATE TABLE arch_ids (arch_id serial, name text);")
  # TODO: Add carnivore

  #Setup architecture table
  for arch in config['archs']:
    cursor.execute("INSERT INTO arch_ids (name) VALUES ('%s');" % (arch))

  connection.commit()

