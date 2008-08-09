#/usr/bin/env python
# Last-Modified: <Sat Aug  9 17:28:33 2008>
# This file is a part of the Ultimate Debian Database project

import debian_bundle.deb822
import gzip
import os
import sys
import aux
import tempfile
from aux import ConfigException
from aux import null_or_quote, quote
from gatherer import gatherer

def get_gatherer(connection, config):
  return sources_gatherer(connection, config)

class sources_gatherer(gatherer):
  "This class imports the data from Sources.gz files into the database"
  mandatory = {'Format': 0, 'Maintainer': 0, 'Package': 0, 'Version': 0, 'Files': 0}
  non_mandatory = {'Uploaders': 0, 'Binary': 0, 'Architecture': 0,
      'Standards-Version': 0, 'Homepage': 0, 'Build-Depends': 0,
      'Build-Depends-Indep': 0, 'Build-Conflicts': 0, 'Build-Conflicts-Indep': 0,
      'Priority': 0, 'Section': 0, 'Python-Version': 0, 'Checksums-Sha1':0,
      'Checksums-Sha256':0, 'Original-Maintainer':0, 'Dm-Upload-Allowed':0} 
  ignorable = {'Vcs-Arch': 0, 'Vcs-Bzr': 0,
      'Vcs-Cvs': 0, 'Vcs-Darcs': 0, 'Vcs-Git': 0, 'Vcs-Hg': 0, 'Vcs-Svn': 0,
      'X-Vcs-Browser': 0, 'Vcs-Browser': 0, 'X-Vcs-Bzr': 0, 'X-Vcs-Darcs': 0, 'X-Vcs-Svn': 0,
      'Directory':0}
  vcs = { 'Arch':0, 'Bzr':0, 'Cvs':0, 'Darcs':0, 'Git':0, 'Hg':0, 'Svn':0}

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
      d[k] = control[k]
    for k in sources_gatherer.non_mandatory:
      if k in control:
	d[k] = control[k]
      else:
	d[k] = None
    
    d['Vcs-Type'] = None
    d['Vcs-Url'] = None
    for vcs in sources_gatherer.vcs:
      if control.has_key("Vcs-"+vcs):  
        d['Vcs-Type'] = vcs
	d['Vcs-Url'] = control["Vcs-"+vcs]
	break
      elif control.has_key("X-Vcs-"+vcs):  
        d['Vcs-Type'] = vcs
	d['Vcs-Url'] = control["X-Vcs-"+vcs]
	break
    if control.has_key("Vcs-Browser"):  
        d['Vcs-Browser'] = control["Vcs-Browser"]
    elif control.has_key("X-Vcs-Browser"):  
        d['Vcs-Browser'] = control["X-Vcs-Browser"]
    else:
        d['Vcs-Browser'] = None
    
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
	  %(Section)s, %(Vcs-Type)s, %(Vcs-Url)s, %(Vcs-Browser)s,
	  %(Python-Version)s, %(Checksums-Sha1)s, %(Checksums-Sha256)s,
	  %(Original-Maintainer)s, %(Dm-Upload-Allowed)s)
	  """ 
      cur.execute(query, d)

  def run(self, source):
    if not source in self.config:
      raise ConfigException, "Source %s not specified" %(src_name)
    src_cfg = self.config[source]

    for k in ['directory', 'components', 'distribution', 'release', 'sources-table']:
      if not k in src_cfg:
	raise ConfigException(k + ' not specified for source ' + source)
    
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
	  Section, Vcs_Type, Vcs_Url, Vcs_Browser, python_version, checksums_sha1,
	  checksums_sha256, original_maintainer, dm_upload_allowed,
	  Distribution, Release, Component)
	VALUES
	  ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
	  $17, $18, $19, $20, $21, $22, $23, $24, '%s', '%s', '%s')"""\
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
      print "Unknown key %s appeared %d times" % (key, sources_gatherer.warned_about[key])
