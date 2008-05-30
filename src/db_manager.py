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
  if 'script' not in config['setup']:
    raise aux.ConfigException('Script not specified in setup')

  c = conn.cursor()
  for line in open(config['setup']['script']).readlines():
    line = line.strip()
    if line:
      c.execute(line)

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


