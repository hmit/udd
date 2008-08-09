#!/usr/bin/env python

"""
This script imports lintian run results into the database
See lintian.debian.org
"""

from aux import quote
from gatherer import gatherer
import re

def get_gatherer(connection, config):
  return carnivore_gatherer(connection, config)

class lintian_gatherer(gatherer):
  #RE to parse lintian output, pushing the tag code to $1, package name
  #to $2, pkg type to $3, tag name to $4 and extra info to $5
  # (stolen from Russ Allbery, thanks dude)
  output_re = re.compile("([EWIXO]): (\S+)(?: (\S+))?: (\S+)(?:\s+(.*))?/");

  code_to_tag_type_map = {
    "E": "error",
    "W": "warning",
    "I": "information",
    "X": "experimental",
    "O": "overriden",
  }

  def __init__(self, connection, config):
    gatherer.__init__(self, connection, config)

  def run(self, source):
    try:
      my_config = self.config[source]
    except:
      raise

    #check that the config contains everything we need:
    for key in ['path', 'table']:
      if not key in my_config:
        raise aux.ConfigException, "%s not configured for source %s" % (key, source)

    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()

    cur.execute("DELETE FROM %s" % my_config["table"])

    cur.execute("""PREPARE lintian_insert 
      AS INSERT INTO %s (package, package_type, tag, tag_type)
      VALUES ($1, $2, $3, $4)""" % (my_config['table']))

    lintian_data = open(my_config['path'])
    line_number = 0
    for line in lintian_data:
      line_number += 1

      #ignore information and verbose output:
      if line.startswith("N:"):
        continue

      match = lintian_gatherer.output_re.match(line)
      if match:
        (code, pkg, pkg_type, tag, extra) = match.groups();

        cur.execute("EXECUTE lintian_insert (%s, %s, %s, %s)" % \
          (pkg, pkg_type, tag, lintian_gatherer.code_to_tag_type_map[code]));
      else:
        print "Can't parse line %d: %s" % (line_number, line)

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:
