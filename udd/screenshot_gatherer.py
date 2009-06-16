#!/usr/bin/env python

"""
This script imports screenshot URLs from screenshots.debian.net
"""

from aux import quote
from gatherer import gatherer
import json
from sys import stderr, exit

from psycopg2 import IntegrityError, InternalError

online=0

def get_gatherer(connection, config, source):
  return screenshot_gatherer(connection, config, source)

class screenshot_gatherer(gatherer):
  # Screenshots from screnshots.debian.net

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('table')
    my_config = self.my_config

    cur = self.cursor()
    query = "TRUNCATE %s" % my_config['table']
    cur.execute(query)
    query = """PREPARE screenshots_insert (text, text, text, text, text, text, text, text, text, text) AS
                   INSERT INTO %s
                   (package, version, homepage, maintainer_name, maintainer_email, description,
                    section, screenshot_url, large_image_url, small_image_url)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""" % (my_config['table'])
    cur.execute(query)

    pkg = None

  def run(self):
    my_config = self.my_config
    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()

    screenshot_file = my_config['screenshots_json']
    fp = open(screenshot_file, 'r')
    result = json.read(fp.read())
    fp.close()

    for res in result['screenshots']:
      # print res
      try:
        res['maintainer'] = res['maintainer'].encode('utf-8')
      except AttributeError, err:
        print >>stderr, "Missing maintainer for screenshot of package %s" % res['name']
      query = """EXECUTE screenshots_insert
                        (%(name)s, %(version)s, %(homepage)s, %(maintainer)s, %(maintainer_email)s,
                         %(description)s, %(section)s, %(url)s, %(large_image_url)s, %(small_image_url)s)"""
      try:
        cur.execute(query, res)
      except UnicodeEncodeError, err:
        print >>stderr, "Unable to inject data for package %s. %s" % (res['name'], err)
        print >>stderr,  "-->", res
    cur.execute("DEALLOCATE screenshots_insert")

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:

