#!/usr/bin/env python

"""
This script imports some fields from the Debian LDAP into the database
"""

from aux import quote
from gatherer import gatherer
import re
import psycopg2
import time

def get_gatherer(connection, config, source):
  return wannabuild_gatherer(connection, config, source)

class wannabuild_gatherer(gatherer):

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config()

  def run(self):
    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()

    cur.execute("DELETE FROM wannabuild")

    cur.execute("""PREPARE wb_insert 
      AS INSERT INTO wannabuild
      (architecture, source, distribution, version, state, installed_version, previous_state, state_change, binary_nmu_version, notes)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""")

    wbconn = psycopg2.connect(self.my_config['wbdb'])
    wbcur = wbconn.cursor()

    entries = []
    for arch in self.my_config['archs']:
        wbcur.execute("SELECT package, distribution, version, state, installed_version, previous_state, state_change, binary_nmu_version, notes FROM \"%s_public\".packages" % arch)
        for row in wbcur.fetchall():
            row = list(row)
            if row[6] != None:
                try:
                    t = time.strptime(row[6], "%Y %b %d %H:%M:%S")
                    row[6] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", t)
                except ValueError:
                    row[6] = None
            entries.append([arch] + row)
        cur.executemany("EXECUTE wb_insert (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", entries)
        entries = []
    cur.execute("DEALLOCATE wb_insert")
    cur.execute("ANALYZE wannabuild")

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:
