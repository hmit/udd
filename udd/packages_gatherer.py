# /usr/bin/env python
# Last-Modified: <Sun Aug 17 12:24:40 2008>
# This file is a part of the Ultimate Debian Database project

import debian.deb822
import gzip
import os
import sys
import aux
import tempfile
from aux import ConfigException
import psycopg2
from gatherer import gatherer
from time import time
import email.Utils
import re

def get_gatherer(connection, config, source):
  return packages_gatherer(connection, config, source)

class packages_gatherer(gatherer):
  "This class imports the data from Packages.gz files into the database"
  # For efficiency, these are dictionaries
  # mandatory: list of fields which each package has to provide
  # non_mandatory: list of fields which are possibly provided by packages
  # ignorable: fields which are not useful for the database,
  #            but for which no warning should be printed
  mandatory = {'Package': 0, 'Version': 0, 'Architecture': 0, 'Maintainer': 0,
      'Description': 0}
  non_mandatory = {'Source': 0, 'Essential': 0, 'Depends': 0, 'Recommends': 0,
      'Suggests': 0, 'Enhances': 0, 'Pre-Depends': 0, 'Breaks':0, 'Installed-Size': 0,
      'Homepage': 0, 'Size': 0, 'Build-Essential':0, 'Origin':0,
      'SHA1':0, 'Replaces':0, 'Section':0, 'MD5sum':0, 'Bugs':0, 'Priority':0,
      'Tag':0, 'Task':0, 'Python-Version':0, 'Ruby-Versions':0, 'Provides':0, 'Conflicts':0,
      'SHA256':0, 'Original-Maintainer':0}
  ignorable = {'Modaliases':0, 'Filename':0, 'Npp-Filename':0, 'Npp-Name':0, 'Npp-Mimetype':0, 'Npp-Applications':0, 'Python-Runtime':0, 'Npp-File':0, 'Npp-Description':0, 'Url':0, 'Gstreamer-Elements':0, 'Gstreamer-Version':0, 'Gstreamer-Decoders':0, 'Gstreamer-Uri-Sinks':0, 'Gstreamer-Encoders':0, 'Gstreamer-Uri-Sources':0, 'url':0, 'Vdr-PatchLevel':0, 'Vdr-Patchlevel':0, 'originalmaintainer':0, 'Originalmaintainer':0, 'Build-Recommends':0, 'Multi-Arch':0, 'Maintainer-Homepage':0, 'Tads2-Version':0, 'Tads3-Version':0, 'Xul-Appid': 0, 'Subarchitecture':0, 'Package-Type':0, 'Kernel-Version': 0, 'Installer-Menu-Item':0, 'Supported':0, 'subarchitecture':0, 'package-type':0, 'Python3-Version':0, 'Built-Using':0 }
  ignorable_re = re.compile("^(Orig-|Original-|Origianl-|Orginal-|Orignal-|Orgiinal-|Orginial-|Debian-|X-Original-|Upstream-)")

  pkgquery = """EXECUTE package_insert
      (%(Package)s, %(Version)s, %(Architecture)s, %(Maintainer)s, %(maintainer_name)s, %(maintainer_email)s,
      %(Description)s, %(Long_Description)s, %(Source)s, %(Source_Version)s, %(Essential)s,
      %(Depends)s, %(Recommends)s, %(Suggests)s, %(Enhances)s,
      %(Pre-Depends)s, %(Breaks)s, %(Installed-Size)s, %(Homepage)s, %(Size)s,
      %(Build-Essential)s, %(Origin)s, %(SHA1)s,
      %(Replaces)s, %(Section)s, %(MD5sum)s, %(Bugs)s, %(Priority)s,
      %(Tag)s, %(Task)s, %(Python-Version)s, %(Ruby-Versions)s, %(Provides)s,
      %(Conflicts)s, %(SHA256)s, %(Original-Maintainer)s)"""

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    # The ID for the distribution we want to include
    self._distr = None
    self.assert_my_config('directory', 'archs', 'release', 'components', 'distribution', 'packages-table', 'packages-schema')
    self.warned_about = {}
    # A mapping from <package-name><version> to 1 If <package-name><version> is
    # included in this dictionary, this means, that we've already added this
    # package with this version for architecture 'all' to the database. Needed
    # because different architectures include packages for architecture 'all'
    # with the same version, and we don't want these duplicate entries
    self.imported_all_pkgs = {}

  def build_dict(self, control):
    """Build a dictionary from the control dictionary.

    Influenced by class variables mandatory, non_mandatory and ignorable"""
    d = {}
    for k in packages_gatherer.mandatory:
      if k not in control:
	raise "Mandatory field %s not specified" % k
      d[k] = control[k]
    for k in packages_gatherer.non_mandatory:
      if k in control:
	d[k] = control[k]
      else:
	d[k] = None
    for k in control.iterkeys():
      if k not in packages_gatherer.non_mandatory and k not in packages_gatherer.mandatory and k not in packages_gatherer.ignorable and not (packages_gatherer.ignorable_re.match(k)):
        if k not in self.warned_about:
          self.warned_about[k] = 1
	else:
	  self.warned_about[k] += 1
    return d

  def import_packages(self, sequence, cur):
    """Import the packages from the sequence into the database-connection
    conn.

    Sequence has to have an iterator interface, that yields a line every time
    it is called.The Format of the sequence is expected to be that of a
    debian packages file."""
    pkgs = []

    # The fields that are to be read. Other fields are ignored
    for control in debian.deb822.Packages.iter_paragraphs(sequence):
      # Check whether packages with architectue 'all' have already been
      # imported
      t = control['Package'] + '_' + control['Version'] + '_' + control['Architecture']
      if t in self.imported_all_pkgs:
        continue
      self.imported_all_pkgs[t] = 1

      d = self.build_dict(control)

      # We split the description
      if 'Description' in d:
	if len(d['Description'].split("\n",1)) > 1:
	  d['Long_Description'] = d['Description'].split("\n",1)[1]
	else:
	  d['Long_Description'] = ''
	d['Description'] = d['Description'].split("\n",1)[0]

      # Convert numbers to numbers
      for f in ['Installed-Size', 'Size']:
	if d[f] is not None:
	  d[f] = int(d[f])
      
      # Source is non-mandatory, but we don't want it to be NULL
      if d['Source'] is None:
	d['Source'] = d['Package']
	d['Source_Version'] = d['Version']
      else:
	split = d['Source'].strip("'").split()
	if len(split) == 1:
	  d['Source_Version'] = d['Version']
	else:
	  d['Source'] = split[0]
	  d['Source_Version'] = split[1].strip("()")

      d['maintainer_name'], d['maintainer_email'] = email.Utils.parseaddr(d['Maintainer'])
      pkgs.append(d)
    try:
      cur.executemany(self.pkgquery, pkgs)
    except psycopg2.ProgrammingError:
      print "Error while inserting packages"
      raise

  def setup(self):
    if 'schema-dir' in self.config['general']:
      schema_dir = self.config['general']['schema-dir']
      if 'packages-schema' in self.my_config:
	schema = schema_dir + '/' + self.my_config['packages-schema']
	self.eval_sql_file(schema, self.my_config)
      else:
	raise Exception("'packages-schema' not specified for source " + self.source)
    else:
      raise Exception("'schema-dir' not specified")

  def tables(self):
    return [
      self.my_config['packages-table'],
      self.my_config['packages-table'] + '_summary']

  def run(self):
    src_cfg = self.my_config

    aux.debug = self.config['general']['debug']
    table = src_cfg['packages-table']

    # Get distribution ID
    self._distr = src_cfg['distribution']

    cur = self.cursor()
    # defer constraints checking until the end of the transaction
    cur.execute("SET CONSTRAINTS ALL DEFERRED")

    # For every part and every architecture, import the packages into the DB
    for comp in src_cfg['components']:
      cur.execute("DELETE FROM %s WHERE distribution = '%s' AND release = '%s' AND component = '%s'" %\
	(table, self._distr, src_cfg['release'], comp))
      for arch in src_cfg['archs']:
	path = os.path.join(src_cfg['directory'], comp, 'binary-' + arch, 'Packages.gz')
	try:
	  cur.execute("""PREPARE package_insert AS INSERT INTO %s
	    (Package, Version, Architecture, Maintainer, maintainer_name, maintainer_email, Description, Long_Description, Source,
	    Source_Version, Essential, Depends, Recommends, Suggests, Enhances,
	    Pre_Depends, Breaks, Installed_Size, Homepage, Size,
	    build_essential, origin, sha1, replaces, section,
            md5sum, bugs, priority, tag, task, python_version, ruby_versions,
            provides, conflicts, sha256, original_maintainer,
	    Distribution, Release, Component)
	  VALUES
	    ( $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
	      $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28,
	      $29, $30, $31, $32, $33, $34, $35, $36, '%s', '%s', '%s')
	    """ %  (table, self._distr, src_cfg['release'], comp))
