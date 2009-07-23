#!/usr/bin/env python

"""
This script imports the list of orphaned, ITAed and RFAed packages into the DB
"""

import aux
from gatherer import gatherer
import re
from psycopg2 import IntegrityError 

def get_gatherer(connection, config, source):
  return orphaned_packages_gatherer(connection, config, source)

class orphaned_packages_gatherer(gatherer):
  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('bugs-path', 'table', 'unarchived-table')

  title_re = re.compile('^(ITA|RFA|O): ([^\s]*)( [-]+ (.*))?$')
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

  def run(self):
    #check that the config contains everything we need:
    for key in ['bugs-path']:
      if not key in self.my_config:
        raise aux.ConfigException, "%s not configured for source %s" % (key, source)

    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()
    cur2 = self.cursor()
    cur.execute("SELECT id, title, arrival FROM %s WHERE package = 'wnpp' AND status != 'done' AND title ~* '^(ITA|RFA|O):' AND id NOT IN (SELECT id from %s WHERE id > merged_with)" % (self.my_config['unarchived-table'], self.my_config['unarchived-table'] + '_merged_with'))
    rows = cur.fetchall()

    cur2.execute("DELETE FROM %s" % self.my_config['table'])
    cur2.execute("PREPARE opkgs_insert AS INSERT INTO %s (source, type, bug, description, orphaned_time) VALUES ($1, $2, $3, $4, $5)" % self.my_config['table'])

    for row in rows:
      m = self.title_re.match(row[1])
      if m == None:
        print "Invalid bug: #" + str(row[0]) + ": " + row[1]
      else:
        #print "bug: #" + str(row[0]) + ": " + row[1]
        time_orphaned = self.get_time_orphaned(row[0])
        try:
          if time_orphaned == None:
            cur2.execute("EXECUTE opkgs_insert(%s,%s,%s,%s,%s)", (
              m.group(2), m.group(1), row[0],
              m.group(4), row[2]))
          else:
            cur2.execute("EXECUTE opkgs_insert(%s,%s,%s,%s,%s::abstime)", (
              m.group(2), m.group(1), row[0],
              m.group(4), time_orphaned))
        except IntegrityError, message:
          print "Integrity Error inserting bug " + str(row[0]) + " " + m.group(2)
          continue
    cur2.execute("ANALYZE %s" % self.my_config['table'])

# vim:set et tabstop=2:
