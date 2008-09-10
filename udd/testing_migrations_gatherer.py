# Last-Modified: <Sun Aug 10 12:16:12 2008>

# This file is a part of the Ultimate Debian Database Project

from gatherer import gatherer
from aux import ConfigException, quote
from time import strptime

ZERO_DATE = '0000-01-01'

def get_gatherer(config, connection, source):
  return testing_migrations_gatherer(config, connection, source)


class testing_migrations_gatherer(gatherer):
  """This class imports testing migrations data into the database.

  For the files, see http://qa.debian.org/~lucas/testing-status.raw"""
  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('path')

  def run(self):
      src_cfg = self.my_config

      c = self.connection.cursor()

      c.execute("DELETE FROM migrations")

      c.execute("PREPARE mig_insert AS INSERT INTO migrations (source, in_testing, testing_version, in_unstable, unstable_version, sync, sync_version, first_seen) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)")
      
      f = open(src_cfg['path'])
      for line in f:
	(package, in_testing, testing_version, in_unstable, unstable_version, sync, sync_version, first_seen) = line.split()
	for field in ('in_testing', 'in_unstable', 'sync', 'first_seen'):
	  is_null = False
	  exec "is_null = %s == ZERO_DATE" % field
	  if is_null:
	    exec "%s = 'NULL'" % field
	  else:
	    exec "%s = quote(%s)" % (field, field)

	for field in ('package', 'testing_version', 'unstable_version', 'sync_version'):
	  is_null = False
	  exec "is_null = %s == '-'" % field
	  if is_null:
	    exec "%s = 'NULL'" % field
	  else:
	    exec "%s = quote(%s)" % (field, field)
	  
	c.execute("EXECUTE mig_insert(%s, %s, %s, %s, %s, %s, %s, %s)" \
	    % (package, in_testing, testing_version, in_unstable, unstable_version, sync, sync_version, first_seen))

      c.execute("DEALLOCATE mig_insert")

