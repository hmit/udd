#!/usr/bin/env python

"""
This script imports bibliographic references from upstream-metadata.debian.net.
"""

from gatherer import gatherer
from sys import stderr, exit
from yaml import safe_load_all

online=0

def get_gatherer(connection, config, source):
  return bibref_gatherer(connection, config, source)

class bibref_gatherer(gatherer):
  """
  Bibliographic references from upstream-metadata.debian.net.
  """

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('table')
    my_config = self.my_config

    cur = self.cursor()
    query = "DELETE FROM %s" % my_config['table']
    cur.execute(query)
    query = """PREPARE bibref_insert (text, text, text) AS
                   INSERT INTO %s
                   (package, key, value)
                    VALUES ($1, $2, $3)""" % (my_config['table'])
    cur.execute(query)

    pkg = None

  def run(self):
    my_config = self.my_config
    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()

    bibref_file = my_config['bibref_yaml']
    fp = open(bibref_file, 'r')
    result = fp.read()
    fp.close()

    for res in safe_load_all(result):
      package, key, value = res
      value = unicode(value)
      query = "EXECUTE bibref_insert (%s, %s, %s)"
      try:
        cur.execute(query, (package, key, value.encode('utf-8')))
      except UnicodeEncodeError, err:
        print >>stderr, "Unable to inject data for package %s, key %s, value %s. %s" % (package, key, value, err)
        print >>stderr,  "-->", res
    cur.execute("DEALLOCATE bibref_insert")
    cur.execute("ANALYZE %s" % my_config['table'])

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:
