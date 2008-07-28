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

    if not 'distribution' in my_config:
      raise aux.ConfigException, "distribution not configured for source " + source

    cur = self.cursor()

    cur.execute("PREPARE pop_insert AS INSERT INTO popcon (package, insts, vote, olde, recent, nofiles, distribution) VALUES ($1, $2, $3, $4, $5, $6, '%s')" % my_config['distribution'])

    popcon = gzip.open(my_config['path'])

    cur.execute("DELETE FROM popcon WHERE distribution = '%s'" % my_config['distribution'])

    # used for ignoring ubuntu's broken popcon lines
    ascii_match = re.compile("^[A-Za-z0-9-.+_]+$")

    linenr = 0
    for line in popcon.readlines():
      linenr += 1
      name, data = line.split(None, 1)
      if name == "Submissions:":
	cur.execute("INSERT INTO popcon (package, vote, distribution) VALUES ('_submissions', %s, '%s')" % (data, my_config['distribution']))
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

if __name__ == '__main__':
  main()
