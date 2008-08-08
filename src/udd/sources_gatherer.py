#/usr/bin/env python
# Last-Modified: <Fri Aug  8 12:45:43 2008>
# This file is a part of the Ultimate Debian Database project

import debian_bundle.deb822
import gzip
import os
import sys
import aux
import tempfile
from aux import ConfigException
from aux import null_or_quote
from gatherer import gatherer

def get_gatherer(connection, config):
  return sources_gatherer(connection, config)

class sources_gatherer(gatherer):
  "This class imports the data from Sources.gz files into the database"
  mandatory = {'Format': 0, 'Maintainer': 0, 'Package': 0, 'Version': 0, 'Files': 0}
  non_mandatory = {'Uploaders': 0, 'Binary': 0, 'Architecture': 0,
      'Standards-Version': 0, 'Homepage': 0, 'Build-Depends': 0,
      'Build-Depends-Indep': 0, 'Build-Conflicts': 0, 'Build-Conflicts-Indep': 0,
      'Priority': 0, 'Section': 0, 'Vcs-Arch': 0, 'Vcs-Browser': 0, 'Vcs-Bzr': 0,
      'Vcs-Cvs': 0, 'Vcs-Darcs': 0, 'Vcs-Git': 0, 'Vcs-Hg': 0, 'Vcs-Svn': 0,
      'X-Vcs-Browser': 0, 'X-Vcs-Bzr': 0, 'X-Vcs-Darcs': 0, 'X-Vcs-Svn': 0}
  ignorable = {}

  warned_about = {}

  def __init__(self, connection, config):
    gatherer.__init__(self, connection, config)
    self._distr = None

  def build_dict(self, control):
    """Build a dictionary from the control dictionary.

    Influenced by global variables mandatory, non_mandatory and ignorable"""
    d = {}
    for k in sources_gatherer.mandatory:
      if k not in control:
	raise "Mandatory field %s not specified" % k
      d[k] = "'" + control[k].replace("\\", "\\\\").replace("'", "\\'") + "'"
    for k in sources_gatherer.non_mandatory:
      d[k] = null_or_quote(control, k)
    for k in control.keys():
      if k not in sources_gatherer.mandatory and k not in sources_gatherer.non_mandatory and k not in sources_gatherer.ignorable:
	if k not in sources_gatherer.warned_about:
	  sources_gatherer.warned_about[k] = 1
	else:
	  sources_gatherer.warned_about[k] += 1
    return d

  def import_sources(self, file):
    """Import the sources from the file into the database-connection conn.

    Sequence has to have an iterator interface, that yields a line every time it
    is called.The Format of the file is expected to be that of a debian
    source file."""
    cur = self.cursor()
    for control in debian_bundle.deb822.Packages.iter_paragraphs(file):
      d = self.build_dict(control)
      query = """EXECUTE source_insert
	  (%(Package)s, %(Version)s, %(Maintainer)s, %(Format)s, %(Files)s,
	  %(Uploaders)s, %(Binary)s, %(Architecture)s, %(Standards-Version)s,
	  %(Homepage)s, %(Build-Depends)s, %(Build-Depends-Indep)s,
	  %(Build-Conflicts)s, %(Build-Conflicts-Indep)s, %(Priority)s,
	  %(Section)s, %(Vcs-Arch)s, %(Vcs-Browser)s, %(Vcs-Bzr)s, %(Vcs-Cvs)s,
	  %(Vcs-Darcs)s, %(Vcs-Git)s, %(Vcs-Hg)s, %(Vcs-Svn)s, %(X-Vcs-Browser)s,
	  %(X-Vcs-Bzr)s, %(X-Vcs-Darcs)s, %(X-Vcs-Svn)s)
	  """  % d
      cur.execute(query)

  def run(self, source):
    if not source in self.config:
      raise ConfigException, "Source %s not specified" %(src_name)
    src_cfg = self.config[source]

    if not 'directory' in src_cfg:
      raise ConfigException('directory not specified for source %s' %
	  (src_name))

    if not 'components' in src_cfg:
      raise ConfigException('parts not specified for source %s' %
	  (src_name))

    if not 'distribution' in src_cfg:
      raise ConfigException('distribution not specified for source in file %s' %
	  (src_name))

    if not 'release' in src_cfg:
      raise ConfigException('release not specified for source %s' %
	  (src_name))

    if not 'sources-table' in src_cfg:
      raise ConfigException('sources-table not specifed for source %s' %
	  (src_name))
    
    table = src_cfg['sources-table']
	

    aux.debug = self.config['general']['debug']

    cur = self.cursor()

    for comp in src_cfg['components']:
      path = os.path.join(src_cfg['directory'], comp, 'source', 'Sources.gz')
      cur.execute("DELETE from %s WHERE Distribution = '%s' AND\
	release = '%s' AND component = '%s'"\
	% (table, src_cfg['distribution'], src_cfg['release'], comp))
      try:
	query = """PREPARE source_insert as INSERT INTO %s
	  (Package, Version, Maintainer, Format, Files, Uploaders, Bin,
	  Architecture, Standards_Version, Homepage, Build_Depends,
	  Build_Depends_Indep, Build_Conflicts, Build_Conflicts_Indep, Priority,
	  Section, Vcs_Arch, Vcs_Browser, Vcs_Bzr, Vcs_Cvs, Vcs_Darcs, Vcs_Git,
	  Vcs_Hg, Vcs_Svn, X_Vcs_Browser, X_Vcs_Bzr, X_Vcs_Darcs, X_Vcs_Svn,
	  Distribution, Release, Component)
	VALUES
	  ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
	  $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, '%s', '%s',
	  '%s')"""\
	  % (table, src_cfg['distribution'], src_cfg['release'], comp)
	cur.execute(query)

	aux.print_debug("Reading file " + path)
	# Copy content from gzipped file to temporary file, so that apt_pkg is
	# used by debian_bundle
	tmp = tempfile.NamedTemporaryFile()
	file = gzip.open(path)
	tmp.write(file.read())
	file.close()
	tmp.seek(0)
	aux.print_debug("Importing from " + path)
	self.import_sources(open(tmp.name))
	tmp.close()
      except IOError, (e, message):
	print "Could not read packages from %s: %s" % (path, message)
      cur.execute("DEALLOCATE source_insert")

    self.print_warnings()

  def print_warnings(self):
    for key in sources_gatherer.warned_about:
      print "Unknowen key %s appeared %d times" % (key, sources_gatherer.warned_about[key])
