#!/usr/bin/python

import udd.aux
import sys
import os

"""This scripts sets up and deletes the tables of the database"""

TABLES = ('popcon_src_average', 'popcon_src', 'popcon',
    'ubuntu_popcon_src_average', 'ubuntu_popcon_src', 'ubuntu_popcon',
    'sources', 'packages', 'ubuntu_sources', 'ubuntu_packages', 'migrations',
    'bugs_archived', 'bugs', 'bug_merged_with', 'bug_user_tags',
    'bug_found_in', 'bug_fixed_in', 'bug_tags', 'upload_history', 'carnivore_emails', 'carnivore_keys', 'carnivore_login', 'carnivore_names', 'lintian', 'orphaned_packages', 'packages_summary', 'ubuntu_packages_summary')
VIEWS = ('bugs_both',)

def print_help():
  print "Usage: %s <config> <delete|setup>" % sys.argv[0]

def delete(conn):
  c = conn.cursor()

  for v in VIEWS:
    c.execute("DROP VIEW " + v)

  for t in TABLES:
    c.execute("DROP TABLE " + t + " CASCADE")


def setup(conn, config):
  if 'script' not in config['setup']:
    raise udd.aux.ConfigException('Script not specified in setup')

  os.system("psql %s < %s" % (config['general']['dbname'],
                              config['setup']['script']))

def main():
  if len(sys.argv) != 3:
    print_help()
    sys.exit(1)

  command = sys.argv[2]
  config_path = sys.argv[1]

  config = udd.aux.load_config(open(config_path).read())
  conn = udd.aux.open_connection(config)

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


