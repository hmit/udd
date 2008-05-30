#!/usr/bin/env python

import aux
import psycopg2
import sys

def main():
  if len(sys.argv) < 2:
    print "Usage: %s <config>" % sys.argv[0]
    sys.exit(1)

  config = aux.load_config(open(sys.argv[1]).read())

  conn = psycopg2.connect("dbname=" + config['dbname'])

  c = conn.cursor()
  for table in ('sources', 'pkgs', 'distr_ids', 'arch_ids'):
    c.execute("DROP TABLE " + table)

  conn.commit()
  conn.close()

if __name__ == '__main__':
  main()
