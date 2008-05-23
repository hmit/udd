#!/usr/bin/env python
# Last-Modified: <Fri 23 May 2008 14:52:25 CEST>

import debian_bundle
from debian_bundle import debfile
import psycopg2
import sys

def get_archs(conn):
  c = conn.cursor();
  c.execute("SELECT * from arch_ids")
  result = {}
  for row in c.fetchall():
    result[row[1]] = row[0]
  return result

def get_distrs(conn):
  c = conn.cursor()
  c.execute("SELECT * from distr_ids")
  result = {}
  for row in c.fetchall():
    result[row[1]] = row[0]
  return result

if __name__ == '__main__':
  conn = psycopg2.connect("dbname=udd")
  archs = get_archs(conn)
  distr = get_distrs(conn)
  n = 0
  for file in sys.argv[1:]:
    try:
      control = debfile.DebFile(file).debcontrol()
    except Exception:
      print "Could not parse " + file
      continue
    c = conn.cursor()
    c.execute("INSERT INTO pkgs (name, distr_id, arch_id, version, src_id) VALUES ('%s', 0, %d, '%s', 0)" % (control["Package"], archs[control["Architecture"]], control["Version"]))
    n += 1
    if n % 100 == 0:
      print n
  conn.commit()