#	  aux.print_debug("Reading file " + path)
	  # Copy content from gzipped file to temporary file, so that apt_pkg is
	  # used by debian
	  tmp = tempfile.NamedTemporaryFile()
	  file = gzip.open(path)
	  tmp.write(file.read())
	  file.close()
	  tmp.seek(0)
#	  aux.print_debug("Importing from " + path)
	  self.import_packages(open(tmp.name), cur)
	  tmp.close()
	except IOError, (e, message):
	  print "Could not read packages from %s: %s" % (path, message)
          sys.exit(1)
	cur.execute("DEALLOCATE package_insert")
    # Fill the summary tables
    cur.execute("DELETE FROM %s" % (table + '_summary'));
    cur.execute("""INSERT INTO %s (package, version, source, source_version,
        maintainer, maintainer_name, maintainer_email, distribution, release, component)
      SELECT DISTINCT ON (package, version, distribution, release, component)
        package, version, source, source_version, maintainer, maintainer_name, maintainer_email, distribution, release, component
      FROM %s""" % (table + '_summary', table));
    cur.execute("DELETE FROM %s" % (table + '_distrelcomparch'));
    cur.execute("""INSERT INTO %s
      (distribution, release, component, architecture)
      SELECT DISTINCT distribution, release, component, architecture
      FROM %s""" % (table + '_distrelcomparch', table))

    cur.execute("ANALYZE %s" % table)
    cur.execute("ANALYZE %s" % table + '_summary')
    cur.execute("ANALYZE %s" % table + '_distrelcomparch')

    self.print_warnings()

  def print_warnings(self):
    for key in self.warned_about:
      print("[Packages] Unknown key %s appeared %d times" % (key, self.warned_about[key]))
