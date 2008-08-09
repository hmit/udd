#!/usr/bin/env python

"""
This script imports the list of orphaned, ITAed and RFAed packages into the DB
"""

import aux
from gatherer import gatherer
import re

def get_gatherer(connection, config):
  return orphaned_packages_gatherer(connection, config)

class orphaned_packages_gatherer(gatherer):
  def __init__(self, connection, config):
    gatherer.__init__(self, connection, config)

  title_re = re.compile('^(ITA|RFA|O): ([^\s]*) [-]+ (.*)$')
  otime_re = re.compile('^<!-- time:([0-9]+) ')
  chtitle_re = re.compile('^<strong>Changed Bug title to `O:.*$')
  
  def get_time_orphaned(self, bug):
    bug = str(bug)
    dir = bug[4:6]
    f = open(self.my_config['bugs-path'] + '/spool/db-h/' + dir + '/' + bug + '.log', 'r')
    otime = None
    for l in f:
      m = self.chtitle_re.match(l)
      if m:
        return otime
      m = self.otime_re.match(l)
      if m:
        otime = int(m.group(1))
    return None

  def run(self, source):
    self.my_config = self.config[source]
    #check that the config contains everything we need:
    for key in ['bugs-path']:
      if not key in self.my_config:
        raise aux.ConfigException, "%s not configured for source %s" % (key, source)

    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()
    cur2 = self.cursor()
    cur.execute("SELECT id, title, arrival FROM bugs_unarchived WHERE package = 'wnpp' AND status != 'done' AND title ~* '^(ITA|RFA|O):' AND id NOT IN (SELECT id from bug_merged_with WHERE id > merged_with)")
    rows = cur.fetchall()

    cur2.execute("DELETE FROM orphaned_packages")
    cur2.execute("PREPARE opkgs_insert AS INSERT INTO orphaned_packages VALUES ($1, $2, $3, $4, $5)")

    for row in rows:
      m = self.title_re.match(row[1])
      if m == None:
        print "Invalid bug: #" + str(row[0]) + ": " + row[1]
      else:
        time_orphaned = self.get_time_orphaned(row[0])
        if time_orphaned == None:
          cur2.execute("EXECUTE opkgs_insert(%s,%s,%s,%s,%s)", (
            m.group(2), m.group(1), row[0],
            m.group(3), row[2]))
        else:
          cur2.execute("EXECUTE opkgs_insert(%s,%s,%s,%s,%s::abstime)", (
            m.group(2), m.group(1), row[0],
            m.group(3), time_orphaned))

# vim:set et tabstop=2:
