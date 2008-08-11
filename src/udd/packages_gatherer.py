# /usr/bin/env python
# Last-Modified: <Sat Aug  9 17:28:45 2008>
# This file is a part of the Ultimate Debian Database project

import debian_bundle.deb822
import gzip
import os
import sys
import aux
import tempfile
from aux import ConfigException
import psycopg2
from gatherer import gatherer

def get_gatherer(connection, config):
  return packages_gatherer(connection, config)

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
      'Suggests': 0, 'Enhances': 0, 'Pre-Depends': 0, 'Installed-Size': 0,
      'Homepage': 0, 'Size': 0, 'Build-Essential':0, 'Origin':0,
      'SHA1':0, 'Replaces':0, 'Section':0, 'MD5sum':0, 'Bugs':0, 'Priority':0,
      'Tag':0, 'Task':0, 'Python-Version':0, 'Provides':0, 'Conflicts':0,
      'SHA256':0, 'Original-Maintainer':0}
  ignorable = {'Filename':0}

  warned_about = {}
  # A mapping from <package-name><version> to 1 If <package-name><version> is
  # included in this dictionary, this means, that we've already added this
  # package with this version for architecture 'all' to the database. Needed
  # because different architectures include packages for architecture 'all'
  # with the same version, and we don't want these duplicate entries
  imported_all_pkgs = {}

  def __init__(self, connection, config):
    gatherer.__init__(self, connection, config)
    # The ID for the distribution we want to include
    self._distr = None

  def build_dict(self, control):
    """Build a dictionary from the control dictionary.

    Influenced by class variables mandatory, non_mandatory and ignorable"""
    d = {}
    for k in packages_gatherer.mandatory:
      if k not in control:
	raise "Mandatory field %s not specified" % k
      d[k] = control[k]
    for k in packages_gatherer.non_mandatory:
      if k not in control:
	d[k] = None
      else:
	d[k] = control[k]
    for k in control.keys():
      if k not in packages_gatherer.non_mandatory and k not in packages_gatherer.mandatory and k not in packages_gatherer.ignorable:
	if k not in packages_gatherer.warned_about:
	  packages_gatherer.warned_about[k] = 1
	else:
	  packages_gatherer.warned_about[k] += 1
    return d

  def import_packages(self, sequence):
    """Import the packages from the sequence into the database-connection
    conn.

    Sequence has to have an iterator interface, that yields a line every time
    it is called.The Format of the sequence is expected to be that of a
    debian packages file."""
    # The fields that are to be read. Other fields are ignored
    cur = self.connection.cursor()
    for control in debian_bundle.deb822.Packages.iter_paragraphs(sequence):
      # Check whether packages with architectue 'all' have already been
      # imported
      if control['Architecture'] == 'all':
	t = control['Package'] + control['Version']
	if t in packages_gatherer.imported_all_pkgs:
	  continue
	packages_gatherer.imported_all_pkgs[t] = 1

      d = self.build_dict(control)

      # We just use the first line of the description
      if 'Description' in d:
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
	  d['Source'] = aux.quote(split[0])
	  d['Source_Version'] = aux.quote(split[1].strip("()"))

      query = """EXECUTE package_insert
	  (%(Package)s, %(Version)s, %(Architecture)s, %(Maintainer)s,
	  %(Description)s, %(Source)s, %(Source_Version)s, %(Essential)s,
	  %(Depends)s, %(Recommends)s, %(Suggests)s, %(Enhances)s,
	  %(Pre-Depends)s, %(Installed-Size)s, %(Homepage)s, %(Size)s,
	  %(Build-Essential)s, %(Origin)s, %(SHA1)s,
	  %(Replaces)s, %(Section)s, %(MD5sum)s, %(Bugs)s, %(Priority)s,
	  %(Tag)s, %(Task)s, %(Python-Version)s, %(Provides)s,
	  %(Conflicts)s, %(SHA256)s, %(Original-Maintainer)s)"""
      try:
	cur.execute(query, d)
      except psycopg2.ProgrammingError:
	print query
	raise

  def run(self, source):
    if not source in self.config:
      raise ConfigException, "Source %s not specified" %(source)
    src_cfg = self.config[source]

    for k in ['directory', 'archs', 'release', 'components', 'distribution', 'packages-table']:
      if not k in src_cfg:
	raise ConfigException(k + ' not sepcified for source ' + source)

    aux.debug = self.config['general']['debug']
    table = src_cfg['packages-table']

    # Get distribution ID
    self._distr = src_cfg['distribution']

    cur = self.cursor()

    # For every part and every architecture, import the packages into the DB
    for comp in src_cfg['components']:
      cur.execute("DELETE FROM %s WHERE distribution = '%s' AND release = '%s' AND component = '%s'" %\
	(table, self._distr, src_cfg['release'], comp))
      for arch in src_cfg['archs']:
	path = os.path.join(src_cfg['directory'], comp, 'binary-' + arch, 'Packages.gz')
	try:
	  cur.execute("""PREPARE package_insert AS INSERT INTO %s
	    (Package, Version, Architecture, Maintainer, Description, Source,
	    Source_Version, Essential, Depends, Recommends, Suggests, Enhances,
	    Pre_Depends, Installed_Size, Homepage, Size,
	    build_essential, origin, sha1, replaces, section,
            md5sum, bugs, priority, tag, task, python_version,
            provides, conflicts, sha256, original_maintainer,
	    Distribution, Release, Component)
	  VALUES
	    ( $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
	      $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28,
	      $29, $30, $31, '%s', '%s', '%s')
	    """ %  (table, self._distr, src_cfg['release'], comp))
	  aux.print_debug("Reading file " + path)
	  # Copy content from gzipped file to temporary file, so that apt_pkg is
	  # used by debian_bundle
	  tmp = tempfile.NamedTemporaryFile()
	  file = gzip.open(path)
	  tmp.write(file.read())
	  file.close()
	  tmp.seek(0)
	  aux.print_debug("Importing from " + path)
	  self.import_packages(open(tmp.name))
	  tmp.close()
	except IOError, (e, message):
	  print "Could not read packages from %s: %s" % (path, message)
	cur.execute("DEALLOCATE package_insert")
	# Fill the summary tables
	cur.execute("TRUNCATE %s" % (table + '_summary'));
	cur.execute("""INSERT INTO %s SELECT DISTINCT ON (package, version,
	  distribution, release, component) package, version, source,
	  source_version, maintainer, distribution, release, component FROM %s""" %
	  (table + '_summary', table));


    self.connection.commit()

    self.print_warnings()

  def print_warnings(self):
    for key in packages_gatherer.warned_about:
      print("Unknown key: %s appeared %d times" % (key, packages_gatherer.warned_about[key]))
