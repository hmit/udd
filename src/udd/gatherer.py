# This file is part of the Ultimate Debian Database project
class gatherer:
  """
  This is the base class of all gatherers which want to use the python
  interface to be called by the dispatcher

  Attributes:
    connection: The connection to the SQL database
    config:     The hashmap representing the configuration"""
  def __init__(self, connection, config):
    self.connection = connection
    self.config = config

  def run(self, source):
    """Called by the dispatcher for a source"""
    raise NotImplementedError

  def cursor(self):
    """Return the cursor for the current connection"""
    return self.connection.cursor()
