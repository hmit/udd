#!/usr/bin/python

import aux
import sys

"""This scripts sets up and deletes the tables of the database"""

TABLES = ('sources', 'pkgs', 'distr_ids', 'arch_ids')

def print_help():
  print "Usage: %s <config> <delete|setup>" % sys.argv[0]

def delete(conn):
  c = conn.cursor()

  for t in TABLES:
    c.execute("DROP TABLE " + t)

def setup(conn, config):
  c = conn.cursor()
  c.execute("CREATE TABLE pkgs (pkg_id serial, name text, distr_id int, arch_id int, version text, src_id int);")
  c.execute("CREATE TABLE sources (src_id serial, name text, upload_date timestamp, uploader_key int, maintainer int, build_archs int, version text, distr_id int);")
  c.execute("CREATE TABLE distr_ids (distr_id serial, name text);")
  c.execute("CREATE TABLE arch_ids (arch_id serial, name text);")

  #Setup architecture table
  for arch in config['general']['archs']:
    c.execute("INSERT INTO arch_ids (name) VALUES ('%s');" % (arch))

def main():
  if len(sys.argv) != 3:
    print_help()
    sys.exit(1)

  command = sys.argv[2]
  config_path = sys.argv[1]

  config = aux.load_config(open(config_path).read())
  conn = aux.open_connection(config)

  if command == 'setup':
    setup(conn, config)
  elif command == 'delete':
    delete(conn)
  else:
    print "Unknown command: " + command
    sys.exit(1)

  conn.commit()

if __name__ == '__main__':
  main()


