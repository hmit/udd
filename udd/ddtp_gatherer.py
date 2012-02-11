#!/usr/bin/env python

"""
This script imports translations from the Debian Description
translation project into the database.  It parses the translation
files at
    http://ftp.debian.org/debian/dists/${release}/${component}/i18n/
"""

from aux import quote
from gatherer import gatherer
import re
try:
    from debian import deb822
except:
    from debian_bundle import deb822
from os import listdir, path, access, F_OK
from sys import stderr, exit
from filecmp import cmp
import gzip
import bz2
import hashlib
from psycopg2 import IntegrityError, InternalError, ProgrammingError

import logging
import logging.handlers

debug=0
def to_unicode(value, encoding='utf-8'):
    if isinstance(value, str):
	return value.decode(encoding)
    else:
        return unicode(value)

def get_gatherer(connection, config, source):
  return ddtp_gatherer(connection, config, source)

class ddtp():
  def __init__(self, package, release, language):
    self.package          = package
    self.release          = release
    self.language         = language
    self.description      = ''
    self.long_description = ''
    self.description_md5  = ''
    self.version          = ''

  def __str__(self):
    return "Package %s: %s, %s\n%s" % \
        (self.package, self.language, self.description, self.long_description)

class ddtp_gatherer(gatherer):
  # DDTP translations

  select_language_re   = re.compile('^Translation-(\w+)\.bz2$')

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('path', 'files', 'mirrorpath', 'table')
    my_config = self.my_config
    self.log = logging.getLogger(self.__class__.__name__)
    if debug==1:
	self.log.setLevel(logging.DEBUG)
    else:
	self.log.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler(filename=self.__class__.__name__+'.log',mode='w')
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - (%(lineno)d): %(message)s")
    handler.setFormatter(formatter)
    self.log.addHandler(handler)

    cur = self.cursor()
    query = "PREPARE ddtp_delete (text, text) AS DELETE FROM %s WHERE release = $1 AND language = $2" % my_config['table']
    self.log.debug("execute query %s", query)
    cur.execute(query)
    query = """PREPARE ddtp_insert AS INSERT INTO %s
                   (package, release, language, description, long_description, description_md5)
                    VALUES ($1, $2, $3, $4, $5, $6)""" % (my_config['table'])
    self.log.debug("execute query %s", query)
    cur.execute(query)

    query = """PREPARE ddtp_check_before_insert (text, text, text, text, text) AS
                  SELECT COUNT(*) FROM %s
                    WHERE package = $1 AND release = $2 AND language = $3 AND 
                          description = $4 AND description_md5 = $5""" % (my_config['table'])
    # self.log.debug("execute query %s", query)
    cur.execute(query)

    pkg = None

  def run(self):
    my_config = self.my_config
    cur = self.cursor()

    cur.execute('SELECT component FROM packages GROUP by component')
    rows = cur.fetchall()
    valid_components = []
    for r in rows:
        valid_components.append(r[0])
    releases = listdir(my_config['path'])
    for rel in releases:
      cpath = my_config['path']+'/'+rel+'/'
      components = listdir(cpath)
      for comp in components:
        if comp not in valid_components:
          self.log.error("Invallid component '%s' file found in %s", comp, cpath)
          continue
        cfp = open(cpath+'/'+comp,'r')
        trfilepath = my_config['mirrorpath']+'/'+rel+'/'+comp+'/i18n/'
        for line in cfp.readlines():
          (sha1, size, file) = line.strip().split(' ')
          trfile = trfilepath + file
          # check whether hash recorded in index file fits real file
          f = open(trfile)
          h = hashlib.sha1()
          h.update(f.read())
          hash = h.hexdigest()
          f.close()
          if sha1 != hash:
            self.log.error("Hash mismatch between file %s and index found in %s/%s.", trfile, cpath, comp)
            continue
          fsize = path.getsize(trfile)
          if int(size) != fsize:
            self.log.error("Size mismatch between file %s (%i) and index found in %s/%s (%s).", trfile, fsize, cpath, comp, size)
            continue
          match = ddtp_gatherer.select_language_re.match(file)
          if not match:
            self.log.error("Can not parse language of file %s.", trfile)
            continue
          lang = match.groups()[0]
          self.import_translations(trfile, rel, lang)
        cfp.close()
       
    cur.execute("DEALLOCATE ddtp_insert")
    cur.execute("ANALYZE %s" % my_config['table'])


  def import_translations(self, trfile, rel, lang):
        print trfile, rel, lang

        cur = self.cursor()
        # Delete only records where we actually have Translation files.  This
        # prevents dump deletion of all data in case of broken downloads
        cur.execute('EXECUTE ddtp_delete (%s, %s)', (rel, lang))
        self.log.debug('EXECUTE ddtp_delete (%s, %s)', (rel, lang))

        i18n_error_flag=0
        descstring = 'Description-'+lang
        g = bz2.BZ2File(trfile)
        try:
          for stanza in deb822.Sources.iter_paragraphs(g, shared_storage=False):
            if i18n_error_flag == 1:
              continue
            self.pkg                 = ddtp(stanza['package'], rel, lang)
            self.pkg.description_md5 = stanza['Description-md5']
            try:
              desc               = stanza[descstring]
            except KeyError, err:
              self.log.error("file=%s%s, pkg=%s, description_md5=%s (%s)" % (dir, filename, self.pkg.package, self.pkg.description_md5, err))
              i18n_error_flag=1
              continue
            lines                = desc.splitlines()
            try:
              self.pkg.description = lines[0]
            except IndexError, err:
              self.log.exception("Did not found first line in description: file=%s%s, pkg=%s, description_md5=%s" % (dir, filename, self.pkg.package, self.pkg.description_md5))
              i18n_error_flag=1
              continue
            for line in lines[1:]:
              self.pkg.long_description += line + "\n"

            paramtuple = (self.pkg.package, self.pkg.release, self.pkg.language, self.pkg.description, self.pkg.description_md5)
            cur.execute('EXECUTE ddtp_check_before_insert (%s, %s, %s, %s, %s)', paramtuple)
            if cur.fetchone()[0] > 0:
              self.log.error("Duplicated key for package %s in release %s in language %s: %s / %s" % paramtuple)
            else:
              query = 'EXECUTE ddtp_insert (%s, %s, %s, %s, %s, %s)'
              try:
                self.log.debug(query, tuple([quote(item) for item in paramtuple]))
                cur.execute(query, (self.pkg.package, self.pkg.release, self.pkg.language, self.pkg.description, self.pkg.long_description, self.pkg.description_md5))
                # self.connection.commit() # commit every single insert as long as translation files are featuring duplicated keys
              except IntegrityError, err:
                self.log.exception("Duplicated key in language %s: (%s)", self.pkg.language,
                                 ", ".join([to_unicode(item) for item in (self.pkg.package, self.pkg.release, self.pkg.description, self.pkg.description_md5)]))
                self.connection.rollback()
                continue
              except ProgrammingError, err:
                self.log.exception("Problem inserting translation %s: (%s)", self.pkg.language,
                                 ", ".join([to_unicode(item) for item in (self.pkg.package, self.pkg.release, self.pkg.description, self.pkg.description_md5)]))
                self.connection.rollback()
                continue
        except IOError, err:
          self.log.exception("Error reading %s%s", dir, filename)
        # commit every successfully language to make sure we get any languages in an will not be blocked by a single failing import
        self.connection.commit()

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:

