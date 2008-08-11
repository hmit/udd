# This file is part of the Ultimate Debian Database project

import aux

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

  def setup(self):
    if 'schema-dir' in self.config['general']:
      schema_dir = self.config['general']['schema-dir']
      if 'schema' in self.my_config:
	schema = schema_dir + '/' + self.my_config['schema']
	self.eval_sql_file(schema, self.my_config)
      else:
	raise Exception("'schema' not specified for source " + self.source)
    else:
      raise Exception("'schema-dir' not specified")

  def drop(self):
    if 'table' in self.my_config:
      self.cursor().execute("DROP TABLE " + self.my_config['table'])

  def eval_sql_file(self, path, d = None):
    """Load the SQL code from the file specified by <path>. Use pythons string
    formating for the dictionary <d> if it is not None
    Warning: No quoting for the elements of d is done"""
    c = file(path).read()
    if d is not None:
      c = c % d

    cur = self.cursor()
    cur.execute(c)

  def assert_my_config(self, *keywords):
    for k in keywords:
      if not k in self.my_config:
	raise aux.ConfigException("%s not specified for source %s" % (k, self.source))
