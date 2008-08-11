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

    for k in ['path', 'table', 'packages-table']:
      if k not in my_config:
	raise aux.ConfigException(k + ' not specified in ' + source)

    table = my_config['table']
    table_src = table + "_src"
    table_src_average = table + "_src_average"

    cur = self.cursor()

    cur.execute("PREPARE pop_insert AS INSERT INTO %s (package, insts, vote, olde, recent, nofiles) VALUES ($1, $2, $3, $4, $5, $6)" % (table))

    popcon = gzip.open(my_config['path'])

    cur.execute("DELETE FROM " + table)
    cur.execute("DELETE FROM " + table_src)
    cur.execute("DELETE FROM " + table_src_average)

    # used for ignoring ubuntu's broken popcon lines
    ascii_match = re.compile("^[A-Za-z0-9-.+_]+$")

    linenr = 0
    d = {}
    for line in popcon:
      linenr += 1
      name, data = line.split(None, 1)
      if name == "Submissions:":
	d['data'] = int(data)
	cur.execute("INSERT INTO " + table + " (package, vote) VALUES ('_submissions', %(data)s)", d)
	continue
      try:
	(name, vote, old, recent, nofiles) = data.split()
	d['name'] = name
	for k in ['vote', 'old', 'recent', 'nofiles']:
	  exec '%s = int(%s)' % (k,k)
	  exec 'd["%s"] = %s' % (k,k)
	d['insts'] = vote + old + recent + nofiles
	if ascii_match.match(name) == None:
	  print "Skipping line %d of file %s as it contains illegal characters: %s" % (linenr, my_config['path'], line)
	  continue
	query = "EXECUTE pop_insert(%(name)s, %(insts)s, %(vote)s, %(old)s, %(recent)s, %(nofiles)s)"
	cur.execute(query, d)
      except ValueError:
	continue

    cur.execute("DEALLOCATE pop_insert")

    #calculate _src and _src_avg
    cur.execute("""
    INSERT INTO %s SELECT DISTINCT packages.source, max(insts) AS insts, max(vote) AS vote, max(olde) AS old,
           max(recent) AS recent, max(nofiles) as nofiles
      FROM %(table)s, %(packages-table)s_summary AS pkgs
      WHERE %(table)s.package = pkgs.package
      GROUP BY pkgs.source;
      """ % (table_src, my_config))
    cur.execute("""
    INSERT INTO %s SELECT packages.source, avg(insts) AS insts, avg(vote) AS vote, avg(olde) AS old,
           avg(recent) AS recent, avg(nofiles) as nofiles
      FROM %(table)s, %(packages-table)s_summary AS pkgs
      WHERE %(table)s.package = pkgs.package
      GROUP BY pkgs.source;
      """ % (table_src_average, my_config))

if __name__ == '__main__':
  main()
