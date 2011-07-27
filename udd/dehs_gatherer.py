#!/usr/bin/env python

"""
This script imports dehs status into the database
See dehs.alioth.debian.org

Query used (on DEHS' side) to generate the data:
SELECT COALESCE(u.name, e.name) AS source,
u.up_version AS unstable_upstream, e.up_version AS experimental_upstream,
u.version AS unstable_version, e.version AS experimental_version,
u.dversionmangled AS unstable_parsed_version, e.dversionmangled AS experimental_parsed_version,
u.updated AS unstable_uptodate, e.updated AS experimental_uptodate,
u.watch_warn <> '' AS  unstable_failed, e.watch_warn <> '' AS experimental_failed
FROM (select * from pkgs where dist='unstable' AND watch IS NOT NULL) AS u
FULL JOIN (select * from pkgs where dist='experimental' AND watch IS NOT NULL) AS e ON u.name=e.name
WHERE (u.dist='unstable' OR u.dist IS NULL) AND (e.dist='experimental' OR e.dist IS NULL)
"""

from aux import quote
from gatherer import gatherer
import re

def get_gatherer(connection, config, source):
  return dehs_gatherer(connection, config, source)

class dehs_gatherer(gatherer):

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('path')

  def run(self):
    my_config = self.my_config

    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()

    cur.execute("DELETE FROM dehs")

    cur.execute("""PREPARE dehs_insert 
      AS INSERT INTO dehs
      (source, unstable_version, unstable_upstream, unstable_parsed_version, unstable_status, unstable_last_uptodate,
      experimental_version, experimental_upstream, experimental_parsed_version, experimental_status, experimental_last_uptodate)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""")

    line_number = 0
    entries = []
    for line in file(my_config['path']):
      line_number += 1

      try:
        src, uu, eu, uv, ev, upv, epv, u_utd, e_utd, uf, ef, udate, edate = line.rstrip().split('|')
      except ValueError:
         print "Error reading "+line
         continue
      if udate == "":
        udate = None
      if edate == "":
        edate = None
      ustat = 'error' if uf == 't' else ('uptodate' if u_utd == 't' else ('outdated' if u_utd == 'f' else None))
      estat = 'error' if ef == 't' else ('uptodate' if e_utd == 't' else ('outdated' if e_utd == 'f' else None))
      entries.append((src, uv, uu, upv, ustat, udate, ev, eu, epv, estat, edate))

    cur.executemany("EXECUTE dehs_insert (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", entries)
    cur.execute("DEALLOCATE dehs_insert")
    cur.execute("ANALYZE dehs")

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:
