# Last-Modified: <Sun Aug 17 12:13:02 2008>
# This file is part of the Ultimate Debian Database Project

from gatherer import gatherer
import aux
from glob import glob
import gzip
import psycopg2
import sys
import os.path

def get_gatherer(config, connection, source):
  return upload_history_gatherer(config, connection, source)

class upload_history_gatherer(gatherer):
  def __init__(self, connection, config, source):
    self.is_ubuntu = source == 'ubuntu-upload-history'
    self.is_debian = not self.is_ubuntu
    gatherer.__init__(self, connection, config, source)
    if not 'path' in self.my_config:
      raise aux.ConfigException('path not specified for source ' + source)

  def run(self):

    path = self.my_config['path']
    if 'only-recent' in self.my_config:
      onlyrecent = self.my_config['only-recent']
    else:
      onlyrecent = True

    cursor = self.cursor()

    tables = ['source', 'version', 'date', 'changed_by', 'changed_by_name', 'changed_by_email', 'maintainer', 'maintainer_name', 'maintainer_email', 'nmu', 'signed_by', 'signed_by_name', 'signed_by_email', 'key_id', 'fingerprint', 'distribution', 'file']

    if self.is_ubuntu:
      tables = tables + ['original_maintainer', 'original_maintainer_name', 'original_maintainer_email']

    indices = ', '.join(map(lambda x: '$' + str(x), range(1,len(tables)+1)))
    tables = ', '.join(tables)

    cursor.execute("PREPARE uh_insert AS INSERT INTO %s (%s) VALUES \
      (%s)" % (self.my_config['table'], tables, indices))

    if self.is_debian:
      cursor.execute("PREPARE uh_arch_insert AS INSERT INTO %s (source, \
        version, architecture, file) VALUES \
        ($1, $2, $3, $4)" % (self.my_config['table'] + '_architecture'))

    if self.is_ubuntu:
      cursor.execute("PREPARE uh_launchpad_close_insert AS INSERT INTO %s (source, version, bug, file) \
          VALUES ($1, $2, $3, $4)" % (self.my_config['table'] + '_launchpad_closes'))
    
    cursor.execute("PREPARE uh_close_insert AS INSERT INTO %s (source, version, bug, file) \
        VALUES ($1, $2, $3, $4)" % (self.my_config['table'] + '_closes'))

    query = "EXECUTE uh_insert(%(Source)s, %(Version)s, %(Message-Date)s, \
      %(Changed-By)s, %(Changed-By_name)s, %(Changed-By_email)s, \
      %(Maintainer)s, %(Maintainer_name)s, %(Maintainer_email)s, %(NMU)s, \
      %(Signed-By)s, %(Signed-By_name)s, %(Signed-By_email)s, %(Key)s, \
      %(Fingerprint)s, %(Distribution)s, %(File)s)"

    if self.is_ubuntu:
        query = query[:-1] + ", %(Original-Maintainer)s, %(Original-Maintainer_name)s, %(Original-Maintainer_email)s)"
        
    if self.is_debian:
        query_archs = "EXECUTE uh_arch_insert(%(Source)s, %(Version)s, %(arch)s, %(File)s)"

    query_closes = "EXECUTE uh_close_insert(%(Source)s, %(Version)s, %(closes)s, %(File)s)"

    if self.is_ubuntu:
        query_launchpad_closes = "EXECUTE uh_launchpad_close_insert(%(Source)s, %(Version)s, %(closes)s, %(File)s)"

    added = {}
    files = glob(path + '/*-changes*')
    files.sort()
    if onlyrecent:
      files = files[-2:]
    else:
      print "Doing full import!"
      if self.is_debian:
        cursor.execute("delete from " + self.my_config['table'] + "_architecture")
      if self.is_ubuntu:
        cursor.execute("delete from " + self.my_config['table'] + "_launchpad_closes")
      cursor.execute("delete from " + self.my_config['table'] + "_closes")
      cursor.execute("delete from " + self.my_config['table'])
    for name in files:
      bname = os.path.basename(name).replace(".gz","").replace(".out","")
      if self.is_debian:
        cursor.execute("DELETE FROM " + self.my_config['table'] + "_architecture where file='%s'" % (bname))
      if self.is_ubuntu:
        cursor.execute("DELETE FROM " + self.my_config['table'] + "_launchpad_closes where file='%s'" % (bname))
      cursor.execute("DELETE FROM " + self.my_config['table'] + "_closes where file='%s'" % (bname))
      cursor.execute("DELETE FROM " + self.my_config['table'] +  " where file='%s'" % (bname))

      f = None
      if name.endswith(".gz"):
        f = gzip.open(name)
      else:
        f = open(name)
      current = {}
      current['Fingerprint'] = 'N/A' # hack: some entries don't have fp
      current['NMU'] = False
      current['Key'] = ''
      current['File'] = bname
      last_field = None
      line_count = 0
      uploads = []
      uploads_archs = []
      uploads_closes = []
      uploads_launchpad_closes = []

      for line in f:
        line_count += 1
        line = line.lstrip()
        # Stupid multi-line maintainer fields *grml*
        if line == '':
          current['Changed-By_name'], current['Changed-By_email'] = aux.parse_email(current['Changed-By'])
          current['Maintainer_name'], current['Maintainer_email'] = aux.parse_email(current['Maintainer'])
          if current['Signed-By'].find('@') != -1:
            current['Signed-By_name'], current['Signed-By_email'] = aux.parse_email(current['Signed-By'])
          else:
            current['Signed-By_name'] = current['Signed-By']
            current['Signed-By_email'] = ''

          if current.has_key('Original-Maintainer'):
            if current['Original-Maintainer'] != 'N/A':
              current['Original-Maintainer_name'], current['Original-Maintainer_email'] = aux.parse_email(current['Original-Maintainer'])
            else:
              current['Original-Maintainer_name'] = current['Original-Maintainer_email'] = 'N/A'
            
          current['Message-Date'] = current['Message-Date'].partition('(')[0].replace('+4200','+0000').replace('+4300','+0000').replace('+4100','+0000').replace('+4400','+0000').replace('+4000','+0000')
          if (current['Source'], current['Version']) in added or \
            (current['Source'], current['Version']) == ('libapache-authznetldap-perl', '0.07-4') or \
            (current['Source'], current['Version']) == ('knj10font', '1.01-1') or \
            (current['Source'], current['Version']) == ('xmorph', '1:20010421') or \
            current['Message-Date'] == 'None':
              print "Skipping upload: "+current['Source']+" "+current['Version']+" "+current['Date']
              current = {}
              current['Fingerprint'] = 'N/A' # hack: some entries don't have fp
              current['NMU'] = False
              current['Key'] = ''
              current['File'] = bname
              last_field = None
              continue
          added[(current['Source'], current['Version'])] = True
          uploads.append(current)
          if self.is_debian:
            for arch in set(current['Architecture'].split()):
              current_arch = {'Source': current['Source'], 'Version': current['Version'], 'File': bname} 
              current_arch['arch'] = arch
              uploads_archs.append(current_arch)
          if current['Closes'] != 'N/A':
            for closes in set(current['Closes'].split()):
              current_closes = {'Source': current['Source'], 'Version': current['Version'], 'File': bname} 
              current_closes['closes'] = closes
              uploads_closes.append(current_closes)
          if current.has_key('Launchpad-Bugs-Fixed') and current['Launchpad-Bugs-Fixed'] != 'N/A':
            for closes in set(current['Launchpad-Bugs-Fixed'].split()):
              current_closes = {'Source': current['Source'], 'Version': current['Version'], 'File': bname} 
              current_closes['closes'] = closes
              uploads_launchpad_closes.append(current_closes)
          current = {}
          current['Fingerprint'] = 'N/A' # hack: some entries don't have fp
          current['NMU'] = False
          current['Key'] = ''
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

      #print uploads
      #for u in uploads:
      #  print u
      #  cursor.execute(query, u)
      cursor.executemany(query, uploads)
      if self.is_debian:
        cursor.executemany(query_archs, uploads_archs)
      if self.is_ubuntu:
        cursor.executemany(query_launchpad_closes, uploads_launchpad_closes)
      cursor.executemany(query_closes, uploads_closes)
      
    cursor.execute("DEALLOCATE uh_insert")
    if self.is_debian:
      cursor.execute("VACUUM ANALYZE " + self.my_config['table'] + '_architecture')
    if self.is_ubuntu:
      cursor.execute("VACUUM ANALYZE " + self.my_config['table'] + '_launchpad_closes')

    cursor.execute("VACUUM ANALYZE " + self.my_config['table'] + '_closes')
    cursor.execute("VACUUM ANALYZE " + self.my_config['table'])
