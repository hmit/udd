#!/usr/bin/env python

"""
This script imports the popcon data into the database
See http://popcon.debian.org/
"""

import aux
import sys
import gzip
from gatherer import gatherer
import re

def get_gatherer(connection, config):
  return popcon_gatherer(connection, config)

class popcon_gatherer(gatherer):
  def __init__(self, connection, config):
    gatherer.__init__(self, connection, config)

  def run(self, source):
    try:
      my_config = self.config[source]
    except:
      raise

    if not 'path' in my_config:
      raise aux.ConfigException, "path not configured for source " + source

    if not 'table' in my_config:
      raise aux.ConfigException, "table not configured for source " + source

    if not 'packages-table' in my_config:
      raise aux.ConfigException, "packages-table not configured for source " + source

    table = my_config['table']
    table_src_max = table + "_src_max"
    table_src_average = table + "_src_average"

    cur = self.cursor()

    cur.execute("PREPARE pop_insert AS INSERT INTO %s (package, insts, vote, olde, recent, nofiles) VALUES ($1, $2, $3, $4, $5, $6)" % (table))

    popcon = gzip.open(my_config['path'])

    cur.execute("DELETE FROM " + table)
    cur.execute("DELETE FROM " + table_src_max)
    cur.execute("DELETE FROM " + table_src_average)

    # used for ignoring ubuntu's broken popcon lines
    ascii_match = re.compile("^[A-Za-z0-9-.+_]+$")

    linenr = 0
    for line in popcon.readlines():
      linenr += 1
      name, data = line.split(None, 1)
      if name == "Submissions:":
	cur.execute("INSERT INTO %s (package, vote) VALUES ('_submissions', %s)" % (table, data))
      try:
	(name, vote, old, recent, nofiles) = data.split()
	if ascii_match.match(name) == None:
	  print "Skipping line %d of file %s as it contains illegal characters: %s" % (linenr, my_config['path'], line)
	  continue
	query = "EXECUTE pop_insert('%s', %s, %s, %s, %s, %s)" %\
	    (name, int(vote) + int(old) + int(recent) + int(nofiles), vote, old, recent, nofiles)
	cur.execute(query)
      except ValueError:
	continue

    cur.execute("DEALLOCATE pop_insert")

    #calculate _src_max and _src_avg
    cur.execute("PREPARE pop_insert AS INSERT INTO %s VALUES ($1, $2, $3, $4, $5, $6)" % table_src_max)
    cur.execute("""
    SELECT packages.source, max(insts) AS insts, max(vote) AS vote, max(olde) AS old,
           max(recent) AS recent, max(nofiles) as nofiles
      FROM %(table)s,
	    (SELECT DISTINCT %(packages-table)s.package, %(packages-table)s.source FROM %(packages-table)s)
	          as packages
      WHERE 
	    %(table)s.package = packages.package
      GROUP BY packages.source;
      """ % my_config)
    for line in cur.fetchall():
      cur.execute("EXECUTE pop_insert ('%s', %s, %s, %s, %s, %s)" % line)
    cur.execute("DEALLOCATE pop_insert");
    cur.execute("PREPARE pop_insert AS INSERT INTO %s VALUES ($1, $2, $3, $4, $5, $6)" % table_src_average)
    cur.execute("""
    SELECT packages.source, avg(insts) AS insts, avg(vote) AS vote, avg(olde) AS old,
           avg(recent) AS recent, avg(nofiles) as nofiles
      FROM %(table)s,
	    (SELECT DISTINCT %(packages-table)s.package, %(packages-table)s.source FROM %(packages-table)s)
	          as packages
      WHERE 
	    %(table)s.package = packages.package
      GROUP BY packages.source;
      """ % my_config)
    for line in cur.fetchall():
      cur.execute("EXECUTE pop_insert ('%s', %s, %s, %s, %s, %s)" % line)
    cur.execute("DEALLOCATE pop_insert");

if __name__ == '__main__':
  main()
