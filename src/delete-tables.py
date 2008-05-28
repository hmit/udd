#!/usr/bin/env python

import aux
import psycopg2
import sys

def main():
  if len(sys.argv) != 2:
    print "Usage: %s <config>" % sys,argv[0]
    sys.exit(1)

  config = aux.load_config(sys.argv[1])

  conn = psycopg2.connect(config['dbname'])

  c = conn.cursor()
  for table in ('sources', 'pkgs', 'distr_ids', 'arch_ids'):
    c.execute("DELETE * FROM " + table)

  conn.commit()
  conn.close()

if __name__ == '__main__':
  main()
