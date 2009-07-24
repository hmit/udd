# Last-Modified: <Sun Aug 17 12:13:02 2008>
# This file is part of the Ultimate Debian Database Project

from gatherer import gatherer
import aux
from glob import glob
import gzip
import psycopg2
import sys
import email.Utils

def get_gatherer(config, connection, source):
  return upload_history_gatherer(config, connection, source)

class upload_history_gatherer(gatherer):
  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    if not 'path' in self.my_config:
      raise aux.ConfigException('path not specified for source ' + source)

  def tables(self):
    return [
      self.my_config['table'] + '_architecture',
      self.my_config['table'] + '_closes',
      self.my_config['table']]


  def run(self):
    path = self.my_config['path']

    cursor = self.cursor()

    cursor.execute("DELETE FROM " + self.my_config['table'] + '_architecture')
    cursor.execute("DELETE FROM " + self.my_config['table'] + '_closes')
    cursor.execute("DELETE FROM " + self.my_config['table'])

    cursor.execute("PREPARE uh_insert AS INSERT INTO %s (id, package, \
        version, date, changed_by, changed_by_name, changed_by_email, maintainer, maintainer_name, maintainer_email, nmu, signed_by, signed_by_name, signed_by_email, key_id, fingerprint) VALUES \
        ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)" % self.my_config['table'])
    cursor.execute("PREPARE uh_arch_insert AS INSERT INTO %s (id, \
        architecture) VALUES \
        ($1, $2)" % (self.my_config['table'] + '_architecture'))
    cursor.execute("PREPARE uh_close_insert AS INSERT INTO %s (id, bug) \
        VALUES ($1, $2)" % (self.my_config['table'] + '_closes'))

    id = 0
    query = "EXECUTE uh_insert(%(id)s, %(Source)s, %(Version)s, %(Date)s, \
      %(Changed-By)s, %(Changed-By_name)s, %(Changed-By_email)s, \
      %(Maintainer)s, %(Maintainer_name)s, %(Maintainer_email)s, %(NMU)s, \
      %(Signed-By)s, %(Signed-By_name)s, %(Signed-By_email)s, %(Key)s, \
      %(Fingerprint)s)"
    query_archs = "EXECUTE uh_arch_insert(%(id)s, %(arch)s)"
    query_closes = "EXECUTE uh_close_insert(%(id)s, %(closes)s)"
    uploads = []
    uploads_archs = []
    uploads_closes = []
    for name in glob(path + '/debian-devel-changes.*'):
      # print name
      f = None
      if name.endswith(".gz"):
        f = gzip.open(name)
      else:
            f = open(name)
      current = {'id': id}
      current['Fingerprint'] = 'N/A' # hack: some entries don't have fp
      last_field = None
      line_count = 0

      for line in f:
        line_count += 1
        line = line.strip()
        # Stupid multi-line maintainer fields *grml*
        if line == '':
          current['Changed-By_name'], current['Changed-By_email'] = email.Utils.parseaddr(current['Changed-By'])
          current['Maintainer_name'], current['Maintainer_email'] = email.Utils.parseaddr(current['Maintainer'])
          current['Signed-By_name'], current['Signed-By_email'] = email.Utils.parseaddr(current['Signed-By'])
          uploads.append(current)
          for arch in set(current['Architecture'].split()):
            current_arch = {'id': id}
            current_arch['arch'] = arch
            uploads_archs.append(current_arch)
          if current['Closes'] != 'N/A':
            for closes in set(current['Closes'].split()):
              current_closes = {'id': id}
              current_closes['closes'] = closes
              uploads_closes.append(current_closes)
          id += 1
          current = {'id': id}
          current['Fingerprint'] = 'N/A' # hack: some entries don't have fp
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
      
    cursor.executemany(query, uploads)
    cursor.executemany(query_archs, uploads_archs)
    cursor.executemany(query_closes, uploads_closes)
    cursor.execute("DEALLOCATE uh_insert")
    cursor.execute("ANALYZE " + self.my_config['table'] + '_architecture')
    cursor.execute("ANALYZE " + self.my_config['table'] + '_closes')
    cursor.execute("ANALYZE " + self.my_config['table'])
