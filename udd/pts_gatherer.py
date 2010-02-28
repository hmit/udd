# Last-Modified: <Sun Aug 10 12:16:12 2008>

# This file is a part of the Ultimate Debian Database Project

from gatherer import gatherer
from aux import ConfigException, quote
from time import strptime

ZERO_DATE = '0000-01-01'

def get_gatherer(config, connection, source):
  return pts_gatherer(config, connection, source)


class pts_gatherer(gatherer):
  """This class imports PTS subscribers"""

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('path')

  def run(self):
    src_cfg = self.my_config

    c = self.connection.cursor()

    c.execute("DELETE FROM pts")

    c.execute("PREPARE pts_insert AS INSERT INTO pts (source, email) VALUES ($1, $2)")
      
    f = open(src_cfg['path'])
    for line in f:
      (package, subs) = line.split("\t")
      for sub in subs.split(", "):
        sub = sub.strip()
        c.execute("EXECUTE pts_insert(%s, %s)", (package, sub))

    c.execute("DELETE FROM pts_public")
    c.execute("INSERT INTO pts_public SELECT source, md5(lower(email)) FROM pts")
    c.execute("DEALLOCATE pts_insert")
    c.execute("ANALYZE pts")
    c.execute("ANALYZE pts_public")

