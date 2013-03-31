#!/usr/bin/env python

"""
This script imports lintian run results into the database
See lintian.debian.org
"""

from aux import quote
from gatherer import gatherer
import re

def get_gatherer(connection, config, source):
  return lintian_gatherer(connection, config, source)

class lintian_gatherer(gatherer):
  #RE to parse lintian output, pushing the tag code to $1, package name
  #to $2, pkg type to $3, pkg version to $4, pkg arch to $5, tag name to $6 and
  # extra info to $7. Taken from Niels Thykier in #647917
  verarch = "(?: \s*\(([^)]+?)\)\s*\[([^)]+?)\])"
                #  vers               arch
  output_re = re.compile("([EWIXOP]): (\S+)(?: (\S+)(?:%s)?)?: (\S+)(?:\s+(.*))?" % verarch)
                         #  code      pkg      type  verarch:  tag     extra

  ignore_re = re.compile("^((gpg|secmem usage|warning|(/bin/)?tar|internal error|/usr/bin/xgettext|ERROR): |     |Use of uninitialized value in numeric lt .*)");

  code_to_tag_type_map = {
    "E": "error",
    "W": "warning",
    "I": "information",
    "X": "experimental",
    "O": "overriden",
    "P": "pedantic",
  }

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('path', 'table')

  def run(self):
    my_config = self.my_config

    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()

    cur.execute("DELETE FROM %s" % my_config["table"])

    cur.execute("""PREPARE lintian_insert 
      AS INSERT INTO %s (package, package_type, package_version, package_arch, tag, tag_type, information)
      VALUES ($1, $2, $3, $4, $5, $6, $7)""" % (my_config['table']))

    lintian_data = file(my_config['path'])
    line_number = 0
    entries = []
    for line in lintian_data:
      line_number += 1

      #ignore information and verbose output:
      if line.startswith("N:"):
        continue

      match = lintian_gatherer.output_re.match(line)
      if match:
        (code, pkg, pkg_type, vers, arch, tag, extra) = match.groups();

        if (pkg == 'manpages-ja' and tag == 'manpage-has-errors-from-man') or \
           (pkg == 'manpages-zh' and tag == 'manpage-has-errors-from-man') or \
           (pkg == 'mplayer' and tag == 'manpage-has-errors-from-man'):
          extra = '' # HACK psycopg2.DataError: invalid byte sequence for encoding "UTF8": 0xbb
        entries.append((pkg, pkg_type, vers, arch, tag, lintian_gatherer.code_to_tag_type_map[code], extra))
#      elif not lintian_gatherer.ignore_re.match(line):
#        print "Can't parse line %d: %s" % (line_number, line.rstrip())

    # for e in entries:
      # print e
      # cur.executemany("EXECUTE lintian_insert (%s, %s, %s, %s, %s)", [e])
    cur.executemany("EXECUTE lintian_insert (%s, %s, %s, %s, %s, %s, %s)", entries)
    cur.execute("DEALLOCATE lintian_insert")
    cur.execute("ANALYZE %s" % my_config["table"])

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:
