# Last-Modified: <Thu Aug 14 12:06:50 2008>
# This file is part of the Ultimate Debian Database Project

from gatherer import gatherer
import aux
from glob import glob
import gzip
import psycopg2
import sys

def get_gatherer(config, connection, source):
  return upload_history_gatherer(config, connection, source)

class upload_history_gatherer(gatherer):
  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    if not 'path' in self.my_config:
      raise aux.ConfigException('path not specified for source ' + source)

  def drop(self):
    cur = self.cursor()
    cur.execute("DROP TABLE %s" % self.my_config['table'])
    cur.execute("DROP TABLE %s" % self.my_config['table'] + '_architecture')
    cur.execute("DROP TABLE %s" % self.my_config['table'] + '_closes')


  def run(self):
    path = self.my_config['path']

    cursor = self.cursor()

    cursor.execute("DELETE FROM " + self.my_config['table'])
    cursor.execute("DELETE FROM " + self.my_config['table'] + '_architecture')
    cursor.execute("DELETE FROM " + self.my_config['table'] + '_closes')

    cursor.execute("PREPARE uh_insert AS INSERT INTO %s VALUES \
	($1, $2, $3, $4, $5, $6, $7, $8, $9)" % self.my_config['table'])
    cursor.execute("PREPARE uh_arch_insert AS INSERT INTO %s VALUES \
	($1, $2)" % (self.my_config['table'] + '_architecture'))
    cursor.execute("PREPARE uh_close_insert AS INSERT INTO %s VALUES \
	($1, $2)" % (self.my_config['table'] + '_closes'))

    id = 0
    for name in glob(path + '/debian-devel-*'):
      print name
      f = None
      if name.endswith(".gz"):
	f = gzip.open(name)
      else:
	f = open(name)
      
      current = {'id': id}
      last_field = None
      line_count = 0
      for line in f:
	line_count += 1
	line = line.strip()
	# Stupid multi-line maintainer fields *grml*
	if line == '':
	  try:
	    query = "EXECUTE uh_insert(%(id)s, %(Source)s, %(Version)s, %(Date)s, %(Changed-By)s, \
		%(Maintainer)s, %(NMU)s, %(Key)s, %(Signed-By)s)"
	    cursor.execute(query, current)
	    for arch in set(current['Architecture'].split()):
	      current['arch'] = arch
	      query = "EXECUTE uh_arch_insert(%(id)s, %(arch)s)"
	      cursor.execute(query, current)
	    if current['Closes'] != 'N/A':
	      for closes in set(current['Closes'].split()):
		current['closes'] = closes
		query = "EXECUTE uh_close_insert(%(id)s, %(closes)s)"
		cursor.execute(query, current)
	  except psycopg2.ProgrammingError, s:
	    print "Error at line %d of file %s" % (line_count, name)
	    continue
	    #raise
	  id += 1
	  current = {'id': id}
	  last_field = None
	  continue

	if line.find(':') == -1:
	  if not last_field:
	    raise Exception, "Format error on line " + line_count + "of file " + name
	  current[last_field] += line
	  continue


	(field, data) = line.split(':', 1)
	data = data.strip()
	current[field] = data
	
	last_field = field
    
    cursor.execute("DEALLOCATE uh_insert")
