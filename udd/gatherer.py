# This file is part of the Ultimate Debian Database project

import aux
import sys
import psycopg2

class gatherer:
  """
  This is the base class of all gatherers which want to use the python
  interface to be called by the dispatcher

  Attributes:
    connection: The connection to the SQL database
    config:     The hashmap representing the configuration"""
  def __init__(self, connection, config, source):
    self.connection = connection
    self.config = config
    self.source = source
    self.my_config = config[source]

  def run(self):
    """Called by the dispatcher for a source"""
    raise NotImplementedError

  def cursor(self):
    """Return the cursor for the current connection"""
    return self.connection.cursor()

  def assert_my_config(self, *keywords):
    for k in keywords:
      if not k in self.my_config:
	raise aux.ConfigException("%s not specified for source %s" % (k, self.source))
