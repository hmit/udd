"""
This is the base class of all gatherers which want to use the python
interface to be called by the dispatcher
"""

class gatherer:
  def __init__(self, connection, config):
    self.connection = connection
    self.config = config

  def run(self, source):
    raise NotImplementedError

  def cursor(self):
    return self.connection.cursor()
