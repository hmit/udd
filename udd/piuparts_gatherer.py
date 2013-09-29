#!/usr/bin/env python

"""
This script imports information from piuparts
See http://piuparts.debian.org
"""

from gatherer import gatherer
import pprint
import yaml

def get_gatherer(connection, config, source):
  return ftpnew_gatherer(connection, config, source)

DEBUG=0

class ftpnew_gatherer(gatherer):
  "This class imports the data from piuparts into the database"

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('path', 'table')

  def run(self):
    my_config = self.my_config

    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()

    cur.execute("DELETE FROM %s" % my_config["table"])

    query = """PREPARE piuparts_insert
      AS INSERT INTO %s (source, version, status, section)
      VALUES ($1, $2, $3, $4)""" % (my_config['table'])
    cur.execute(query)

    sf = open(my_config["path"]+"/sections.yaml")
    sections = yaml.safe_load(sf.read())
    sf.close()
    for section in sections:
      sf = open(my_config["path"]+"/"+section+".yaml")
      section_data = yaml.safe_load(sf.read())
      sf.close()
      for source_data in section_data:
        query = """EXECUTE piuparts_insert (
                  %(source)s,
                  %(version)s,
                  %(state)s,
                  '""" + section + "');"
        cur.execute(query, source_data)
        
    cur.execute("DEALLOCATE piuparts_insert")
    cur.execute("ANALYZE %s" % my_config["table"])

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:
