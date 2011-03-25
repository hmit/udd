#!/usr/bin/env python

"""
This script imports translations from the Debian Description
translation project into the database.  It parses the translation
files at
     http://ddtp.debian.net/Translation_udd
which are enriched by the version numbers of the packages that
are described which makes it qut simple to assotiate a primary
key to the translation even if it might be redundant information
because you have the MD5sum of the descriptions
"""

from aux import quote
from gatherer import gatherer
import re
try:
    from debian import deb822
except:
    from debian_bundle import deb822
from os import listdir, access, F_OK
from sys import stderr, exit
from filecmp import cmp
import gzip
# import bz2
from psycopg2 import IntegrityError, InternalError

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
    self.distribution     = 'debian' # No DDTP translations for debian-backports / debian-volatile
    self.release          = release
    self.component        = 'main'   # Only main translated for the moment
    self.language         = language
    self.description      = ''
    self.long_description = ''
    self.md5sum           = ''
    self.version          = ''

  def __str__(self):
    return "Package %s: %s, %s\n%s" % \
        (self.package, self.language, self.description, self.long_description)

class ddtp_gatherer(gatherer):
  # DDTP translations

  select_language_re    = re.compile('^Translation-(\w+)\.gz$')

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('path', 'files', 'table', 'releases')
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
    # self.log.debug("execute query %s", query)
    cur.execute(query)
    query = """PREPARE ddtp_insert AS INSERT INTO %s
                   (package, distribution, component, release, language, version, description, long_description, md5sum)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""" % (my_config['table'])
    # self.log.debug("execute query %s", query)
    cur.execute(query)

    query = """PREPARE ddtp_check_before_insert (text, text, text, text, text, text) AS
                  SELECT COUNT(*) FROM %s
                    WHERE package = $1 AND distribution = $2 AND component = $3 AND
                          release = $4 AND language = $5 AND version = $6""" % (my_config['table'])
    # self.log.debug("execute query %s", query)
    cur.execute(query)

    query = """PREPARE ddtp_get_duplicate (text, text, text, text, text, text) AS
                  SELECT description, long_description, md5sum FROM %s
                    WHERE package = $1 AND distribution = $2 AND component = $3 AND
                          release = $4 AND language = $5 AND version = $6""" % (my_config['table'])
    # self.log.debug("execute query %s", query)
    cur.execute(query)

    # Query for english package description of the i386 architecture because this is the
    # most popular arch.  In case a package description might differ in very seldom cases
    # we put the translation of the i386 architecture into UDD
    query = """PREPARE ddtp_packages_recieve_description_md5 (text, text, text, text, text) AS 
               SELECT md5(full_description || E'\n' ) AS md5,
               full_description FROM (
                 SELECT DISTINCT
                   description || E'\n' || long_description AS full_description
                  FROM packages
                  WHERE package = $1 AND distribution = $2 AND component = $3 AND
                  release = $4 AND version = $5 AND architecture in ('all', 'i386', 'amd64')
               ) AS tmp GROUP BY full_description LIMIT 1"""
    # self.log.debug("execute query %s", query)
    cur.execute(query)

    # In some cases a just imported translation has to be removed again because
    # of a further translation which matches MD5 sum of i386 architecture
    query = """PREPARE ddtp_delete_duplicate(text, text, text, text, text, text) AS 
               DELETE FROM %s
                    WHERE package = $1 AND distribution = $2 AND component = $3 AND
                          release = $4 AND language = $5 AND version = $6""" % (my_config['table'])
    # self.log.debug("execute query %s", query)
    cur.execute(query)

    pkg = None

  def run(self):
    my_config = self.my_config
    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()

    releases=my_config['releases'].split(' ')
    for rel in releases:
      dir = my_config['path']+'/'+rel+'/'
      if not access(dir, F_OK):
	self.log.error("Directory %s for release %s does not exist", dir, rel)
        continue
      for filename in listdir(dir):
        match = ddtp_gatherer.select_language_re.match(filename)
        if not match:
          continue
        lang = match.groups()[0]
        md5file=dir + 'Translation-' + lang + '.md5'
        try:
          if ( cmp(md5file, md5file + '.prev' ) ):
            # self.log.debug("%s has not changed.  No update needed.", md5file)
            continue
          else:
            # self.log.debug("%s changed.  Go on updating language %s", md5file, lang)
            pass
        except OSError:
          self.log.info('md5file for %s missing,  Go updating', lang)

        # Delete only records where we actually have Translation files.  This
        # prevents dump deletion of all data in case of broken downloads
        query = "EXECUTE ddtp_delete (%s, %s)" % (quote(rel), quote(lang))
        # self.log.debug("execute query %s", query)
        cur.execute(query)

        i18n_error_flag=0
        descstring = 'Description-'+lang
        g = gzip.GzipFile(dir + filename)
        try:
          for stanza in deb822.Sources.iter_paragraphs(g, shared_storage=False):
            if i18n_error_flag == 1:
              continue
            self.pkg             = ddtp(stanza['package'], rel, lang)
            self.pkg.md5sum      = stanza['Description-md5']
            self.pkg.version     = stanza['Version']
            try:
              desc               = stanza[descstring]
            except KeyError, err:
              self.log.error("file=%s%s, pkg=%s, version=%s (%s)" % (dir, filename, self.pkg.package, self.pkg.version, err))
              i18n_error_flag=1
              continue
            lines                = desc.splitlines()
            try:
              self.pkg.description = lines[0]
            except IndexError, err:
              self.log.exception("Did not found first line in description: file=%s%s, pkg=%s, version=%s" % (dir, filename, self.pkg.package, self.pkg.version))
              i18n_error_flag=1
              continue
            for line in lines[1:]:
              self.pkg.long_description += line + "\n"
            query = "EXECUTE ddtp_check_before_insert (%s, %s, %s, %s, %s, %s)" % \
                    tuple([quote(item) for item in (self.pkg.package, self.pkg.distribution, self.pkg.component, 
                     self.pkg.release, self.pkg.language, self.pkg.version)])
            # self.log.debug("execute query %s", query)
            try:
              cur.execute(query)
            except InternalError, err:
              self.log.exception("Encoding problem reading %s%s", dir, filename)
              i18n_error_flag=1
              continue
            if cur.fetchone()[0] > 0:
              self.log.debug("Just imported key in language %s: (%s)", self.pkg.language,
                             ", ".join([self.pkg.package, self.pkg.distribution, self.pkg.component, self.pkg.release,
                                      self.pkg.version, self.pkg.description, self.pkg.md5sum]))
              query = " EXECUTE ddtp_packages_recieve_description_md5 (%s, %s, %s, %s, %s)" % \
                    tuple([quote(item) for item in (self.pkg.package, self.pkg.distribution, self.pkg.component, \
                     self.pkg.release, self.pkg.version)])
              self.log.debug("execute query %s", query)
              cur.execute(query)
              if cur.rowcount <= 0:
                self.log.warning("Did not find description for most frequent architectures in %s",
                                 ", ".join([self.pkg.package, self.pkg.distribution, self.pkg.component,
                                            self.pkg.release, self.pkg.version]))
                continue

              md5sum = cur.fetchone()[0]
              if  md5sum.startswith(self.pkg.md5sum):
                self.log.debug("Correct translation is just in the Database.")
                continue

              query = "EXECUTE ddtp_get_duplicate (%s, %s, %s, %s, %s, %s)" % \
                    tuple([quote(item) for item in (self.pkg.package, self.pkg.distribution, self.pkg.component, \
                     self.pkg.release, self.pkg.language, self.pkg.version)])
              # self.log.debug("execute query %s", query)
              cur.execute(query)
              for r in cur.fetchall():
                if md5sum.startswith(r[2]):
                  query = "EXECUTE ddtp_delete_duplicate (%s, %s, %s, %s, %s, %s)" % \
                      tuple([quote(item) for item in (self.pkg.package, self.pkg.distribution, self.pkg.component, \
                       self.pkg.release, self.pkg.language, self.pkg.version)])
                  # self.log.debug("execute query %s", query)
                  cur.execute(query)

            query = "EXECUTE ddtp_insert (%s, %s, %s, %s, %s, %s, %s, %s, %s)" % \
                        tuple([quote(item) for item in (self.pkg.package, self.pkg.distribution, \
                         self.pkg.component, self.pkg.release, \
                         self.pkg.language, self.pkg.version, \
                         self.pkg.description, \
                         self.pkg.long_description, \
                         self.pkg.md5sum)])
            try:
              # self.log.debug("execute query %s", query)
              cur.execute(query)
            except IntegrityError, err:
              self.log.exception("Duplicated key in language %s: (%s)", self.pkg.language,
                                 ", ".join([to_unicode(item) for item in (self.pkg.package, self.pkg.version, self.pkg.description, self.pkg.md5sum)]))
              self.connection.rollback()
              continue
        except IOError, err:
          self.log.exception("Error reading %s%s", dir, filename)
        # commit every successfully language to make sure we get any languages in an willnot be blocked by a single failing import
        self.connection.commit()

    cur.execute("DEALLOCATE ddtp_insert")
    cur.execute("ANALYZE %s" % my_config['table'])

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:

