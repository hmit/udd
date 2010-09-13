# Last-Modified: <Sun Aug 17 12:13:02 2008>
# This file is part of the Ultimate Debian Database Project

from gatherer import gatherer
import aux
from glob import glob
import gzip
import psycopg2
import sys
import email.Utils
import os.path

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

    cursor.execute("PREPARE uh_insert AS INSERT INTO %s (source, \
        version, date, changed_by, changed_by_name, changed_by_email, maintainer, maintainer_name, maintainer_email, nmu, signed_by, signed_by_name, signed_by_email, key_id, fingerprint, distribution, file) VALUES \
        ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)" % self.my_config['table'])
    cursor.execute("PREPARE uh_arch_insert AS INSERT INTO %s (source, \
        version, architecture, file) VALUES \
        ($1, $2, $3, $4)" % (self.my_config['table'] + '_architecture'))
    cursor.execute("PREPARE uh_close_insert AS INSERT INTO %s (source, version, bug, file) \
        VALUES ($1, $2, $3, $4)" % (self.my_config['table'] + '_closes'))

    query = "EXECUTE uh_insert(%(Source)s, %(Version)s, %(Message-Date)s, \
      %(Changed-By)s, %(Changed-By_name)s, %(Changed-By_email)s, \
      %(Maintainer)s, %(Maintainer_name)s, %(Maintainer_email)s, %(NMU)s, \
      %(Signed-By)s, %(Signed-By_name)s, %(Signed-By_email)s, %(Key)s, \
      %(Fingerprint)s, %(Distribution)s, %(File)s)"
    query_archs = "EXECUTE uh_arch_insert(%(Source)s, %(Version)s, %(arch)s, %(File)s)"
    query_closes = "EXECUTE uh_close_insert(%(Source)s, %(Version)s, %(closes)s, %(File)s)"
    added = {}
    files = glob(path + '/debian-devel-changes.*')
    files.sort()
    for name in files[-2:]:
#    for name in files:
      bname = os.path.basename(name).replace(".gz","").replace(".out","")
#      print bname
      cursor.execute("DELETE FROM " + self.my_config['table'] + "_architecture where file='%s'" % (bname))
      cursor.execute("DELETE FROM " + self.my_config['table'] + "_closes where file='%s'" % (bname))
      cursor.execute("DELETE FROM " + self.my_config['table'] +  " where file='%s'" % (bname))

      f = None
      if name.endswith(".gz"):
        f = gzip.open(name)
      else:
        f = open(name)
      current = {}
      current['Fingerprint'] = 'N/A' # hack: some entries don't have fp
      current['File'] = bname
      last_field = None
      line_count = 0
      uploads = []
      uploads_archs = []
      uploads_closes = []

      for line in f:
        line_count += 1
        line = line.lstrip()
        # Stupid multi-line maintainer fields *grml*
        if line == '':
          current['Changed-By_name'], current['Changed-By_email'] = email.Utils.parseaddr(current['Changed-By'])
          current['Maintainer_name'], current['Maintainer_email'] = email.Utils.parseaddr(current['Maintainer'])
          if current['Signed-By'].find('@') != -1:
            current['Signed-By_name'], current['Signed-By_email'] = email.Utils.parseaddr(current['Signed-By'])
          else:
            current['Signed-By_name'] = current['Signed-By']
            current['Signed-By_email'] = ''
          current['Message-Date'] = current['Message-Date'].partition('(')[0].replace('+4200','+0000').replace('+4300','+0000').replace('+4100','+0000').replace('+4400','+0000').replace('+4000','+0000')
          if (current['Source'], current['Version']) in added or \
            (current['Source'], current['Version']) == ('libapache-authznetldap-perl', '0.07-4') or \
            (current['Source'], current['Version']) == ('knj10font', '1.01-1') or \
            current['Message-Date'] == 'None':
              print "Skipping upload: "+current['Source']+" "+current['Version']+" "+current['Date']
              current = {}
              current['Fingerprint'] = 'N/A' # hack: some entries don't have fp
	      current['File'] = bname
              last_field = None
              continue
          added[(current['Source'], current['Version'])] = True
          uploads.append(current)
          for arch in set(current['Architecture'].split()):
            current_arch = {'Source': current['Source'], 'Version': current['Version'], 'File': bname} 
            current_arch['arch'] = arch
            uploads_archs.append(current_arch)
          if current['Closes'] != 'N/A':
            for closes in set(current['Closes'].split()):
              current_closes = {'Source': current['Source'], 'Version': current['Version'], 'File': bname} 
              current_closes['closes'] = closes
              uploads_closes.append(current_closes)
          current = {}
          current['Fingerprint'] = 'N/A' # hack: some entries don't have fp
	  current['File'] = bname
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
