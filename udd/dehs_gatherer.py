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
import yaml

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
      (source, unstable_version, unstable_upstream, unstable_parsed_version, unstable_status)
      VALUES ($1, $2, $3, $4, $5)""")

    entries = []
    f = open(my_config['path'])
    pkgs = yaml.load(f)
    for e in pkgs:
      if not 'status' in e:
          ustat = 'error'
      elif e['status'] == 'up to date':
          ustat = 'uptodate'
      elif e['status'] == 'Newer version available':
          ustat = 'outdated'
      else:
          ustat = 'newer-in-debian'

      # add empty fields if missing
      for k in ('debian-uversion', 'upstream-version', 'debian-mangled-uversion'):
          if not k in e:
              e[k] = ''

      entries.append((e['package'], e['debian-uversion'], e['upstream-version'], e['debian-mangled-uversion'], ustat))

    cur.executemany("EXECUTE dehs_insert (%s, %s, %s, %s, %s)", entries)
    cur.execute("DEALLOCATE dehs_insert")
    cur.execute("ANALYZE dehs")

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:
