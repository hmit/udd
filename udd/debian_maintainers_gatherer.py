#!/usr/bin/env python

"""
Import information about debian maintainer upload right from the dm.txt file
hosted on ftp-master
"""

try:
    from debian import deb822
except:
    from debian_bundle import deb822
from aux import parse_email
from gatherer import gatherer
import re

def get_gatherer(connection, config, source):
  return debian_maintainer_gatherer(connection, config, source)

class debian_maintainer_gatherer(gatherer):

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('path', 'table')

  def run(self):
    my_config = self.my_config

    cur = self.cursor()
    cur.execute("DELETE FROM %s" % my_config["table"])

    cur.execute("""PREPARE dm_insert 
      AS INSERT INTO %s (
        maintainer,
        maintainer_name,
        maintainer_email,
        fingerprint,
        package,
        granted_by_fingerprint
      ) VALUES (
        $1,
        $2,
        $3,
        $4,
        $5,
        $6
      )""" % (my_config['table']))


    dm_data = open(my_config['path'])
    entries = []

    for stanza in deb822.Sources.iter_paragraphs(dm_data, shared_storage=False):
      maintainer_name, maintainer_email = parse_email(stanza["Uid"])
      allowed = re.split(',\s*',stanza['Allow']);
      for a in allowed:
        matches = re.match('^\s*(\S+)\s+\(([^$]+)\)\s*$',a)
        if matches:
          package = matches.group(1)
          granted_by = matches.group(2)
          entries.append((stanza["Uid"],maintainer_name,maintainer_email,stanza["Fingerprint"],package,granted_by))
        else:
          raise Exception("no match: " + a)

    cur.executemany("EXECUTE dm_insert (%s, %s, %s, %s, %s, %s)", entries)
    cur.execute("DEALLOCATE dm_insert")
    cur.execute("ANALYZE %s" % my_config["table"])

# vim:set et tabstop=2:
