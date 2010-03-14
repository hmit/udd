#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script imports informations about translated applications
inside Debian packages.
"""

from aux import quote
from gatherer import gatherer
import re
from debian_bundle import deb822
from os import stat
from sys import stderr, exit
from filecmp import cmp
import gzip
# import bz2
from psycopg2 import IntegrityError, InternalError

debug=0

check_char_re               = re.compile('&#[0-9][0-9][0-9];')
parse_translation_status_re = re.compile('^(\d+)t(\d+)f(\d+)u$')

def replace_special_char(string):
  if not check_char_re.search(string):
    return string
  parts = string.split('&#')
  newstring = ''
  for p in parts:
    q = p.split(';')
    if len(q) > 1:
      newstring += unichr(int(q[0])) + q[1]
    else:
      newstring += q[0]
  return newstring.encode('utf-8')

def get_gatherer(connection, config, source):
  return i18n_apps_gatherer(connection, config, source)

class pkg_info():
  def __init__(self, package, release):
    self.package          = package
    self.release          = release
    self.version          = ''
    self.maintainer       = ''

  def __str__(self):
    return "Package %s: %s, %s\n%s" % \
        (self.package, self.maintainer, self.version)

class po_info():
  def __init__(self, poline):
    po = poline.strip().split('!')
    # ignore .pot and .templates files
    if not po[0].endswith('.po'):
      # or po[1].startswith('_') :
      self.infofields = 0
      return
    # Keep track of the number of information fields given for a po files
    # In case there are more than one po file in a package just take the
    # one containing more information
    self.infofields       = len(po)
    self.po_file          = po[0]
    self.language         = po[1]
    if len(self.language) < 2:
      print >>stderr, "Invalid language '%s'. Po filename is %s." % (self.language, self.po_file)
      self.infofields = 0
      return
    match = parse_translation_status_re.match(po[2])
    if not match:
      self.translated   = 'NULL'
      self.fuzzy        = 'NULL'
      self.untranslated = 'NULL'
    else:
      self.translated   = match.groups()[0]
      self.fuzzy        = match.groups()[1]
      self.untranslated = match.groups()[2]
    self.pkg_version_lang = po[3]       # Meaning is unclear

    # sometimes language translation team is missing
    if self.infofields < 6:
      self.language_team = 'NULL'
    else:
      self.language_team = replace_special_char(po[5])
    if self.infofields == 4:
      self.last_translator = 'NULL'
    else:
      self.last_translator = replace_special_char(po[4])

  def __str__(self):
    return "Package %s: %s, %s\n%s" % \
        (self.infofields, self.language, self.po_file, self.last_translator)

  def __cmp__(self, other):
    return self.infofields - other.infofields

class i18n_apps_gatherer(gatherer):

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('path', 'files', 'table_apps', 'table_debconf')
    my_config = self.my_config

    cur = self.cursor()
    # create prepared statements here!
    query = """PREPARE %s_insert
                   (text, text, text, text, text, text, text, text, text, int, int, int)
                AS INSERT INTO %s
                   (package, version, release, maintainer, po_file, language,
                    pkg_version_lang, last_translator, language_team,
                    translated, fuzzy, untranslated)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)"""
    cur.execute(query % (my_config['table_apps'], my_config['table_apps']))
    cur.execute(query % (my_config['table_debconf'], my_config['table_debconf']))

    pkg = None

  def parse_po_infoline(self, po_type, data):
    cur = self.cursor()

    if po_type == 'PO':
      target_table = self.my_config['table_apps']
    elif po_type == 'PODEBCONF':
      target_table = self.my_config['table_debconf']
    else:
      print >>stderr, "Wrong PO type %s ignored." % po_type
      return

    po_info_dict = {}
    for poline in data[po_type].split("\n"):
      # ignore first empty line
      if len(poline) <= 1:
        continue
      poinfo = po_info(poline)
      if poinfo.infofields == 0:
        continue
      # Sometimes there is more than one po file in a package.  We inject the file
      # which contains better info about translator
      # Attention: For the current application it is completely sufficient that we
      #            keep the information *that* a package contains translation for
      #            a certain package in UDD.  Other applications might need more
      #            complete information.
      if po_info_dict.has_key(poinfo.language):
        po_info_dict[poinfo.language] = max(po_info_dict[poinfo.language], poinfo)
      else:
        po_info_dict[poinfo.language] = poinfo

    for lang in po_info_dict.keys():
      poinfo = po_info_dict[lang]
      query = "EXECUTE %s_insert (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" % \
                (target_table, \
                 quote(self.pkg.package), quote(self.pkg.version), quote(self.pkg.release), \
                 quote(self.pkg.maintainer), quote(poinfo.po_file), quote(poinfo.language), \
                 quote(poinfo.pkg_version_lang), \
                 quote(poinfo.last_translator), quote(poinfo.language_team), \
                 poinfo.translated, poinfo.fuzzy, poinfo.untranslated)
      try:
        cur.execute(query)
      except IntegrityError, err:
        print str(err).strip()
        print len(po), po, poline, self.pkg
      except InternalError, err:
        print "InternalError:", err
        print len(po), po, poline, self.pkg, po_type
        print query
        exit(-1)
      except UnicodeEncodeError, err:
        print err
        print query

  def run(self):
    my_config = self.my_config
    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()

    releases=my_config['releases'].split(' ')

    # verify whether input files are properly downloaded
    for rel in releases:
      file = my_config['path']+'/'+rel+'.gz'
      statinfo = stat(file)
      if not statinfo or statinfo[6] < 1:
        print >>stderr, "File %s for release %s does not exist or is empty" % (file, rel)
        exit
      # print "File %s has %i bytes" % ( file, statinfo[6] )
    # Clean up tables
    query = "TRUNCATE %s; TRUNCATE %s;" % ( my_config['table_apps'], my_config['table_debconf'])
    cur.execute(query)

    for rel in releases:
      file = my_config['path']+'/'+rel+'.gz'
      g = gzip.GzipFile(file)
      try:
        for stanza in deb822.Sources.iter_paragraphs(g, shared_storage=False):
          self.pkg             = pkg_info(stanza['Package'], rel)
          # First entry is no real package but a date entry
          if not stanza.has_key('Version'):
            continue
          # Package without language information are irrelevant
          if not stanza.has_key('PO') or not stanza.has_key('PODEBCONF'):
            continue
          self.pkg.version     = stanza['Version']
          self.pkg.maintainer  = stanza['Maintainer']

          if stanza.has_key('PO'):
            self.parse_po_infoline('PO', stanza)
          if stanza.has_key('PODEBCONF'):
            self.parse_po_infoline('PODEBCONF', stanza)

      except IOError, err:
        print >>stderr, "Error reading %s (%s)" % (file, err)

    cur.execute("ANALYZE %s" % my_config['table_apps'])
    cur.execute("ANALYZE %s" % my_config['table_debconf'])

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:

