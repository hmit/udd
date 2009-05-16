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
from debian_bundle import deb822
from os import listdir, access, F_OK
from sys import stderr, exit
import gzip
# import bz2
from psycopg2 import IntegrityError, InternalError

online=0

def get_gatherer(connection, config, source):
  return ddtp_gatherer(connection, config, source)

class ddtp():
  def __init__(self, package, release, language):
    self.package          = package
    self.distribution     = 'debian' # No DDTP translations for debian-backports / debian-volatile
    self.release          = release  # sid for the moment
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

    cur = self.cursor()
    query = "DELETE FROM %s" % my_config['table']
    cur.execute(query)
    query = """PREPARE ddtp_insert AS INSERT INTO %s
                   (package, distribution, component, release, language, version, description, long_description, md5sum)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""" % (my_config['table'])
    cur.execute(query)

    query = """PREPARE ddtp_check_before_insert (text, text, text, text, text, text) AS
                  SELECT COUNT(*) FROM %s
                    WHERE package = $1 AND distribution = $2 AND component = $3 AND
                          release = $4 AND language = $5 AND version = $6""" % (my_config['table'])
    cur.execute(query)


    # Query for english package description, its md5 sum and package version
# Not used any more because the Translation files now contain version numbers
# but keep the query as comment to store the knowledge how to calculate MD5 sums
# for the descriptions for possible later use
#    query = """PREPARE ddtp_packages_recieve_description_md5 AS 
#               SELECT md5(full_description || E'\n' ) AS md5,
#               full_description, MAX(version) AS version FROM (
#                 SELECT DISTINCT
#                   description || E'\n' || long_description AS full_description,
#                   version
#                  FROM packages
#                  WHERE package = $1 AND distribution = $2 AND component = $3 AND
#                  release = $4
#               ) AS tmp GROUP BY full_description"""
#    cur.execute(query)

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
        print >>stderr, "Directory %s for release %s does not exist" % (dir, rel)
        continue
      for filename in listdir(dir):
        match = ddtp_gatherer.select_language_re.match(filename)
        if not match:
          continue
        lang = match.groups()[0]
        descstring = 'Description-'+lang
        g = gzip.GzipFile(dir + filename)
        try:
          for stanza in deb822.Sources.iter_paragraphs(g, shared_storage=False):
            self.pkg             = ddtp(stanza['package'], rel, lang)
            self.pkg.md5sum      = stanza['Description-md5']
            self.pkg.version     = stanza['Version']
            desc                 = stanza[descstring]
            lines                = desc.splitlines()
            self.pkg.description = lines[0]
            for line in lines[1:]:
              self.pkg.long_description += line + "\n"
            query = "EXECUTE ddtp_check_before_insert ('%s', '%s', '%s', '%s', '%s', '%s')" % \
                    (self.pkg.package, self.pkg.distribution, self.pkg.component, \
                     self.pkg.release, self.pkg.language, self.pkg.version)
            cur.execute(query)
            if cur.fetchone()[0] > 0:
              print >>stderr, "Duplicated key in language %s: " % self.pkg.language, \
                  self.pkg.package, self.pkg.distribution, self.pkg.component, self.pkg.release, \
                  self.pkg.version, self.pkg.description, self.pkg.md5sum
              continue
            query = "EXECUTE ddtp_insert (%s, '%s', '%s', '%s', '%s', '%s', %s, %s, %s)" % \
                        (quote(self.pkg.package), self.pkg.distribution, self.pkg.component, self.pkg.release, \
                         self.pkg.language, self.pkg.version, quote(self.pkg.description), \
                         quote(self.pkg.long_description), \
                         quote(self.pkg.md5sum))
            try:
              cur.execute(query)
            except IntegrityError, err:
              print "Duplicated key in language %s: " % self.pkg.language, \
                    (self.pkg.package, self.pkg.version, self.pkg.description, self.pkg.md5sum)
        except IOError, err:
          print >>stderr, "Error reading %s (%s)" % (dir+filename, err)

    cur.execute("DEALLOCATE ddtp_insert")

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:

