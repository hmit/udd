#/usr/bin/env python
# Last-Modified: <Sat Jun 28 15:48:36 2008>

import debian_bundle.deb822
import gzip
import os
import sys
import aux
import tempfile
from aux import ConfigException
import psycopg2
from gatherer import gatherer

def quote(s):
  return "'" + s.replace("'", "\\'") + "'"

def null_or_quote(dict, key):
  if key in dict:
    return quote(dict[key])
  else:
    return 'NULL'

class packages_gatherer(gatherer):
  # For efficiency, these are dictionaries
  mandatory = {'Package': 0, 'Version': 0, 'Architecture': 0, 'Maintainer': 0,
      'Description': 0}
  non_mandatory = {'Source': 0, 'Essential': 0, 'Depends': 0, 'Recommends': 0,
      'Suggests': 0, 'Enhances': 0, 'Pre-Depends': 0, 'Installed-Size': 0,
      'Homepage': 0, 'Size': 0, 'MD5Sum': 0}
  ignorable = ()

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
      d[k] = "'" + control[k].replace("\\", "\\\\").replace("'", "\\'") + "'"
    for k in packages_gatherer.non_mandatory:
      d[k] = packages_gatherer.null_or_quote(control, k)
    for k in control.keys():
      if k not in packages_gatherer.mandatory and k not in packages_gatherer.non_mandatory and k not in packages_gatherer.ignorable:
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

      # These are integer values - we don't need quotes for them
      if d['Installed-Size'] != 'NULL':
	d['Installed-Size'] = d['Installed-Size'].strip("'")
      if d['Size'] != 'NULL':
	d['Size'] = d['Size'].strip("'")

      # We just use the first line of the description
      if d['Description'] != "NULL":
	d['Description'] = d['Description'].split("\n",1)[0]
	# If the description was a one-liner only, we don't need to add
	# a quote
	if d['Description'][-1] != "'" or d['Description'][-2] == '\\':
	  d['Description'] += "'"
      
      # Source is non-mandatory, but we don't want it to be NULL
      if d['Source'] == "NULL":
	d['Source'] = d['Package']
	d['Source_Version'] = d['Version']
      else:
	split = d['Source'].strip("'").split()
	if len(split) == 1:
	  d['Source_Version'] = d['Version']
	else:
	  d['Source'] = quote(split[0])
	  d['Source_Version'] = quote(split[1].strip("()"))

      query = """EXECUTE package_insert
	  (%(Package)s, %(Version)s, %(Architecture)s, %(Maintainer)s,
	  %(Description)s, %(Source)s, %(Source_Version)s, %(Essential)s,
	  %(Depends)s, %(Recommends)s, %(Suggests)s, %(Enhances)s,
	  %(Pre-Depends)s, %(Installed-Size)s, %(Homepage)s, %(Size)s,
	  %(MD5Sum)s)""" % d
      try:
	cur.execute(query)
      except psycopg2.ProgrammingError:
	print query
	raise

  def run(self, source):
    if not source in self.config:
      raise ConfigException, "Source %s not specified" %(source)
    src_cfg = self.config[source]

    if not 'directory' in src_cfg:
      raise ConfigException('directory not specified for source %s' %
	  (source))

    if not 'archs' in src_cfg:
      raise ConfigException('archs not specified for source %s' %
	  (source))

    if not 'release' in src_cfg:
      raise ConfigException('release not specified for source %s' %
	  (source))

    if not 'components' in src_cfg:
      raise ConfigException('components not specified for source %s' %
	  (source))

    if not 'distribution' in src_cfg:
      raise ConfigException('distribution not specified for source %s' %
	  (source))

    aux.debug = self.config['general']['debug']

    # Get distribution ID. If it does not exist, create it
    self._distr = src_cfg['distribution']

    cur = self.cursor()
    #cur.execute("PREPARE pkg_insert AS INSERT INTO pkgs (name, distr_id, arch_id, version, src_id) VALUES ($1, $2, $3, $4, $5);")

    # For every part and every architecture, import the packages into the DB
    for comp in src_cfg['components']:
      for arch in src_cfg['archs']:
	path = os.path.join(src_cfg['directory'], comp, 'binary-' + arch, 'Packages.gz')
	try:
	  cur.execute("""PREPARE package_insert AS INSERT INTO Packages
	    (Package, Version, Architecture, Maintainer, Description, Source,
	    Source_Version, Essential, Depends, Recommends, Suggests, Enhances,
	    Pre_Depends, Installed_Size, Homepage, Size, MD5Sum, Distribution,
	    Release, Component)
	  VALUES
	    ( $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
	      $16, $17, '%s', '%s', '%s')
	    """ %  (distr, src_cfg['release'], comp))
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

    self.connection.commit()

  def print_warnings(self):
    for key in packages_gatherer.warned_about:
      print("Unknown key: %s appeared %d times" % (key, packages_gatherer.warned_about[key]))
